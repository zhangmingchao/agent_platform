from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..auth import authenticate_user, create_token, get_current_user
from ..database import execute, fetch_one

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=100)
    new_password: str = Field(min_length=6, max_length=20)


@router.post("/login")
async def api_login(req: LoginRequest):
    user = await authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user["id"], user["username"])
    return {"token": token, "user_id": user["id"], "username": user["username"]}


@router.post("/register")
async def api_register(req: RegisterRequest):
    existing = await fetch_one("SELECT id FROM users WHERE username=%s", (req.username,))
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user_id = await execute(
        "INSERT INTO users (username, password, created_at) VALUES (%s, %s, %s)",
        (req.username, req.password, _now()),
    )
    return {"user_id": user_id, "username": req.username}


@router.get("/me")
async def api_me(request: Request):
    return get_current_user(request)


@router.put("/password")
async def api_change_password(data: ChangePasswordRequest, request: Request):
    user = get_current_user(request)

    if data.new_password == data.current_password:
        raise HTTPException(status_code=400, detail="新密码不能与当前密码相同")
    if not data.new_password.strip():
        raise HTTPException(status_code=400, detail="新密码不能为空")

    existing = await fetch_one(
        "SELECT id FROM users WHERE id=%s AND password=%s",
        (user["user_id"], data.current_password),
    )
    if not existing:
        raise HTTPException(status_code=400, detail="当前密码错误")

    await execute(
        "UPDATE users SET password=%s WHERE id=%s",
        (data.new_password, user["user_id"]),
    )
    return {
        "success": True,
        "message": "密码修改成功，请重新登录",
        "require_relogin": True,
    }


@router.post("/logout")
async def api_logout():
    return {"success": True, "message": "请在前端清除 token"}
