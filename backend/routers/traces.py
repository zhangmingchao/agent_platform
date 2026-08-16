"""Traces router — local MySQL-based trace querying."""
from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..database import fetch_all, fetch_one

router = APIRouter(prefix="/api/traces", tags=["Traces"])


@router.get("")
async def api_list_traces(user: dict = Depends(get_current_user), limit: int = 200):
    traces = await fetch_all(
        "SELECT t.id, t.status, t.input_text, t.output_text, t.model, "
        "t.total_tokens, t.total_duration_ms as duration_ms, t.started_at, "
        "a.name as agent_name, s.title as session_title, "
        "(SELECT COUNT(*) FROM trace_spans WHERE run_id=t.id) as span_count "
        "FROM trace_runs t "
        "LEFT JOIN agents a ON t.agent_id=a.id "
        "LEFT JOIN chat_sessions s ON t.session_id=s.id "
        "WHERE t.user_id=%s "
        "ORDER BY t.started_at DESC "
        "LIMIT %s",
        (user["user_id"], limit)
    )
    return traces


@router.get("/{trace_id}")
async def api_get_trace(trace_id: int, user: dict = Depends(get_current_user)):
    trace = await fetch_one(
        "SELECT t.id, t.status, t.input_text, t.output_text, t.error_text, t.model, "
        "t.total_tokens, t.total_duration_ms as duration_ms, t.started_at, t.created_at, "
        "a.name as agent_name, s.title as session_title "
        "FROM trace_runs t "
        "LEFT JOIN agents a ON t.agent_id=a.id "
        "LEFT JOIN chat_sessions s ON t.session_id=s.id "
        "WHERE t.id=%s AND t.user_id=%s",
        (trace_id, user["user_id"])
    )
    if not trace:
        raise HTTPException(status_code=404, detail="Trace 不存在")

    spans = await fetch_all(
        "SELECT id, run_id, span_type, name, round_no, input_data, output_data, "
        "error_text, tokens_used, duration_ms, status, started_at, created_at "
        "FROM trace_spans WHERE run_id=%s ORDER BY created_at",
        (trace_id,)
    )

    trace["spans"] = spans
    return trace
