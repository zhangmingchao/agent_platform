from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from ..auth import get_current_user
from ..database import execute, fetch_all, fetch_one

router = APIRouter(prefix="/api/sessions", tags=["Chat Sessions"])


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


@router.get("")
async def api_list_sessions(request: Request):
    user = get_current_user(request)
    return await fetch_all(
        "SELECT id, agent_id, title, created_at, updated_at FROM chat_sessions "
        "WHERE user_id=%s ORDER BY updated_at DESC",
        (user["user_id"],),
    )


@router.post("")
async def api_create_session(request: Request):
    user = get_current_user(request)
    body = await request.json()
    agent_id = body.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="需要 agent_id")
    session_id = await execute(
        "INSERT INTO chat_sessions (user_id, agent_id, title, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s)",
        (user["user_id"], agent_id, "新对话", _now(), _now()),
    )
    return {"session_id": session_id}


@router.put("/{session_id}")
async def api_rename_session(session_id: int, request: Request):
    user = get_current_user(request)
    body = await request.json()
    title = body.get("title", "新对话")
    await execute(
        "UPDATE chat_sessions SET title=%s WHERE id=%s AND user_id=%s",
        (title, session_id, user["user_id"]),
    )
    return {"success": True}


@router.delete("/{session_id}")
async def api_delete_session(session_id: int, request: Request):
    user = get_current_user(request)
    await execute(
        "DELETE FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"]),
    )
    return {"success": True}


@router.get("/{session_id}/messages")
async def api_get_messages(session_id: int, request: Request):
    user = get_current_user(request)
    session = await fetch_one(
        "SELECT id, agent_id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"]),
    )
    if not session:
        return []
    return await fetch_all(
        "SELECT role, content, created_at FROM chat_messages "
        "WHERE session_id=%s ORDER BY id ASC",
        (session_id,),
    )
