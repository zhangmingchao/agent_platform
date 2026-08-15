from datetime import datetime
from typing import Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from ..auth import get_current_user
from ..database import execute, fetch_all, fetch_one

router = APIRouter(prefix="/api/sessions", tags=["Chat Sessions"])


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


class SessionPayload(BaseModel):
    target_type: Literal["crew", "flow"]
    target_id: int


async def _target_exists(user_id: int, target_type: str, target_id: int) -> bool:
    table = "crews" if target_type == "crew" else "flows"
    return bool(await fetch_one(f"SELECT id FROM {table} WHERE id=%s AND user_id=%s", (target_id, user_id)))


@router.get("")
async def api_list_sessions(
    target_type: Optional[Literal["crew", "flow"]] = Query(None),
    target_id: Optional[int] = Query(None),
    user: Dict = Depends(get_current_user),
):
    user_id = user["user_id"]
    if target_type and target_id is not None:
        return await fetch_all(
            "SELECT id, target_type, target_id, title, created_at, updated_at FROM chat_sessions "
            "WHERE user_id=%s AND target_type=%s AND target_id=%s ORDER BY updated_at DESC",
            (user_id, target_type, target_id),
        )
    return await fetch_all(
        "SELECT id, target_type, target_id, title, created_at, updated_at FROM chat_sessions "
        "WHERE user_id=%s ORDER BY updated_at DESC",
        (user_id,),
    )


@router.post("")
async def api_create_session(data: SessionPayload, user: Dict = Depends(get_current_user)):
    user_id = user["user_id"]
    if not await _target_exists(user_id, data.target_type, data.target_id):
        raise HTTPException(status_code=404, detail="执行目标不存在")
    session_id = await execute(
        "INSERT INTO chat_sessions (user_id, target_type, target_id, title, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, data.target_type, data.target_id, "新对话", _now(), _now()),
    )
    return {"session_id": session_id}


@router.put("/{session_id}")
async def api_rename_session(session_id: int, request: Request, user: Dict = Depends(get_current_user)):
    user_id = user["user_id"]
    title = (await request.json()).get("title", "新对话")
    await execute(
        "UPDATE chat_sessions SET title=%s WHERE id=%s AND user_id=%s",
        (title, session_id, user_id),
    )
    return {"success": True}


@router.delete("/{session_id}")
async def api_delete_session(session_id: int, user: Dict = Depends(get_current_user)):
    user_id = user["user_id"]
    if not await fetch_one("SELECT id FROM chat_sessions WHERE id=%s AND user_id=%s", (session_id, user_id)):
        raise HTTPException(status_code=404, detail="会话不存在")
    await execute("DELETE FROM chat_sessions WHERE id=%s AND user_id=%s", (session_id, user_id))
    return {"success": True}


@router.get("/{session_id}/messages")
async def api_get_messages(session_id: int, user: Dict = Depends(get_current_user)):
    user_id = user["user_id"]
    if not await fetch_one("SELECT id FROM chat_sessions WHERE id=%s AND user_id=%s", (session_id, user_id)):
        return []
    return await fetch_all(
        "SELECT role, content, created_at FROM chat_messages WHERE session_id=%s ORDER BY id",
        (session_id,),
    )
