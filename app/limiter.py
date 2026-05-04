"""
Rate limiting setup (SlowAPI).

This module defines a global Limiter instance used across the application.
It is attached to FastAPI app state in app.main.

Key function:
- Uses client remote address as the rate-limit key.

Endpoints:
- /api/users/me is rate-limited via decorator in app.api.users.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global limiter instance (attached in app.main)
limiter = Limiter(key_func=get_remote_address)