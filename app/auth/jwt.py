from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRES_MINUTES


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=int(JWT_ACCESS_TOKEN_EXPIRES_MINUTES))
    payload = {"sub": subject, "type": "access", "iat": int(now.timestamp()), "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_email_verify_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=24)
    payload = {"sub": subject, "type": "verify", "iat": int(now.timestamp()), "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise ValueError("Invalid token")