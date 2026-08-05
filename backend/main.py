"""
Agent Platform - Backend API
FastAPI application providing:
- Authentication (login/logout)
- Agent CRUD
- Skill management
- MCP configuration
- Streaming chat API
"""
import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query, Request, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional as OptionalType

from config import SERVER_PORT, SKILLS_DIR
from database import init_db, fetch_all, fetch_one, execute
from auth import authenticate_user, create_token, get_current_user
from agents import list_agents, get_agent, create_agent, update_agent, delete_agent
from skills import list_skills, get_skill, create_skill, delete_skill, get_agent_skills
from mcp_configs import list_mcp_configs, get_mcp_config, create_mcp_config, update_mcp_config, delete_mcp_config, get_agent_mcps
from mcp_client import McpClient
from chat_engine import chat_stream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("agent-platform")

app = FastAPI(title="Agent Platform")


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


@app.on_event("startup")
async def startup():
    await init_db()
    log.info("数据库初始化完成")


# ==================== 认证 ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
async def api_login(req: LoginRequest):
    user = await authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user["id"], user["username"])
    return {"token": token, "user_id": user["id"], "username": user["username"]}


@app.post("/api/auth/register")
async def api_register(req: RegisterRequest):
    existing = await fetch_one("SELECT id FROM users WHERE username=%s", (req.username,))
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user_id = await execute(
        "INSERT INTO users (username, password, created_at) VALUES (%s, %s, %s)",
        (req.username, req.password, _now())
    )
    return {"user_id": user_id, "username": req.username}


@app.get("/api/auth/me")
async def api_me(request: Request):
    return get_current_user(request)


@app.post("/api/auth/logout")
async def api_logout():
    return {"success": True, "message": "请在前端清除 token"}


# ==================== Agent ====================

class AgentCreate(BaseModel):
    name: str = "新Agent"
    description: str = ""
    system_prompt: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.7
    skill_ids: List[int] = []
    mcp_ids: List[int] = []


class AgentUpdate(AgentCreate):
    pass


@app.get("/api/agents")
async def api_list_agents(request: Request):
    user = get_current_user(request)
    return await list_agents(user["user_id"])


