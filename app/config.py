"""
Application configuration.

This module loads all configuration values from environment variables (.env)
using python-dotenv. No sensitive values should be hard-coded in source code.

Configuration groups:
- Database (PostgreSQL)
- JWT settings (access, refresh, verify, reset tokens)
- SMTP settings (Mailtrap in development)
- CORS settings
- Rate limiting settings
- Cloudinary settings
- Redis cache settings
- Roles and default avatar settings

Notes:
- In Docker Compose, DB_HOST should be set to the service name (e.g., "db").
- In Docker Compose, REDIS_URL should use the service name (e.g., "redis").
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    """
    Read an environment variable and normalize it.

    :param name: Environment variable name.
    :param default: Default value if variable is missing.
    :return: Trimmed string value.
    """
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


# --- Database ---
DB_USER = _env("DB_USER", "postgres")
DB_PASSWORD = _env("DB_PASSWORD", "mysecretpassword")
DB_HOST = _env("DB_HOST", "localhost")
DB_PORT = _env("DB_PORT", "5432")
DB_NAME = _env("DB_NAME", "postgres")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- JWT ---
JWT_SECRET_KEY = _env("JWT_SECRET_KEY", "CHANGE_ME")
JWT_ALGORITHM = _env("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(_env("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30") or "30")
JWT_REFRESH_TOKEN_EXPIRES_DAYS = int(_env("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7") or "7")

# Password reset token TTL (minutes)
PASSWORD_RESET_TOKEN_EXPIRES_MINUTES = int(_env("PASSWORD_RESET_TOKEN_EXPIRES_MINUTES", "30") or "30")

# --- Email (SMTP / Mailtrap) ---
SMTP_HOST = _env("SMTP_HOST", "")
SMTP_PORT = _env("SMTP_PORT", "587")
SMTP_USER = _env("SMTP_USER", "")
SMTP_PASSWORD = _env("SMTP_PASSWORD", "")
MAIL_FROM = _env("MAIL_FROM", "noreply@example.com")
APP_BASE_URL = _env("APP_BASE_URL", "http://localhost:8000")

# --- CORS ---
CORS_ORIGINS = _env("CORS_ORIGINS", "")

# --- Rate limiting ---
ME_RATE_LIMIT = _env("ME_RATE_LIMIT", "5/minute") or "5/minute"

# --- Cloudinary ---
CLOUDINARY_CLOUD_NAME = _env("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = _env("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = _env("CLOUDINARY_API_SECRET", "")

# --- Redis cache ---
REDIS_URL = _env("REDIS_URL", "redis://redis:6379/0")
REDIS_TTL_SECONDS = int(_env("REDIS_TTL_SECONDS", "300") or "300")

# --- Roles / Default avatar ---
ADMIN_EMAIL = _env("ADMIN_EMAIL", "admin@example.com")
DEFAULT_AVATAR_URL = _env("DEFAULT_AVATAR_URL", "")