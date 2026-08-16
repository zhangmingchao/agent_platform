"""Persistence helpers for Flow/Crew/Task/Agent/Tool execution traces."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database import execute, fetch_all, fetch_one


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")


def _serialize(value: Any) -> str:
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)


async def create_trace(
    user_id: int,
    target_type: str,
    target_id: int,
    target_name: str,
    session_id: int,
    user_message: str,
    model: str = "",
) -> int:
    return await execute(
        "INSERT INTO trace_runs (user_id, target_type, target_id, target_name, session_id, "
        "status, model, input_text, started_at, created_at) "
        "VALUES (%s, %s, %s, %s, %s, 'running', %s, %s, %s, %s)",
        (user_id, target_type, target_id, target_name, session_id, model, user_message, _now(), _now()),
    )


async def finish_trace(
    trace_id: int,
    status: str,
    output_text: str = "",
    error_text: str = "",
    duration_ms: int = 0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
) -> None:
    await execute(
        "UPDATE trace_runs SET status=%s, output_text=%s, error_text=%s, ended_at=%s, "
        "duration_ms=%s, prompt_tokens=%s, completion_tokens=%s, total_tokens=%s WHERE id=%s",
        (status, output_text, error_text, _now(), duration_ms,
         prompt_tokens, completion_tokens, total_tokens, trace_id),
    )


async def create_span(
    trace_id: int,
    span_type: str,
    name: str,
    status: str,
    round_no: Optional[int] = None,
    task_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    input_data: Any = None,
    output_data: Any = None,
    error_text: str = "",
    duration_ms: int = 0,
    started_at: Optional[str] = None,
) -> int:
    started = started_at or _now()
    return await execute(
        "INSERT INTO trace_spans (trace_id, task_id, agent_id, span_type, name, round_no, status, "
        "input_data, output_data, error_text, started_at, ended_at, duration_ms, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            trace_id, task_id, agent_id, span_type, name, round_no, status,
            _serialize(input_data) if input_data is not None else None,
            _serialize(output_data) if output_data is not None else None,
            error_text, started, _now(), duration_ms, _now(),
        ),
    )


async def list_traces(user_id: int, limit: int = 100) -> List[Dict]:
    return await fetch_all(
        "SELECT t.id, t.target_type, t.target_id, t.target_name, t.session_id, t.status, "
        "t.model, t.input_text, t.duration_ms, t.started_at, t.ended_at, t.created_at, "
        "t.prompt_tokens, t.completion_tokens, t.total_tokens, "
        "s.title AS session_title, "
        "(SELECT COUNT(*) FROM trace_spans sp WHERE sp.trace_id=t.id) AS span_count "
        "FROM trace_runs t JOIN chat_sessions s ON s.id=t.session_id "
        "WHERE t.user_id=%s ORDER BY t.id DESC LIMIT %s",
        (user_id, limit),
    )


async def get_trace(trace_id: int, user_id: int) -> Optional[Dict]:
    trace = await fetch_one(
        "SELECT t.*, s.title AS session_title FROM trace_runs t "
        "JOIN chat_sessions s ON s.id=t.session_id WHERE t.id=%s AND t.user_id=%s",
        (trace_id, user_id),
    )
    if not trace:
        return None
    trace["spans"] = await fetch_all(
        "SELECT sp.id, sp.task_id, sp.agent_id, sp.span_type, sp.name, sp.round_no, sp.status, "
        "sp.input_data, sp.output_data, sp.error_text, sp.started_at, sp.ended_at, sp.duration_ms, "
        "a.name AS agent_name, ct.name AS task_name FROM trace_spans sp "
        "LEFT JOIN agents a ON a.id=sp.agent_id LEFT JOIN crew_tasks ct ON ct.id=sp.task_id "
        "WHERE sp.trace_id=%s ORDER BY sp.started_at, sp.id",
        (trace_id,),
    )
    return trace
