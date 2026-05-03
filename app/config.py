import os
from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
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
JWT_ACCESS_TOKEN_EXPIRES_MINUTES = _env("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30")

# --- Email (Mailtrap / SMTP) ---
SMTP_HOST = _env("SMTP_HOST", "")
SMTP_PORT = _env("SMTP_PORT", "587")
SMTP_USER = _env("SMTP_USER", "")
SMTP_PASSWORD = _env("SMTP_PASSWORD", "")
MAIL_FROM = _env("MAIL_FROM", "noreply@example.com")
APP_BASE_URL = _env("APP_BASE_URL", "http://localhost:8000")

# --- CORS ---
CORS_ORIGINS = _env("CORS_ORIGINS", "")

# --- Rate limit for /me (robust default if env missing/empty) ---
ME_RATE_LIMIT = _env("ME_RATE_LIMIT", "5/minute") or "5/minute"

# --- Cloudinary ---
CLOUDINARY_CLOUD_NAME = _env("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = _env("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = _env("CLOUDINARY_API_SECRET", "")