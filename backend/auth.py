"""
认证模块 —— 基于 JWT + Redis 的 Token 管理，支持 FastAPI Depends 依赖注入。
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
    """创建 JWT Token。调用方还需调用 set_token() 将 Token 存入 Redis。"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def login_and_store_token(user_id: int, username: str) -> str:
    """创建 JWT Token 并存入 Redis。"""
    token = create_token(user_id, username)
    await set_token(token, user_id)
    log.info("[Auth] login user=%s, token stored in Redis", username)
    return token


async def get_current_user(request: Request) -> Dict:
    """
    强制认证 —— 未认证时抛出 401 错误。
    可作为 Depends(get_current_user) 使用，或直接传入 request 调用。
    先检查 Redis 中 Token 是否有效，再解码 JWT 获取用户信息。
    """
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="未登录")

    # 检查 Redis —— Token 必须存在
    user_id = await get_token_user_id(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="token无效或已过期，请重新登录")

    # 解码 JWT 获取用户名
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"user_id": payload["user_id"], "username": payload["username"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的token")


async def get_current_user_optional(request: Request) -> Optional[Dict]:
    """
    可选认证 —— 已认证则返回用户字典，否则返回 None。
    适用于登出/注册等不需要强制认证但能从中受益的接口。
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
    """从 Redis 删除 Token（登出）。Token 存在时返回 True。"""
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
