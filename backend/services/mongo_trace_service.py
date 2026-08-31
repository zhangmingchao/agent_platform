"""MongoDB Trace Span 持久化服务。Trace Run 汇总仍保存在 MySQL。"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from ..mongo_client import get_trace_spans_collection, trace_expire_at


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def create_trace_span(
    *,
    trace_run_id: int,
    user_id: int,
    span_type: str,
    name: str,
    input_data: Any,
    session_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    workflow_run_id: Optional[int] = None,
    workflow_step_id: Optional[int] = None,
    event_run_id: str = "",
    round_no: Optional[int] = None,
) -> str:
    now = _utc_now()
    document = {
        "trace_run_id": trace_run_id,
        "user_id": user_id,
        "session_id": session_id,
        "agent_id": agent_id,
        "span_type": span_type,
        "name": name,
        "event_run_id": event_run_id,
        "round_no": round_no,
        "input_data": input_data,
        "output_data": None,
        "error_text": None,
        "tokens_used": 0,
        "duration_ms": 0,
        "status": "running",
        "workflow": {
            "run_id": workflow_run_id,
            "step_id": workflow_step_id,
        } if workflow_run_id or workflow_step_id else None,
        "started_at": now,
        "created_at": now,
        "finished_at": None,
        "expire_at": trace_expire_at(),
    }
    result = await get_trace_spans_collection().insert_one(document)
    return str(result.inserted_id)


async def finish_trace_span(
    span_id: str,
    *,
    output_data: Any = None,
    tokens_used: int = 0,
    duration_ms: int = 0,
    status: str = "success",
    error_text: Optional[str] = None,
) -> None:
    await get_trace_spans_collection().update_one(
        {"_id": ObjectId(span_id)},
        {"$set": {
            "output_data": output_data,
            "tokens_used": tokens_used,
            "duration_ms": duration_ms,
            "status": status,
            "error_text": error_text,
            "finished_at": _utc_now(),
        }},
    )


async def get_trace_spans(trace_run_id: int) -> List[Dict]:
    cursor = get_trace_spans_collection().find(
        {"trace_run_id": trace_run_id},
        {"event_run_id": 0, "expire_at": 0},
    ).sort([("started_at", 1), ("_id", 1)])
    spans = []
    async for document in cursor:
        document["id"] = str(document.pop("_id"))
        workflow = document.pop("workflow", None) or {}
        document["workflow_run_id"] = workflow.get("run_id")
        document["workflow_step_id"] = workflow.get("step_id")
        spans.append(document)
    return spans
