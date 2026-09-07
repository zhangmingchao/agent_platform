"""链路追踪路由：MySQL 查询 Run 汇总，MongoDB 查询 Span 明细。"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..database import fetch_all, fetch_one
from ..mongo_client import trace_span_counts
from ..services.mongo_trace_service import get_trace_spans

router = APIRouter(prefix="/api/traces", tags=["Traces"])


@router.get("")
async def api_list_traces(user: dict = Depends(get_current_user), limit: int = 200) -> List[Dict[str, Any]]:
    traces = await fetch_all(
        "SELECT t.id, t.status, t.input_text, t.output_text, t.model, "
        "t.workflow_run_id, t.workflow_step_id, wr.workflow_id, ws.step_order, ws.role_name, "
        "t.total_tokens, t.total_duration_ms as duration_ms, t.started_at, "
        "a.name as agent_name, s.title as session_title, w.name as workflow_name "
        "FROM trace_runs t "
        "LEFT JOIN agents a ON t.agent_id=a.id "
        "LEFT JOIN chat_sessions s ON t.session_id=s.id "
        "LEFT JOIN multi_agent_runs wr ON t.workflow_run_id=wr.id "
        "LEFT JOIN multi_agent_run_steps ws ON t.workflow_step_id=ws.id "
        "LEFT JOIN multi_agent_workflows w ON wr.workflow_id=w.id "
        "WHERE t.user_id=%s "
        "ORDER BY t.started_at DESC "
        "LIMIT %s",
        (user["user_id"], limit)
    )
    counts = await trace_span_counts(trace["id"] for trace in traces)
    for trace in traces:
        trace["span_count"] = counts.get(trace["id"], 0)
    return traces


@router.get("/{trace_id}")
async def api_get_trace(trace_id: int, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    trace = await fetch_one(
        "SELECT t.id, t.status, t.input_text, t.output_text, t.error_text, t.model, "
        "t.workflow_run_id, t.workflow_step_id, wr.workflow_id, ws.step_order, ws.role_name, "
        "t.total_tokens, t.total_duration_ms as duration_ms, t.started_at, t.created_at, "
        "a.name as agent_name, s.title as session_title, w.name as workflow_name "
        "FROM trace_runs t "
        "LEFT JOIN agents a ON t.agent_id=a.id "
        "LEFT JOIN chat_sessions s ON t.session_id=s.id "
        "LEFT JOIN multi_agent_runs wr ON t.workflow_run_id=wr.id "
        "LEFT JOIN multi_agent_run_steps ws ON t.workflow_step_id=ws.id "
        "LEFT JOIN multi_agent_workflows w ON wr.workflow_id=w.id "
        "WHERE t.id=%s AND t.user_id=%s",
        (trace_id, user["user_id"])
    )
    if not trace:
        raise HTTPException(status_code=404, detail="Trace 不存在")

    spans = await get_trace_spans(trace_id)

    trace["spans"] = spans
    return trace
