"""
Redis cache utilities.

This module provides a small helper layer over Redis for storing JSON payloads.
It is used primarily for caching the current user in get_current_user to avoid
repeated DB queries on each request.

Configuration:
- REDIS_URL is read from .env via app.config

Key conventions:
- user:{email}  -> cached user payload (id, email, is_verified, avatar_url, role)

Security:
- Do NOT store sensitive fields (e.g., hashed_password) in cache.
- Cache should be invalidated when user data changes (verify, avatar update, role change, password reset).
"""

import json
import redis

from app.config import REDIS_URL


# Global Redis client. decode_responses=True returns strings instead of bytes.
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_json(key: str) -> dict | None:
    """
    Get a JSON object from Redis by key.

    Args:
        key: Redis key.

    Returns:
        Parsed dict if key exists and contains valid JSON, otherwise None.
    """
    raw = redis_client.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def set_json(key: str, value: dict, ttl: int) -> None:
    """
    Set a JSON object in Redis with TTL.

    Args:
        key: Redis key.
        value: JSON-serializable dict.
        ttl: Time-to-live in seconds.

    Returns:
        None
    """
    redis_client.setex(key, ttl, json.dumps(value))


def delete_key(key: str) -> None:
    """
    Delete a Redis key.

    Args:
        key: Redis key.

    Returns:
        None
    """
    redis_client.delete(key)


def user_cache_key(email: str) -> str:
    """
    Build the Redis cache key for a user.

    Args:
        email: User email.

    Returns:
        Cache key string in the form "user:{email}".
    """
    return f"user:{email}"


def invalidate_user_cache(email: str) -> None:
    """
    Invalidate cached user data for a given email.

    Args:
        email: User email.

    Returns:
        None
    """
    delete_key(user_cache_key(email))