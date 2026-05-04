"""
JWT utilities.

This module is responsible for creating and decoding JWT tokens used by the API.

Token types:
- access: short-lived token used for authorization on protected endpoints
- refresh: long-lived token used to obtain a new access token (rotation supported)
- verify: token used for email verification
- reset: token used for password reset

All secrets and lifetimes are configured through environment variables (.env).
"""

from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from app.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRES_DAYS,
    PASSWORD_RESET_TOKEN_EXPIRES_MINUTES,
)


def create_access_token(subject: str) -> str:
    """
    Create a JWT access token.

    Access token is short-lived and is used in Authorization header:
        Authorization: Bearer <access_token>

    Args:
        subject: Token subject (user email).

    Returns:
        Encoded JWT access token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=int(JWT_ACCESS_TOKEN_EXPIRES_MINUTES))
    payload = {
        "sub": subject,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """
    Create a JWT refresh token.

    Refresh token is long-lived and is used to refresh/rotate tokens via:
        POST /api/auth/refresh

    Args:
        subject: Token subject (user email).

    Returns:
        Encoded JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=int(JWT_REFRESH_TOKEN_EXPIRES_DAYS))
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_email_verify_token(subject: str) -> str:
    """
    Create a JWT email verification token.

    This token is sent by email after signup and used by:
        GET /api/auth/verify?token=...

    Args:
        subject: Token subject (user email).

    Returns:
        Encoded JWT verify token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=24)
    payload = {
        "sub": subject,
        "type": "verify",
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_password_reset_token(subject: str) -> str:
    """
    Create a JWT password reset token (short TTL).

    This token is sent by email and used by:
        POST /api/auth/password-reset/confirm

    Args:
        subject: Token subject (user email).

    Returns:
        Encoded JWT reset token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=int(PASSWORD_RESET_TOKEN_EXPIRES_MINUTES))
    payload = {
        "sub": subject,
        "type": "reset",
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded JWT payload as dict.

    Raises:
        ValueError: If token is invalid or cannot be decoded.
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise ValueError("Invalid token")