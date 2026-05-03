from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Request
from sqlalchemy.orm import Session
from slowapi.util import get_remote_address

from app.database import get_db
from app.schemas import UserResponse
from app.auth.deps import get_current_user
from app.models import User
from app.config import ME_RATE_LIMIT
from app.limiter import limiter
from app.services.cloudinary import upload_avatar

router = APIRouter(prefix="/users", tags=["Users"])

# robust fallback if env missing/empty
RATE_LIMIT_VALUE = ME_RATE_LIMIT or "5/minute"

# max avatar size in bytes (2MB)
MAX_AVATAR_SIZE = 2_000_000
ALLOWED_TYPES = ("image/jpeg", "image/png", "image/webp")


def _get_upload_size(upload: UploadFile) -> int:
    """
    Determine file size without reading full content into memory.
    Works for SpooledTemporaryFile used by Starlette/FastAPI.
    """
    try:
        upload.file.seek(0, 2)  # to end
        size = upload.file.tell()
        upload.file.seek(0)     # back to start
        return int(size)
    except Exception:
        return -1  # unknown


@router.get("/me", response_model=UserResponse)
@limiter.limit(RATE_LIMIT_VALUE, key_func=get_remote_address)
def me(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/avatar", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # basic content-type validation
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WEBP images are allowed")

    # basic file size validation (best-effort)
    size = _get_upload_size(file)
    if size != -1 and size > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 2MB.")

    # upload to Cloudinary with transformation (250x250 crop fill)
    try:
        url = upload_avatar(file.file, public_id=f"user_{current_user.id}")
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Cloudinary upload failed")

    current_user.avatar_url = url
    db.commit()
    db.refresh(current_user)
    return current_user