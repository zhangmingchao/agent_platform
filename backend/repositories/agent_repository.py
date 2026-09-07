"""Agent 实体的数据访问 Repository。"""

from typing import Any, Dict, List, Optional

from ..database import fetch_all, fetch_one
from ..models.agent import Agent


async def find_agent_by_id(agent_id: int, user_id: int) -> Optional[Agent]:
    """按用户和 Agent ID 查询实体，不存在时返回 ``None``。"""
    row: Optional[Dict[str, Any]] = await fetch_one(
        "SELECT * FROM agents WHERE id=%s AND user_id=%s",
        (agent_id, user_id),
    )
    if row is None:
        return None

    skills: List[Dict[str, Any]] = await fetch_all(
        "SELECT s.id, s.name, s.description FROM skills s "
        "JOIN agent_skills ao ON s.id=ao.skill_id WHERE ao.agent_id=%s",
        (agent_id,),
    )
    mcps: List[Dict[str, Any]] = await fetch_all(
        "SELECT m.id, m.name, m.base_url, m.endpoint, m.description FROM mcp_configs m "
        "JOIN agent_mcps ao ON m.id=ao.mcp_id WHERE ao.agent_id=%s",
        (agent_id,),
    )
    return Agent.from_mapping(row, skills=skills, mcps=mcps)


async def find_agents_by_user(user_id: int) -> List[Agent]:
    """查询用户的 Agent 列表并转换为实体。列表场景不额外加载关联详情。"""
    rows: List[Dict[str, Any]] = await fetch_all(
        "SELECT id, user_id, name, description, system_prompt, prompt_variables, output_schema, "
        "model, model_config_id, temperature, iteration_count, created_at, updated_at "
        "FROM agents WHERE user_id=%s ORDER BY updated_at DESC",
        (user_id,),
    )
    return [Agent.from_mapping(row) for row in rows]
