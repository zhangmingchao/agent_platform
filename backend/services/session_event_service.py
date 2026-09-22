"""Session append-only 事件日志服务。"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database import execute, fetch_all
from ..models.session_event import SessionEventRecord

log = logging.getLogger(__name__)


def _now() -> str:
    """返回数据库使用的 UTC 时间字符串。"""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")


def _payload_json(payload: Dict[str, Any]) -> str:
    """将事件 payload 转成 JSON 字符串。"""
    return json.dumps(payload, ensure_ascii=False, default=str)


async def append_session_event(event: SessionEventRecord) -> Optional[int]:
    """追加一条 Session 事件。

    Args:
        event: 已构造好的不可变事件实体。

    Returns:
        新增事件 ID；写入失败时返回 ``None``，避免影响 Agent 主执行流程。
    """
    try:
        return await execute(
            "INSERT INTO session_events "
            "(user_id, session_id, trace_run_id, agent_id, workflow_run_id, workflow_step_id, "
            "event_source, event_type, turn_id, step_id, run_id, phase, name, status, payload_json, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                event.user_id,
                event.session_id,
                event.trace_run_id,
                event.agent_id,
                event.workflow_run_id,
                event.workflow_step_id,
                event.event_source.value,
                event.event_type.value,
                event.turn_id,
                event.step_id,
                event.run_id,
                event.phase,
                event.name,
                event.status,
                _payload_json(event.payload),
                _now(),
            ),
        )
    except Exception as exc:
        log.warning("[SessionEvent] append failed: %s", exc)
        return None


async def list_session_events(
    user_id: int,
    session_id: Optional[int] = None,
    trace_run_id: Optional[int] = None,
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """查询当前用户的 Session 事件。

    Args:
        user_id: 当前登录用户 ID。
        session_id: 可选的会话 ID 过滤条件。
        trace_run_id: 可选的 Trace Run ID 过滤条件。
        limit: 最大返回条数。

    Returns:
        按追加顺序返回的事件列表。
    """
    clauses = ["user_id=%s"]
    params: List[Any] = [user_id]
    if session_id is not None:
        clauses.append("session_id=%s")
        params.append(session_id)
    if trace_run_id is not None:
        clauses.append("trace_run_id=%s")
        params.append(trace_run_id)
    params.append(max(1, min(limit, 2000)))
    rows = await fetch_all(
        "SELECT id, user_id, session_id, trace_run_id, agent_id, workflow_run_id, workflow_step_id, "
        "event_source, event_type, turn_id, step_id, run_id, phase, name, status, payload_json, created_at "
        "FROM session_events WHERE "
        + " AND ".join(clauses)
        + " ORDER BY id ASC LIMIT %s",
        tuple(params),
    )
    for row in rows:
        try:
            row["payload"] = json.loads(row.pop("payload_json") or "{}")
        except json.JSONDecodeError:
            row["payload"] = {}
    return rows
