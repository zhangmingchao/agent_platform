from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..config import LLM_MODEL_OPTIONS
from ..core.schema_dsl import json_schema_to_python_schema, python_schema_to_json_schema
from ..services.agent_service import create_agent, delete_agent, get_agent, list_agents, update_agent

router = APIRouter(prefix="/api", tags=["Agents"])


class AgentCreate(BaseModel):
    name: str = "新Agent"
    description: str = ""
    system_prompt: str = ""
    prompt_variables: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None
    iteration_count: int = Field(default=6, ge=1, le=100)
    model: str = "deepseek-chat"
    model_config_id: Optional[int] = None
    temperature: float = 0.7
    skill_ids: List[int] = Field(default_factory=list)
    mcp_ids: List[int] = Field(default_factory=list)


class AgentUpdate(AgentCreate):
    pass


class PythonSchemaRequest(BaseModel):
    source: str = Field(min_length=1, max_length=20_000)


class JsonSchemaRequest(BaseModel):
    schema_data: Dict[str, Any]


@router.get("/ll_models")
async def api_list_llm_models(user: dict = Depends(get_current_user)):
    return LLM_MODEL_OPTIONS


@router.get("/agentsList")
async def api_list_agents(user: dict = Depends(get_current_user)):
    agents = await list_agents(user["user_id"])
    return [agent.to_summary_dict() for agent in agents]


@router.post("/output-schema/python-to-json")
async def api_python_schema_to_json(
    data: PythonSchemaRequest,
    user: dict = Depends(get_current_user),
):
    """安全解析 Python 风格描述；只读 AST，绝不执行用户提交的代码。"""
    try:
        return {"schema": python_schema_to_json_schema(data.source)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/output-schema/json-to-python")
async def api_json_schema_to_python(
    data: JsonSchemaRequest,
    user: dict = Depends(get_current_user),
):
    """将数据库中的标准 JSON Schema 格式化为可编辑的 Python 风格描述。"""
    try:
        return {"source": json_schema_to_python_schema(data.schema_data)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/agents/{agent_id}")
async def api_get_agent(agent_id: int, user: dict = Depends(get_current_user)):
    agent = await get_agent(agent_id, user["user_id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent.to_dict()


@router.post("/agents")
async def api_create_agent(data: AgentCreate, user: dict = Depends(get_current_user)):
    agent = await create_agent(user["user_id"], data.dict())
    return agent.to_dict()


@router.put("/agents/{agent_id}")
async def api_update_agent(agent_id: int, data: AgentUpdate, user: dict = Depends(get_current_user)):
    agent = await update_agent(agent_id, user["user_id"], data.dict())
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent.to_dict()


@router.delete("/agents/{agent_id}")
async def api_delete_agent(agent_id: int, user: dict = Depends(get_current_user)):
    success = await delete_agent(agent_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return {"success": True}
