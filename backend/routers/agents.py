from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..config import LLM_MODEL_OPTIONS
from ..services.agent_service import create_agent, delete_agent, get_agent, list_agents, update_agent

router = APIRouter(prefix="/api", tags=["Agents"])


class AgentPayload(BaseModel):
    name: str = Field(default="新 Agent", min_length=1, max_length=200)
    description: str = ""
    role: str = Field(default="AI Agent", min_length=1, max_length=200)
    goal: str = ""
    backstory: str = ""
    system_prompt: str = ""
    model: str = "deepseek-chat"
    temperature: float = Field(default=0.7, ge=0, le=2)
    iteration_count: int = Field(default=6, ge=1, le=100)
    allow_delegation: bool = False
    reasoning: bool = False
    planning: bool = False
    memory: bool = False
    enabled: bool = True
    skill_ids: List[int] = Field(default_factory=list)
    mcp_ids: List[int] = Field(default_factory=list)


@router.get("/ll_models")
async def api_list_llm_models(request: Request):
    get_current_user(request)
    return LLM_MODEL_OPTIONS


@router.get("/agentsList")
async def api_list_agents(request: Request):
    return await list_agents(get_current_user(request)["user_id"])


@router.get("/agents/{agent_id}")
async def api_get_agent(agent_id: int, request: Request):
    agent = await get_agent(agent_id, get_current_user(request)["user_id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent


@router.post("/agents")
async def api_create_agent(data: AgentPayload, request: Request):
    try:
        return await create_agent(get_current_user(request)["user_id"], data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/agents/{agent_id}")
async def api_update_agent(agent_id: int, data: AgentPayload, request: Request):
    try:
        agent = await update_agent(agent_id, get_current_user(request)["user_id"], data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent


@router.delete("/agents/{agent_id}")
async def api_delete_agent(agent_id: int, request: Request):
    try:
        deleted = await delete_agent(agent_id, get_current_user(request)["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return {"success": True}
