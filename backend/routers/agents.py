from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agents import create_agent, delete_agent, get_agent, list_agents, update_agent
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Agents"])


class AgentCreate(BaseModel):
    name: str = "新Agent"
    description: str = ""
    system_prompt: str = ""
    iteration_count: int = Field(default=6, ge=1, le=100)
    model: str = "deepseek-chat"
    temperature: float = 0.7
    skill_ids: List[int] = Field(default_factory=list)
    mcp_ids: List[int] = Field(default_factory=list)


class AgentUpdate(AgentCreate):
    pass


@router.get("/agentsList")
async def api_list_agents(request: Request):
    user = get_current_user(request)
    return await list_agents(user["user_id"])


@router.get("/agents/{agent_id}")
async def api_get_agent(agent_id: int, request: Request):
    user = get_current_user(request)
    agent = await get_agent(agent_id, user["user_id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent


@router.post("/agents")
async def api_create_agent(data: AgentCreate, request: Request):
    user = get_current_user(request)
    return await create_agent(user["user_id"], data.dict())


@router.put("/agents/{agent_id}")
async def api_update_agent(agent_id: int, data: AgentUpdate, request: Request):
    user = get_current_user(request)
    agent = await update_agent(agent_id, user["user_id"], data.dict())
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent


@router.delete("/agents/{agent_id}")
async def api_delete_agent(agent_id: int, request: Request):
    user = get_current_user(request)
    success = await delete_agent(agent_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return {"success": True}
