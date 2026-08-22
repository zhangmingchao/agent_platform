"""聊天链路追踪和 span 的持久化辅助函数。"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database import execute, fetch_all, fetch_one


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")


def _serialize(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


async def create_trace(
    user_id: int,
    agent_id: int,
    session_id: int,
    user_message: str,
    model: str,
) -> int:
    return await execute(
        "INSERT INTO trace_runs "
        "(user_id, agent_id, session_id, status, model, input_text, started_at, created_at) "
        "VALUES (%s, %s, %s, 'running', %s, %s, %s, %s)",
        (user_id, agent_id, session_id, model, user_message, _now(), _now()),
    )


async def finish_trace(
    trace_id: int,
    status: str,
    output_text: str = "",
    error_text: str = "",
    duration_ms: int = 0,
) -> None:
    await execute(
        "UPDATE trace_runs SET status=%s, output_text=%s, error_text=%s, "
        "ended_at=%s, duration_ms=%s WHERE id=%s",
        (status, output_text, error_text, _now(), duration_ms, trace_id),
    )


async def create_span(
    trace_id: int,
    span_type: str,
    name: str,
    status: str,
    round_no: Optional[int] = None,
    input_data: Any = None,
    output_data: Any = None,
    error_text: str = "",
    duration_ms: int = 0,
    started_at: Optional[str] = None,
) -> int:
    started = started_at or _now()
    return await execute(
        "INSERT INTO trace_spans "
        "(trace_id, span_type, name, round_no, status, input_data, output_data, "
        "error_text, started_at, ended_at, duration_ms, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            trace_id,
            span_type,
            name,
            round_no,
            status,
            _serialize(input_data) if input_data is not None else None,
            _serialize(output_data) if output_data is not None else None,
            error_text,
            started,
            _now(),
            duration_ms,
            _now(),
        ),
    )


async def list_traces(user_id: int, limit: int = 100) -> List[Dict]:
    return await fetch_all(
        "SELECT t.id, t.agent_id, t.session_id, t.status, t.model, t.input_text, "
        "t.duration_ms, t.started_at, t.ended_at, t.created_at, "
        "a.name AS agent_name, s.title AS session_title, "
        "(SELECT COUNT(*) FROM trace_spans sp WHERE sp.trace_id=t.id) AS span_count "
        "FROM trace_runs t "
        "JOIN agents a ON a.id=t.agent_id "
        "JOIN chat_sessions s ON s.id=t.session_id "
        "WHERE t.user_id=%s ORDER BY t.id DESC LIMIT %s",
        (user_id, limit),
    )


async def get_trace(trace_id: int, user_id: int) -> Optional[Dict]:
    trace = await fetch_one(
        "SELECT t.*, a.name AS agent_name, s.title AS session_title "
        "FROM trace_runs t "
        "JOIN agents a ON a.id=t.agent_id "
        "JOIN chat_sessions s ON s.id=t.session_id "
        "WHERE t.id=%s AND t.user_id=%s",
        (trace_id, user_id),
    )
    if not trace:
        return None
    trace["spans"] = await fetch_all(
        "SELECT id, span_type, name, round_no, status, input_data, output_data, "
        "error_text, started_at, ended_at, duration_ms "
        "FROM trace_spans WHERE trace_id=%s ORDER BY id ASC",
        (trace_id,),
    )
    return trace
