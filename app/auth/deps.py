"""
Authentication dependencies (FastAPI).

This module provides reusable dependency functions for:
- resolving the current user from JWT access token (with Redis cache)
- enforcing verified email requirement
- enforcing admin-only access

Caching:
- get_current_user first tries Redis (user:{email})
- if cache miss, falls back to DB, then caches minimal safe fields

Security:
- Only access tokens (type="access") are accepted here.
- Admin/verified checks are enforced via dedicated dependencies.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth.jwt import decode_token
from app.services.redis_cache import get_json, set_json, user_cache_key
from app.config import REDIS_TTL_SECONDS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Resolve current authenticated user from JWT access token.

    The function:
    1) Decodes and validates JWT token
    2) Extracts email from payload (sub)
    3) Tries Redis cache first (key: user:{email})
    4) Falls back to DB query on cache miss
    5) Caches minimal safe fields (NO hashed_password)

    Args:
        db: SQLAlchemy session.
        token: JWT access token from Authorization header (Bearer).

    Returns:
        A lightweight User object (detached) or DB User.

    Raises:
        HTTPException: 401 if token invalid, wrong type, payload missing, or user not found.
    """
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    key = user_cache_key(email)

    # 1) Cache first
    cached = get_json(key)
    if cached:
        # detached lightweight user
        return User(
            id=cached["id"],
            email=cached["email"],
            hashed_password="!",
            is_verified=cached.get("is_verified", False),
            avatar_url=cached.get("avatar_url"),
            refresh_token_hash=None,
            role=cached.get("role", "user"),
        )

    # 2) DB fallback
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 3) Cache minimal safe fields
    set_json(
        key,
        {
            "id": user.id,
            "email": user.email,
            "is_verified": user.is_verified,
            "avatar_url": user.avatar_url,
            "role": user.role,
        },
        ttl=REDIS_TTL_SECONDS,
    )
    return user


def require_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure that current user has verified email.

    Args:
        current_user: resolved by get_current_user.

    Returns:
        current_user unchanged.

    Raises:
        HTTPException: 403 if user's email is not verified.
    """
    if not getattr(current_user, "is_verified", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure that current user has admin role.

    Args:
        current_user: resolved by get_current_user.

    Returns:
        current_user unchanged.

    Raises:
        HTTPException: 403 if role != 'admin'.
    """
    if getattr(current_user, "role", "user") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user