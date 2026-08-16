"""
Authentication module — JWT + Redis token management with FastAPI Depends support.
"""
import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from fastapi import Request, HTTPException

from .config import JWT_ALGORITHM, JWT_EXPIRE_HOURS, JWT_SECRET
from .database import fetch_one
from .redis_client import set_token, get_token_user_id, delete_token

log = logging.getLogger("agent-platform")


async def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = await fetch_one(
        "SELECT id, username FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    return user


def create_token(user_id: int, username: str) -> str:
    """Create JWT token. Caller must also call set_token() to store in Redis."""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def login_and_store_token(user_id: int, username: str) -> str:
    """Create JWT token and store in Redis."""
    token = create_token(user_id, username)
    await set_token(token, user_id)
    log.info("[Auth] login user=%s, token stored in Redis", username)
    return token


async def get_current_user(request: Request) -> Dict:
    """
    Required auth — raises 401 if not authenticated.
    Can be used as Depends(get_current_user) or called directly with request.
    Checks Redis for token validity, then decodes JWT for user info.
    """
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="未登录")

    # Check Redis — token must exist
    user_id = await get_token_user_id(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="token无效或已过期，请重新登录")

    # Decode JWT for username
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"user_id": payload["user_id"], "username": payload["username"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的token")


async def get_current_user_optional(request: Request) -> Optional[Dict]:
    """
    Optional auth — returns user dict if authenticated, None otherwise.
    Use for endpoints like logout/register that don't require auth but benefit from it.
    """
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.query_params.get("token")

    if not token:
        return None

    user_id = await get_token_user_id(token)
    if not user_id:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"user_id": payload["user_id"], "username": payload["username"]}
    except Exception:
        return None


async def logout_token(request: Request) -> bool:
    """Delete token from Redis (logout). Returns True if token was found."""
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.query_params.get("token")

    if not token:
        return False

    await delete_token(token)
    log.info("[Auth] logout, token deleted from Redis")
    return True
