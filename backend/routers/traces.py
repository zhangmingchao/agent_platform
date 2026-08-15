from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import get_current_user
from ..services.trace_service import get_trace, list_traces

router = APIRouter(prefix="/api/traces", tags=["Traces"])


@router.get("")
async def api_list_traces(
    limit: int = Query(100, ge=1, le=500),
    user: Dict = Depends(get_current_user),
):
    return await list_traces(user["user_id"], limit)


@router.get("/{trace_id}")
async def api_get_trace(trace_id: int, user: Dict = Depends(get_current_user)):
    trace = await get_trace(trace_id, user["user_id"])
    if not trace:
        raise HTTPException(status_code=404, detail="Trace 不存在")
    return trace
