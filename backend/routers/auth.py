from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..auth import authenticate_user, get_current_user, login_and_store_token, logout_token
from ..config import (
    AUTH_RATE_LIMIT_WINDOW_SECONDS,
    LOGIN_RATE_LIMIT_PER_IP,
    LOGIN_RATE_LIMIT_PER_USERNAME,
    REGISTER_RATE_LIMIT_PER_IP,
)
from ..database import execute, fetch_one
from ..rate_limit import RateLimitRule, enforce_rate_limit, get_client_ip
from ..security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

LOGIN_IP_RULE = RateLimitRule(
    name="auth-login-ip",
    limit=LOGIN_RATE_LIMIT_PER_IP,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)
LOGIN_USERNAME_RULE = RateLimitRule(
    name="auth-login-username",
    limit=LOGIN_RATE_LIMIT_PER_USERNAME,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)
REGISTER_IP_RULE = RateLimitRule(
    name="auth-register-ip",
    limit=REGISTER_RATE_LIMIT_PER_IP,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


class LoginRequest(BaseModel):
    """登录请求参数。"""

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    """注册请求参数。"""

    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class ChangePasswordRequest(BaseModel):
    """修改密码请求参数。"""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


@router.post("/login")
async def api_login(req: LoginRequest, request: Request) -> Dict[str, Any]:
    """登录 — 创建 JWT 并将令牌存储到 Redis。"""
    await enforce_rate_limit(LOGIN_IP_RULE, get_client_ip(request))
    await enforce_rate_limit(LOGIN_USERNAME_RULE, req.username.strip().lower())
    user = await authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = await login_and_store_token(user["id"], user["username"])
    return {"token": token, "user_id": user["id"], "username": user["username"]}


@router.post("/register")
async def api_register(req: RegisterRequest, request: Request) -> Dict[str, Any]:
    """注册 — 无需身份验证。"""
    await enforce_rate_limit(REGISTER_IP_RULE, get_client_ip(request))
    existing = await fetch_one("SELECT id FROM users WHERE username=%s", (req.username,))
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user_id = await execute(
        "INSERT INTO users (username, password, created_at) VALUES (%s, %s, %s)",
        (req.username, hash_password(req.password), _now()),
    )
    return {"user_id": user_id, "username": req.username}


@router.get("/me")
async def api_me(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """获取当前用户信息 — 需要身份验证。"""
    return user


@router.put("/password")
async def api_change_password(
    data: ChangePasswordRequest,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """修改密码 — 需要身份验证。"""
    if data.new_password == data.current_password:
        raise HTTPException(status_code=400, detail="新密码不能与当前密码相同")

    existing = await fetch_one("SELECT id, password FROM users WHERE id=%s", (user["user_id"],))
    if not existing or not verify_password(
        data.current_password,
        str(existing.get("password") or ""),
    ).verified:
        raise HTTPException(status_code=400, detail="当前密码错误")

    await execute(
        "UPDATE users SET password=%s WHERE id=%s",
        (hash_password(data.new_password), user["user_id"]),
    )
    return {
        "success": True,
        "message": "密码修改成功，请重新登录",
        "require_relogin": True,
    }


@router.post("/logout")
async def api_logout(request: Request) -> Dict[str, Any]:
    """退出登录 — 从 Redis 删除令牌。无需身份验证（可选验证）。"""
    deleted = await logout_token(request)
    if deleted:
        return {"success": True, "message": "已退出登录"}
    return {"success": True, "message": "无需退出（未检测到有效token）"}
