"""Agent 业务操作。"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..database import execute, execute_many, fetch_one
from ..core.agent_output import parse_json_object, validate_output_schema
from ..models.agent import Agent
from ..repositories.agent_repository import find_agent_by_id, find_agents_by_user
from fastapi import HTTPException

log = logging.getLogger(__name__)


def _validated_agent_options(data: Dict) -> Tuple[Dict, Any]:
    try:
        return (
            parse_json_object(data.get("prompt_variables"), "prompt_variables") or {},
            validate_output_schema(data.get("output_schema")),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def list_agents(user_id: int) -> List[Agent]:
    """返回当前用户的 Agent 实体列表。"""
    return await find_agents_by_user(user_id)


async def get_agent(agent_id: int, user_id: int) -> Optional[Agent]:
    """通过 Repository 返回 Agent 实体，不向业务层暴露数据库字典。"""
    return await find_agent_by_id(agent_id, user_id)


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def create_agent(user_id: int, data: Dict) -> Agent:
    prompt_variables, output_schema = _validated_agent_options(data)
    now = _now()
    agent_id = await execute(
        "INSERT INTO agents (user_id, name, description, system_prompt, prompt_variables, output_schema, model, model_config_id, "
        "temperature, iteration_count, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            user_id,
            data.get("name", "新Agent"),
            data.get("description", ""),
            data.get("system_prompt", ""),
            json.dumps(prompt_variables, ensure_ascii=False),
            json.dumps(output_schema, ensure_ascii=False) if output_schema else None,
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

    agent = await get_agent(agent_id, user_id)
    if agent is None:
        raise RuntimeError("Agent 创建成功后无法重新加载")
    return agent


async def update_agent(agent_id: int, user_id: int, data: Dict) -> Optional[Agent]:
    existing = await fetch_one(
        "SELECT id FROM agents WHERE id=%s AND user_id=%s",
        (agent_id, user_id)
    )
    if not existing:
        return None

    prompt_variables, output_schema = _validated_agent_options(data)

    now = _now()
    await execute(
        "UPDATE agents SET name=%s, description=%s, system_prompt=%s, prompt_variables=%s, output_schema=%s, model=%s, "
        "model_config_id=%s, temperature=%s, iteration_count=%s, updated_at=%s "
        "WHERE id=%s",
        (
            data.get("name", "新Agent"),
            data.get("description", ""),
            data.get("system_prompt", ""),
            json.dumps(prompt_variables, ensure_ascii=False),
            json.dumps(output_schema, ensure_ascii=False) if output_schema else None,
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
