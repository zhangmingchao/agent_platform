"""Agent business operations."""
import logging
from datetime import datetime
from typing import List, Dict, Optional

from ..database import execute, execute_many, fetch_all, fetch_one

log = logging.getLogger("agent-platform")


async def list_agents(user_id: int) -> List[Dict]:
    return await fetch_all(
        "SELECT id, name, description, system_prompt, model, model_config_id, "
        "temperature, iteration_count, created_at, updated_at "
        "FROM agents WHERE user_id=%s ORDER BY updated_at DESC",
        (user_id,)
    )


async def get_agent(agent_id: int, user_id: int) -> Optional[Dict]:
    agent = await fetch_one(
        "SELECT * FROM agents WHERE id=%s AND user_id=%s",
        (agent_id, user_id)
    )
    if not agent:
        return None

    agent["skills"] = await fetch_all(
        "SELECT s.id, s.name, s.description FROM skills s "
        "JOIN agent_skills ao ON s.id=ao.skill_id WHERE ao.agent_id=%s",
        (agent_id,)
    )
    agent["mcps"] = await fetch_all(
        "SELECT m.id, m.name, m.base_url, m.endpoint, m.description FROM mcp_configs m "
        "JOIN agent_mcps ao ON m.id=ao.mcp_id WHERE ao.agent_id=%s",
        (agent_id,)
    )
    return agent


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def create_agent(user_id: int, data: Dict) -> Dict:
    now = _now()
    agent_id = await execute(
        "INSERT INTO agents (user_id, name, description, system_prompt, model, model_config_id, "
        "temperature, iteration_count, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            user_id,
            data.get("name", "新Agent"),
            data.get("description", ""),
            data.get("system_prompt", ""),
            data.get("model", "deepseek-chat"),
            data.get("model_config_id"),
            data.get("temperature", 0.7),
            data.get("iteration_count", 6),
            now,
            now,
        )
    )

    skill_ids = data.get("skill_ids", [])
    if skill_ids:
        await execute_many(
            "INSERT IGNORE INTO agent_skills (agent_id, skill_id) VALUES (%s, %s)",
            [(agent_id, sid) for sid in skill_ids]
        )

    mcp_ids = data.get("mcp_ids", [])
    if mcp_ids:
        await execute_many(
            "INSERT IGNORE INTO agent_mcps (agent_id, mcp_id) VALUES (%s, %s)",
            [(agent_id, mid) for mid in mcp_ids]
        )

    return await get_agent(agent_id, user_id)


async def update_agent(agent_id: int, user_id: int, data: Dict) -> Optional[Dict]:
    existing = await fetch_one(
        "SELECT id FROM agents WHERE id=%s AND user_id=%s",
        (agent_id, user_id)
    )
    if not existing:
        return None

    now = _now()
    await execute(
        "UPDATE agents SET name=%s, description=%s, system_prompt=%s, model=%s, "
        "model_config_id=%s, temperature=%s, iteration_count=%s, updated_at=%s "
        "WHERE id=%s",
        (
            data.get("name", "新Agent"),
            data.get("description", ""),
            data.get("system_prompt", ""),
            data.get("model", "deepseek-chat"),
            data.get("model_config_id"),
            data.get("temperature", 0.7),
            data.get("iteration_count", 6),
            now,
            agent_id,
        )
    )

    if "skill_ids" in data:
        await execute("DELETE FROM agent_skills WHERE agent_id=%s", (agent_id,))
        skill_ids = data["skill_ids"]
        if skill_ids:
            await execute_many(
                "INSERT INTO agent_skills (agent_id, skill_id) VALUES (%s, %s)",
                [(agent_id, sid) for sid in skill_ids]
            )

    if "mcp_ids" in data:
        await execute("DELETE FROM agent_mcps WHERE agent_id=%s", (agent_id,))
        mcp_ids = data["mcp_ids"]
        if mcp_ids:
            await execute_many(
                "INSERT INTO agent_mcps (agent_id, mcp_id) VALUES (%s, %s)",
                [(agent_id, mid) for mid in mcp_ids]
            )

    return await get_agent(agent_id, user_id)


async def delete_agent(agent_id: int, user_id: int) -> bool:
    result = await execute(
        "DELETE FROM agents WHERE id=%s AND user_id=%s",
        (agent_id, user_id)
    )
    return result > 0
