"""Reusable CrewAI Agent definitions and capability assignments."""
from datetime import datetime
from typing import Dict, List, Optional

from ..database import execute, execute_many, fetch_all, fetch_one


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_agents(user_id: int) -> List[Dict]:
    return await fetch_all(
        "SELECT id, name, description, role, goal, model, temperature, iteration_count, "
        "allow_delegation, reasoning, planning, memory, enabled, created_at, updated_at "
        "FROM agents WHERE user_id=%s ORDER BY updated_at DESC",
        (user_id,),
    )


async def get_agent(agent_id: int, user_id: int) -> Optional[Dict]:
    agent = await fetch_one("SELECT * FROM agents WHERE id=%s AND user_id=%s", (agent_id, user_id))
    if not agent:
        return None
    agent["skills"] = await fetch_all(
        "SELECT s.* FROM skills s JOIN agent_skills x ON s.id=x.skill_id "
        "WHERE x.agent_id=%s ORDER BY s.name",
        (agent_id,),
    )
    agent["mcps"] = await fetch_all(
        "SELECT m.* FROM mcp_configs m JOIN agent_mcps x ON m.id=x.mcp_id "
        "WHERE x.agent_id=%s ORDER BY m.name",
        (agent_id,),
    )
    return agent


async def _validate_capabilities(user_id: int, data: Dict) -> None:
    for field, table in (("skill_ids", "skills"), ("mcp_ids", "mcp_configs")):
        ids = list(dict.fromkeys(data.get(field, [])))
        if not ids:
            continue
        placeholders = ",".join(["%s"] * len(ids))
        rows = await fetch_all(
            f"SELECT id FROM {table} WHERE user_id=%s AND id IN ({placeholders})",
            (user_id, *ids),
        )
        if {row["id"] for row in rows} != set(ids):
            raise ValueError(f"{field} 包含不存在或无权访问的数据")


async def _replace_capabilities(agent_id: int, data: Dict) -> None:
    await execute("DELETE FROM agent_skills WHERE agent_id=%s", (agent_id,))
    await execute("DELETE FROM agent_mcps WHERE agent_id=%s", (agent_id,))
    if data.get("skill_ids"):
        await execute_many(
            "INSERT INTO agent_skills (agent_id, skill_id) VALUES (%s, %s)",
            [(agent_id, item_id) for item_id in data["skill_ids"]],
        )
    if data.get("mcp_ids"):
        await execute_many(
            "INSERT INTO agent_mcps (agent_id, mcp_id) VALUES (%s, %s)",
            [(agent_id, item_id) for item_id in data["mcp_ids"]],
        )


def _agent_values(data: Dict) -> tuple:
    name = data.get("name") or "新 Agent"
    return (
        name,
        data.get("description", ""),
        data.get("role") or name,
        data.get("goal", ""),
        data.get("backstory", ""),
        data.get("system_prompt", ""),
        data.get("model", "deepseek-chat"),
        data.get("temperature", 0.7),
        data.get("iteration_count", 6),
        bool(data.get("allow_delegation", False)),
        bool(data.get("reasoning", False)),
        bool(data.get("planning", False)),
        bool(data.get("memory", False)),
        bool(data.get("enabled", True)),
    )


async def create_agent(user_id: int, data: Dict) -> Dict:
    await _validate_capabilities(user_id, data)
    now = _now()
    agent_id = await execute(
        "INSERT INTO agents (user_id, name, description, role, goal, backstory, system_prompt, "
        "model, temperature, iteration_count, allow_delegation, reasoning, planning, memory, "
        "enabled, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
        "%s, %s, %s, %s, %s, %s, %s)",
        (user_id, *_agent_values(data), now, now),
    )
    await _replace_capabilities(agent_id, data)
    return await get_agent(agent_id, user_id)


async def update_agent(agent_id: int, user_id: int, data: Dict) -> Optional[Dict]:
    if not await fetch_one("SELECT id FROM agents WHERE id=%s AND user_id=%s", (agent_id, user_id)):
        return None
    await _validate_capabilities(user_id, data)
    await execute(
        "UPDATE agents SET name=%s, description=%s, role=%s, goal=%s, backstory=%s, "
        "system_prompt=%s, model=%s, temperature=%s, iteration_count=%s, allow_delegation=%s, "
        "reasoning=%s, planning=%s, memory=%s, enabled=%s, updated_at=%s WHERE id=%s",
        (*_agent_values(data), _now(), agent_id),
    )
    await _replace_capabilities(agent_id, data)
    return await get_agent(agent_id, user_id)


async def delete_agent(agent_id: int, user_id: int) -> bool:
    existing = await fetch_one("SELECT id FROM agents WHERE id=%s AND user_id=%s", (agent_id, user_id))
    if not existing:
        return False
    membership = await fetch_one(
        "SELECT c.name FROM crews c JOIN crew_agents ca ON ca.crew_id=c.id "
        "WHERE ca.agent_id=%s AND c.user_id=%s LIMIT 1",
        (agent_id, user_id),
    )
    if membership:
        raise ValueError(f"Agent 正在被 Crew“{membership['name']}”使用，请先从 Crew 中移除")
    await execute("DELETE FROM agents WHERE id=%s AND user_id=%s", (agent_id, user_id))
    return True
