from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..config import LLM_MODEL_OPTIONS
from ..services.agent_service import create_agent, delete_agent, get_agent, list_agents, update_agent

router = APIRouter(prefix="/api", tags=["Agents"])


class AgentCreate(BaseModel):
    name: str = "新Agent"
    description: str = ""
    system_prompt: str = ""
    iteration_count: int = Field(default=6, ge=1, le=100)
    model: str = "deepseek-chat"
    model_config_id: Optional[int] = None
    temperature: float = 0.7
    skill_ids: List[int] = Field(default_factory=list)
    mcp_ids: List[int] = Field(default_factory=list)


class AgentUpdate(AgentCreate):
    pass


@router.get("/ll_models")
async def api_list_llm_models(user: dict = Depends(get_current_user)):
    return LLM_MODEL_OPTIONS


@router.get("/agentsList")
async def api_list_agents(user: dict = Depends(get_current_user)):
    return await list_agents(user["user_id"])


@router.get("/agents/{agent_id}")
async def api_get_agent(agent_id: int, user: dict = Depends(get_current_user)):
    agent = await get_agent(agent_id, user["user_id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent


@router.post("/agents")
async def api_create_agent(data: AgentCreate, user: dict = Depends(get_current_user)):
    return await create_agent(user["user_id"], data.dict())


@router.put("/agents/{agent_id}")
async def api_update_agent(agent_id: int, data: AgentUpdate, user: dict = Depends(get_current_user)):
    agent = await update_agent(agent_id, user["user_id"], data.dict())
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent


@router.delete("/agents/{agent_id}")
async def api_delete_agent(agent_id: int, user: dict = Depends(get_current_user)):
    success = await delete_agent(agent_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return {"success": True}
