from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..services.flow_service import create_flow, delete_flow, get_flow, list_flows, update_flow

router = APIRouter(prefix="/api/flows", tags=["Flows"])


class FlowNodePayload(BaseModel):
    node_key: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    node_type: Literal["crew", "condition", "approval", "transform", "end"] = "crew"
    crew_id: Optional[int] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    position_x: int = 0
    position_y: int = 0


class FlowEdgePayload(BaseModel):
    source_key: str
    target_key: str
    condition_type: Literal["always", "contains", "equals", "not_contains"] = "always"
    condition_value: str = ""
    priority: int = 0


class FlowPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    state_schema: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    nodes: List[FlowNodePayload] = Field(default_factory=list)
    edges: List[FlowEdgePayload] = Field(default_factory=list)


@router.get("")
async def api_list_flows(request: Request):
    return await list_flows(get_current_user(request)["user_id"])


@router.get("/{flow_id}")
async def api_get_flow(flow_id: int, request: Request):
    flow = await get_flow(flow_id, get_current_user(request)["user_id"])
    if not flow:
        raise HTTPException(status_code=404, detail="Flow 不存在")
    return flow


@router.post("")
async def api_create_flow(data: FlowPayload, request: Request):
    try:
        return await create_flow(get_current_user(request)["user_id"], data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{flow_id}")
async def api_update_flow(flow_id: int, data: FlowPayload, request: Request):
    try:
        flow = await update_flow(flow_id, get_current_user(request)["user_id"], data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not flow:
        raise HTTPException(status_code=404, detail="Flow 不存在")
    return flow


@router.delete("/{flow_id}")
async def api_delete_flow(flow_id: int, request: Request):
    if not await delete_flow(flow_id, get_current_user(request)["user_id"]):
        raise HTTPException(status_code=404, detail="Flow 不存在")
    return {"success": True}
