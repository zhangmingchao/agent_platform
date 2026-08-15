from typing import Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..services.crew_service import create_crew, delete_crew, get_crew, list_crews, update_crew

router = APIRouter(prefix="/api/crews", tags=["Crews"])


class TaskPayload(BaseModel):
    client_key: str
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    expected_output: str = Field(min_length=1)
    agent_id: Optional[int] = None
    order_no: int = Field(default=1, ge=1)
    async_execution: bool = False
    human_input: bool = False
    markdown: bool = True
    guardrail: str = ""
    max_retries: int = Field(default=2, ge=0, le=10)
    output_file: str = ""
    dependency_keys: List[str] = Field(default_factory=list)
    skill_ids: List[int] = Field(default_factory=list)
    mcp_ids: List[int] = Field(default_factory=list)


class CrewPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    process: Literal["sequential", "hierarchical"] = "sequential"
    manager_agent_id: Optional[int] = None
    agent_ids: List[int] = Field(min_length=1)
    tasks: List[TaskPayload] = Field(default_factory=list)
    planning: bool = False
    memory: bool = False
    cache_enabled: bool = False
    verbose: bool = False
    max_rpm: Optional[int] = Field(default=None, ge=1)
    enabled: bool = True


@router.get("")
async def api_list_crews(user: Dict = Depends(get_current_user)):
    return await list_crews(user["user_id"])


@router.get("/{crew_id}")
async def api_get_crew(crew_id: int, user: Dict = Depends(get_current_user)):
    crew = await get_crew(crew_id, user["user_id"])
    if not crew:
        raise HTTPException(status_code=404, detail="Crew 不存在")
    return crew


@router.post("")
async def api_create_crew(data: CrewPayload, user: Dict = Depends(get_current_user)):
    try:
        return await create_crew(user["user_id"], data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{crew_id}")
async def api_update_crew(crew_id: int, data: CrewPayload, user: Dict = Depends(get_current_user)):
    try:
        crew = await update_crew(crew_id, user["user_id"], data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not crew:
        raise HTTPException(status_code=404, detail="Crew 不存在")
    return crew


@router.delete("/{crew_id}")
async def api_delete_crew(crew_id: int, user: Dict = Depends(get_current_user)):
    try:
        deleted = await delete_crew(crew_id, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=404, detail="Crew 不存在")
    return {"success": True}
