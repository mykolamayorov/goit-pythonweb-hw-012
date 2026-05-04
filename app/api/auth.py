"""
Auth API router.

Endpoints:
- POST /api/auth/signup
- POST /api/auth/login
- POST /api/auth/refresh
- GET  /api/auth/verify
- POST /api/auth/password-reset/request
- POST /api/auth/password-reset/confirm
"""

import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import ADMIN_EMAIL
from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate,
    UserResponse,
    TokenResponse,
    RefreshRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    create_email_verify_token,
    create_password_reset_token,
    decode_token,
)
from app.auth.security import hash_password, verify_password
from app.services.email import send_verification_email, send_password_reset_email
from app.services.redis_cache import invalidate_user_cache

router = APIRouter(prefix="/auth", tags=["Auth"])


def _hash_refresh(token: str) -> str:
    """
    Compute SHA-256 hash of refresh token for secure storage in DB.

    :param token: Raw refresh token string.
    :return: SHA-256 hex digest.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    Rules:
    - If email already exists -> 409 Conflict.
    - Password is hashed before storing.
    - Role is assigned automatically from ADMIN_EMAIL.
    - Verification email is sent via SMTP.

    :param body: UserCreate payload (email, password).
    :param db: SQLAlchemy DB session.
    :return: Created user (id, email, is_verified, avatar_url).
    :raises HTTPException: 409 if email already registered.
    """
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    role = "admin" if body.email.lower() == ADMIN_EMAIL.lower() else "user"

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        is_verified=False,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_email_verify_token(user.email)
    send_verification_email(user.email, token)

    invalidate_user_cache(user.email)
    return user


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint (OAuth2 password flow).

    :param form_data: OAuth2PasswordRequestForm (username=email, password=password).
    :param db: SQLAlchemy DB session.
    :return: TokenResponse(access_token, refresh_token, token_type="bearer").
    :raises HTTPException: 401 if credentials invalid.
    """
    email = form_data.username
    password = form_data.password

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(user.email)
    refresh_token = create_refresh_token(user.email)

    user.refresh_token_hash = _hash_refresh(refresh_token)
    db.commit()

    invalidate_user_cache(user.email)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(body: RefreshRequest, db: Session = Depends(get_db)):
    """
    Refresh token rotation endpoint.

    :param body: RefreshRequest(refresh_token).
    :param db: SQLAlchemy DB session.
    :return: New TokenResponse(access_token, refresh_token).
    :raises HTTPException: 401 if refresh token invalid/mismatch/not recognized.
    """
    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.refresh_token_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not recognized")

    if user.refresh_token_hash != _hash_refresh(body.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token mismatch")

    new_access = create_access_token(user.email)
    new_refresh = create_refresh_token(user.email)

    user.refresh_token_hash = _hash_refresh(new_refresh)
    db.commit()

    invalidate_user_cache(user.email)
    return TokenResponse(access_token=new_access, refresh_token=new_refresh, token_type="bearer")


@router.get("/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user email using a verification token (type="verify").

    :param token: Verification token.
    :param db: SQLAlchemy DB session.
    :return: Message dict.
    """
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")

    if payload.get("type") != "verify":
        raise HTTPException(status_code=400, detail="Invalid token type")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        invalidate_user_cache(user.email)
        return {"message": "Email already verified"}

    user.is_verified = True
    db.commit()

    invalidate_user_cache(user.email)
    return {"message": "Email verified successfully"}


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
def password_reset_request(body: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Request password reset.

    Security: always returns 200 OK regardless of whether email exists.

    :param body: PasswordResetRequest(email).
    :param db: SQLAlchemy DB session.
    :return: Generic message.
    """
    user = db.query(User).filter(User.email == body.email).first()
    if user:
        token = create_password_reset_token(user.email)
        send_password_reset_email(user.email, token)
    return {"message": "If the email exists, a reset link/token has been sent."}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
def password_reset_confirm(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Confirm password reset.

    :param body: PasswordResetConfirm(token, new_password).
    :param db: SQLAlchemy DB session.
    :return: Success message.
    """
    try:
        payload = decode_token(body.token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    if payload.get("type") != "reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token payload")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = hash_password(body.new_password)
    user.refresh_token_hash = None
    db.commit()

    invalidate_user_cache(user.email)
    return {"message": "Password has been reset successfully"}