@app.get("/api/agents/{agent_id}")
async def api_get_agent(agent_id: int, request: Request):
    user = get_current_user(request)
    agent = await get_agent(agent_id, user["user_id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent


@app.post("/api/agents")
async def api_create_agent(data: AgentCreate, request: Request):
    user = get_current_user(request)
    return await create_agent(user["user_id"], data.dict())


@app.put("/api/agents/{agent_id}")
async def api_update_agent(agent_id: int, data: AgentUpdate, request: Request):
    user = get_current_user(request)
    agent = await update_agent(agent_id, user["user_id"], data.dict())
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent


@app.delete("/api/agents/{agent_id}")
async def api_delete_agent(agent_id: int, request: Request):
    user = get_current_user(request)
    success = await delete_agent(agent_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return {"success": True}


# ==================== Skill ====================

@app.get("/api/skills")
async def api_list_skills(request: Request):
    user = get_current_user(request)
    return await list_skills(user["user_id"])


@app.get("/api/skills/{skill_id}")
async def api_get_skill(skill_id: int, request: Request):
    user = get_current_user(request)
    skill = await get_skill(skill_id, user["user_id"])
    if not skill:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return skill


@app.post("/api/skills/upload")
async def api_upload_skill(
    request: Request,
    file: UploadFile = File(...),
):
    user = get_current_user(request)
    content = await file.read()
    content_text = content.decode("utf-8")

    name = file.filename.replace(".md", "").replace(".txt", "")
    lines = content_text.split("\n")
    description = ""
    for line in lines[:5]:
        line = line.strip()
        if line.startswith("# "):
            name = line[2:].strip() or name
        elif line.startswith("description:"):
            description = line.split(":", 1)[1].strip()

    return await create_skill(user["user_id"], name, description, content_text)


@app.post("/api/skills")
async def api_create_skill(request: Request):
    user = get_current_user(request)
    body = await request.json()
    return await create_skill(
        user["user_id"],
        body.get("name", ""),
        body.get("description", ""),
        body.get("content", "")
    )


@app.delete("/api/skills/{skill_id}")
async def api_delete_skill(skill_id: int, request: Request):
    user = get_current_user(request)
    success = await delete_skill(skill_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Skill 不存在")
    return {"success": True}


# ==================== MCP Config ====================

@app.get("/api/mcp-configs")
async def api_list_mcp_configs(request: Request):
    user = get_current_user(request)
    return await list_mcp_configs(user["user_id"])


@app.get("/api/mcp-configs/{config_id}")
async def api_get_mcp_config(config_id: int, request: Request):
    user = get_current_user(request)
    cfg = await get_mcp_config(config_id, user["user_id"])
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return cfg


@app.post("/api/mcp-configs")
async def api_create_mcp(request: Request):
    user = get_current_user(request)
    body = await request.json()
    return await create_mcp_config(user["user_id"], body)


@app.put("/api/mcp-configs/{config_id}")
async def api_update_mcp(config_id: int, request: Request):
    user = get_current_user(request)
    body = await request.json()
    cfg = await update_mcp_config(config_id, user["user_id"], body)
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return cfg


@app.delete("/api/mcp-configs/{config_id}")
async def api_delete_mcp(config_id: int, request: Request):
    user = get_current_user(request)
    success = await delete_mcp_config(config_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return {"success": True}


async def _run_mcp_request(func, *args):
    """Run the synchronous MCP client without blocking FastAPI's event loop."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args))


@app.get("/api/mcp-configs/{config_id}/tools")
async def api_list_mcp_tools(config_id: int, request: Request):
    user = get_current_user(request)
    cfg = await get_mcp_config(config_id, user["user_id"])
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")

    try:
        client = McpClient(cfg["base_url"], cfg["endpoint"])
        tools = await _run_mcp_request(client.list_tools)
        return {"tools": tools}
    except Exception as exc:
        log.exception("获取 MCP 工具失败: config_id=%s", config_id)
        raise HTTPException(status_code=502, detail=f"连接 MCP 失败: {exc}")


@app.post("/api/mcp-configs/{config_id}/call")
async def api_call_mcp_tool(config_id: int, request: Request):
    user = get_current_user(request)
    cfg = await get_mcp_config(config_id, user["user_id"])
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")

    body = await request.json()
    tool_name = body.get("name", "").strip()
    arguments = body.get("arguments", {})
    if not tool_name:
        raise HTTPException(status_code=400, detail="需要工具名称")
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="arguments 必须是 JSON 对象")

    try:
        client = McpClient(cfg["base_url"], cfg["endpoint"])
        result = await _run_mcp_request(client.call_tool_raw, tool_name, arguments)
        return {"result": result}
    except Exception as exc:
        log.exception("调用 MCP 工具失败: config_id=%s tool=%s", config_id, tool_name)
        raise HTTPException(status_code=502, detail=f"调用 MCP 工具失败: {exc}")


# ==================== Chat Sessions ====================

@app.get("/api/sessions")
async def api_list_sessions(request: Request):
    user = get_current_user(request)
    return await fetch_all(
        "SELECT id, agent_id, title, created_at, updated_at FROM chat_sessions "
        "WHERE user_id=%s ORDER BY updated_at DESC",
        (user["user_id"],)
    )


@app.post("/api/sessions")
async def api_create_session(request: Request):
    user = get_current_user(request)
    body = await request.json()
    agent_id = body.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="需要 agent_id")
    session_id = await execute(
        "INSERT INTO chat_sessions (user_id, agent_id, title, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
        (user["user_id"], agent_id, "新对话", _now(), _now())
    )
    return {"session_id": session_id}


@app.put("/api/sessions/{session_id}")
async def api_rename_session(session_id: int, request: Request):
    user = get_current_user(request)
    body = await request.json()
    title = body.get("title", "新对话")
    await execute(
        "UPDATE chat_sessions SET title=%s WHERE id=%s AND user_id=%s",
        (title, session_id, user["user_id"])
    )
    return {"success": True}


@app.delete("/api/sessions/{session_id}")
async def api_delete_session(session_id: int, request: Request):
    user = get_current_user(request)
    await execute(
        "DELETE FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"])
    )
    return {"success": True}


@app.get("/api/sessions/{session_id}/messages")
async def api_get_messages(session_id: int, request: Request):
    user = get_current_user(request)
    session = await fetch_one(
        "SELECT id, agent_id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"])
    )
    if not session:
        return []
    return await fetch_all(
        "SELECT role, content, created_at FROM chat_messages WHERE session_id=%s ORDER BY id ASC",
        (session_id,)
    )


# ==================== Streaming Chat ====================

async def _create_chat_response(request: Request, message: str, session_id: int):
    user = get_current_user(request)

    session = await fetch_one(
        "SELECT id, agent_id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"])
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在，请重新创建会话")

    agent = await get_agent(session["agent_id"], user["user_id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    history = await fetch_all(
        "SELECT role, content FROM chat_messages WHERE session_id=%s ORDER BY id ASC",
        (session_id,)
    )
    history_messages = [{"role": m["role"], "content": m["content"]} for m in history]

    now = _now()
    await execute(
        "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
        (session_id, "user", message, now)
    )
    if not history:
        title = message[:50].replace("\n", " ").strip() or "新对话"
        await execute(
            "UPDATE chat_sessions SET title=%s WHERE id=%s",
            (title, session_id)
        )

    skills_data = await get_agent_skills(agent["id"])
    mcps_data = await get_agent_mcps(agent["id"])

    async def generate():
        full_response = []
        async for chunk in chat_stream(
            agent=agent,
            skills=skills_data,
            mcp_configs=mcps_data,
            user_message=message,
            history_messages=history_messages,
            session_id=session_id,
        ):
            if chunk.startswith("data:") and chunk != "data:\n\n":
                full_response.append(chunk[5:])
            yield chunk

        assistant_text = "".join(full_response)
        if assistant_text.strip():
            await execute(
                "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
                (session_id, "assistant", assistant_text, _now())
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/api/chat/stream")
async def api_chat_stream_post(request: Request):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id")
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    if not isinstance(session_id, int):
        raise HTTPException(status_code=400, detail="需要有效的 session_id")
    return await _create_chat_response(request, message, session_id)

@app.get("/api/chat/stream")
async def api_chat_stream(
    request: Request,
    message: str = Query(...),
    session_id: int = Query(...),
    token: Optional[str] = Query(None),
):
    return await _create_chat_response(request, message, session_id)


# ==================== Frontend ====================

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    log.info(f"Agent Platform 启动中... 端口={SERVER_PORT}")
    log.info(f"前端地址: http://127.0.0.1:{SERVER_PORT}/")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
