"""
Users API router.

This module contains endpoints related to the current user:
- /me (rate-limited) returns current authenticated user
- /avatar upload (Cloudinary) for any authenticated user
- /avatar/default (admin-only) sets DEFAULT_AVATAR_URL

Security notes:
- All protected endpoints require a valid JWT access token.
- Admin-only endpoint enforces role-based access control.
- Cache invalidation is performed to keep Redis cache consistent.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Request
from sqlalchemy.orm import Session
from slowapi.util import get_remote_address

from app.database import get_db
from app.schemas import UserResponse
from app.auth.deps import get_current_user, require_admin
from app.models import User
from app.config import ME_RATE_LIMIT, DEFAULT_AVATAR_URL
from app.limiter import limiter
from app.services.cloudinary import upload_avatar
from app.services.redis_cache import invalidate_user_cache

router = APIRouter(prefix="/users", tags=["Users"])

RATE_LIMIT_VALUE = ME_RATE_LIMIT or "5/minute"

MAX_AVATAR_SIZE = 2_000_000
ALLOWED_TYPES = ("image/jpeg", "image/png", "image/webp")


def _get_upload_size(upload: UploadFile) -> int:
    """
    Determine the size of an uploaded file (best-effort).

    The underlying file object is usually a SpooledTemporaryFile.
    We seek to the end to get its size and then return to start.

    Args:
        upload: FastAPI UploadFile.

    Returns:
        File size in bytes, or -1 if size cannot be determined.
    """
    try:
        upload.file.seek(0, 2)
        size = upload.file.tell()
        upload.file.seek(0)
        return int(size)
    except Exception:
        return -1


@router.get("/me", response_model=UserResponse)
@limiter.limit(RATE_LIMIT_VALUE, key_func=get_remote_address)
def me(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Return the current authenticated user.

    This endpoint is rate-limited (ME_RATE_LIMIT from .env).
    Authentication uses JWT access token.

    Args:
        request: Starlette request (required by slowapi).
        db: SQLAlchemy DB session.
        current_user: User resolved from JWT (may come from Redis cache).

    Returns:
        UserResponse (id, email, is_verified, avatar_url).
    """
    return current_user


@router.patch("/avatar", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload and set a new avatar for the current user (Cloudinary).

    Validation:
    - content-type must be JPEG/PNG/WEBP
    - file size must be <= 2MB (best-effort check)

    After a successful update, invalidates Redis cache for this user.

    Args:
        file: Uploaded image file.
        db: SQLAlchemy DB session.
        current_user: Current authenticated user (from JWT/cache).

    Returns:
        Updated user object.

    Raises:
        HTTPException: 400 for invalid file type/size.
        HTTPException: 502 for Cloudinary upload errors.
        HTTPException: 401 if user not found.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WEBP images are allowed")

    size = _get_upload_size(file)
    if size != -1 and size > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 2MB.")

    try:
        url = upload_avatar(file.file, public_id=f"user_{current_user.id}")
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Cloudinary upload failed")

    # Persist in DB (current_user may be detached from cache)
    user_db = db.query(User).filter(User.id == current_user.id).first()
    if not user_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    user_db.avatar_url = url
    db.commit()
    db.refresh(user_db)

    invalidate_user_cache(user_db.email)
    return user_db


@router.patch("/avatar/default", response_model=UserResponse, status_code=status.HTTP_200_OK)
def set_default_avatar(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Admin-only: set avatar_url to DEFAULT_AVATAR_URL for current admin user.

    This implements role-based access requirement:
    only administrators may set their avatar to the default value.

    After update, invalidates Redis cache for this user.

    Args:
        db: SQLAlchemy DB session.
        admin_user: Current authenticated admin user.

    Returns:
        Updated user object (with default avatar url).

    Raises:
        HTTPException: 500 if DEFAULT_AVATAR_URL not configured.
        HTTPException: 401 if user not found.
        HTTPException: 403 if not admin (handled by require_admin).
    """
    if not DEFAULT_AVATAR_URL:
        raise HTTPException(status_code=500, detail="DEFAULT_AVATAR_URL is not configured in .env")

    user_db = db.query(User).filter(User.id == admin_user.id).first()
    if not user_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    user_db.avatar_url = DEFAULT_AVATAR_URL
    db.commit()
    db.refresh(user_db)

    invalidate_user_cache(user_db.email)
    return user_db