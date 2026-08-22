"""MCP 配置业务操作。"""
import logging
from datetime import datetime
from typing import List, Dict, Optional

from ..database import execute, fetch_all, fetch_one

log = logging.getLogger("agent-platform")


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_mcp_configs(user_id: int) -> List[Dict]:
    return await fetch_all(
        "SELECT id, name, base_url, endpoint, description, created_at "
        "FROM mcp_configs WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,)
    )


async def get_mcp_config(config_id: int, user_id: int) -> Optional[Dict]:
    return await fetch_one(
        "SELECT * FROM mcp_configs WHERE id=%s AND user_id=%s",
        (config_id, user_id)
    )


async def create_mcp_config(user_id: int, data: Dict) -> Dict:
    now = _now()
    config_id = await execute(
        "INSERT INTO mcp_configs (user_id, name, base_url, endpoint, description, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            user_id,
            data.get("name", "New MCP"),
            data.get("base_url", "http://localhost:18888"),
            data.get("endpoint", "/mcp"),
            data.get("description", ""),
            now,
        )
    )
    return {
        "id": config_id,
        "name": data.get("name", "New MCP"),
        "base_url": data.get("base_url", "http://localhost:18888"),
        "endpoint": data.get("endpoint", "/mcp"),
        "description": data.get("description", ""),
        "created_at": now,
    }


async def update_mcp_config(config_id: int, user_id: int, data: Dict) -> Optional[Dict]:
    existing = await fetch_one(
        "SELECT id FROM mcp_configs WHERE id=%s AND user_id=%s",
        (config_id, user_id)
    )
    if not existing:
        return None

    await execute(
        "UPDATE mcp_configs SET name=%s, base_url=%s, endpoint=%s, description=%s WHERE id=%s",
        (
            data.get("name", "New MCP"),
            data.get("base_url", "http://localhost:18888"),
            data.get("endpoint", "/mcp"),
            data.get("description", ""),
            config_id,
        )
    )
    return await get_mcp_config(config_id, user_id)


async def delete_mcp_config(config_id: int, user_id: int) -> bool:
    result = await execute(
        "DELETE FROM mcp_configs WHERE id=%s AND user_id=%s",
        (config_id, user_id)
    )
    return result > 0


async def get_agent_mcps(agent_id: int) -> List[Dict]:
    return await fetch_all(
        "SELECT m.* FROM mcp_configs m "
        "JOIN agent_mcps ao ON m.id=ao.mcp_id "
        "WHERE ao.agent_id=%s",
        (agent_id,)
    )
