"""将历史 MySQL trace_spans 幂等迁移到 MongoDB。

运行：
    python -m backend.scripts.migrate_trace_spans_to_mongodb
"""

import asyncio
from datetime import timezone

from backend.database import close_pool, fetch_all
from backend.mongo_client import close_mongo, get_trace_spans_collection, init_mongo, trace_expire_at


def _as_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def migrate() -> tuple[int, int]:
    await init_mongo()
    rows = await fetch_all(
        "SELECT sp.id, sp.run_id, sp.span_type, sp.name, sp.round_no, sp.input_data, "
        "sp.output_data, sp.error_text, sp.tokens_used, sp.duration_ms, sp.status, "
        "sp.started_at, sp.created_at, tr.user_id, tr.session_id, tr.agent_id, "
        "tr.workflow_run_id, tr.workflow_step_id "
        "FROM trace_spans sp JOIN trace_runs tr ON tr.id=sp.run_id ORDER BY sp.id"
    )
    collection = get_trace_spans_collection()
    migrated = 0
    for row in rows:
        document = {
            "legacy_mysql_id": row["id"],
            "trace_run_id": row["run_id"],
            "user_id": row["user_id"],
            "session_id": row.get("session_id"),
            "agent_id": row.get("agent_id"),
            "span_type": row["span_type"],
            "name": row.get("name"),
            "event_run_id": "",
            "round_no": row.get("round_no"),
            "input_data": row.get("input_data"),
            "output_data": row.get("output_data"),
            "error_text": row.get("error_text"),
            "tokens_used": row.get("tokens_used") or 0,
            "duration_ms": row.get("duration_ms") or 0,
            "status": row.get("status") or "success",
            "workflow": {
                "run_id": row.get("workflow_run_id"),
                "step_id": row.get("workflow_step_id"),
            } if row.get("workflow_run_id") or row.get("workflow_step_id") else None,
            "started_at": _as_utc(row.get("started_at")),
            "created_at": _as_utc(row.get("created_at")),
            "finished_at": None,
            "expire_at": trace_expire_at(),
        }
        result = await collection.replace_one(
            {"legacy_mysql_id": row["id"]}, document, upsert=True,
        )
        if result.upserted_id is not None or result.modified_count:
            migrated += 1
    return len(rows), migrated


async def main():
    try:
        total, migrated = await migrate()
        print(f"MySQL Span 数量: {total}，本次写入 MongoDB: {migrated}")
    finally:
        await close_mongo()
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
