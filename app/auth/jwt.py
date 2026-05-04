"""
JWT utilities.

This module creates and decodes JWT tokens used by the API.

Token types:

- access: short-lived token used for authorization on protected endpoints
- refresh: long-lived token used to obtain a new access token (supports rotation)
- verify: token used for email verification
- reset: token used for password reset

All secrets and lifetimes are configured through environment variables (.env).
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

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

    :param subject: Token subject (user email).
    :return: Encoded JWT access token string.
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

    Refresh tokens must be unique even if issued within the same second.
    We include a random ``jti`` claim to guarantee uniqueness (rotation safety).

    :param subject: Token subject (user email).
    :return: Encoded JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=int(JWT_REFRESH_TOKEN_EXPIRES_DAYS))
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_email_verify_token(subject: str) -> str:
    """
    Create a JWT email verification token (type="verify").

    :param subject: Token subject (user email).
    :return: Encoded JWT verify token string.
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
    Create a JWT password reset token (type="reset") with short TTL.

    :param subject: Token subject (user email).
    :return: Encoded JWT reset token string.
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
    Decode and validate a JWT token.

    :param token: Encoded JWT string.
    :return: Decoded JWT payload as dict.
    :raises ValueError: If token is invalid or cannot be decoded.
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise ValueError("Invalid token")
