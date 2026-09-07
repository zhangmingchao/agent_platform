"""MongoDB 连接与 Trace Span 索引管理。"""

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

from .config import (
    MONGODB_CONNECT_TIMEOUT_MS,
    MONGODB_DATABASE,
    MONGODB_TRACE_RETENTION_DAYS,
    MONGODB_TRACE_SPANS_COLLECTION,
    MONGODB_URL,
)

_client = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=MONGODB_CONNECT_TIMEOUT_MS,
            connectTimeoutMS=MONGODB_CONNECT_TIMEOUT_MS,
            appname="agent-platform",
        )
    return _client


def get_trace_spans_collection() -> Any:
    return get_mongo_client()[MONGODB_DATABASE][MONGODB_TRACE_SPANS_COLLECTION]


async def init_mongo() -> None:
    """验证连接并创建索引；失败直接抛出，阻止应用以缺失 Trace 的状态运行。"""
    client = get_mongo_client()
    await client.admin.command("ping")
    collection = get_trace_spans_collection()
    await collection.create_index(
        [("trace_run_id", ASCENDING), ("started_at", ASCENDING)],
        name="idx_trace_started",
    )
    await collection.create_index(
        [("user_id", ASCENDING), ("started_at", DESCENDING)],
        name="idx_user_started",
    )
    await collection.create_index(
        [("workflow.run_id", ASCENDING)],
        name="idx_workflow_run",
        sparse=True,
    )
    await collection.create_index(
        [("expire_at", ASCENDING)],
        name="idx_expire_at_ttl",
        expireAfterSeconds=0,
    )
    await collection.create_index(
        [("legacy_mysql_id", ASCENDING)],
        name="idx_legacy_mysql_id",
        unique=True,
        sparse=True,
    )


async def close_mongo() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def trace_expire_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=MONGODB_TRACE_RETENTION_DAYS)


async def trace_span_counts(trace_ids: Iterable[int]) -> dict[int, int]:
    ids = list({int(value) for value in trace_ids})
    if not ids:
        return {}
    pipeline = [
        {"$match": {"trace_run_id": {"$in": ids}}},
        {"$group": {"_id": "$trace_run_id", "count": {"$sum": 1}}},
    ]
    return {row["_id"]: row["count"] async for row in get_trace_spans_collection().aggregate(pipeline)}
