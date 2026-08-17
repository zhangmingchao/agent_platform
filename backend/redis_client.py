"""Redis client for token storage."""
import logging
from typing import Optional

import redis.asyncio as aioredis

from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, JWT_EXPIRE_HOURS

log = logging.getLogger("agent-platform")

_pool: Optional[aioredis.ConnectionPool] = None


async def get_redis() -> aioredis.Redis:
    """Get Redis connection from pool."""
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD or None,
            decode_responses=True,
        )
    return aioredis.Redis(connection_pool=_pool)


async def close_redis():
    """Close Redis connection pool on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None


async def set_token(token: str, user_id: int):
    """Store token → user_id in Redis with TTL matching JWT expiry."""
    r = await get_redis()
    await r.setex(f"token:{token}", JWT_EXPIRE_HOURS * 3600, str(user_id))


async def get_token_user_id(token: str) -> Optional[int]:
    """Get user_id by token from Redis. Returns None if not found."""
    r = await get_redis()
    val = await r.get(f"token:{token}")
    return int(val) if val else None


async def delete_token(token: str):
    """Delete token from Redis (logout)."""
    r = await get_redis()
    await r.delete(f"token:{token}")
