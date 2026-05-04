"""
FastAPI application entrypoint.

This module creates the FastAPI app instance and configures:
- Rate limit exception handling (SlowAPI)
- CORS middleware
- API routers (auth, users, contacts)

Notes:
- DB migrations are handled via Alembic; this file does not create tables.
- All configuration is loaded from environment variables (.env) via app.config.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.contacts import router as contacts_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.config import CORS_ORIGINS
from app.limiter import limiter

app = FastAPI(title="Contacts REST API", version="1.0.0")

# --- Rate limit (SlowAPI) ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Routers ---
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")


@app.get("/")
def root():
    """
    Healthcheck endpoint.

    :return: Simple message dict.
    """
    return {"message": "API is running. Open /docs"}
