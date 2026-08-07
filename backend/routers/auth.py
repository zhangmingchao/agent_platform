from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

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


@router.post("/logout")
async def api_logout():
    return {"success": True, "message": "请在前端清除 token"}
