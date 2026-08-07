"""Skill business operations."""
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

from database import fetch_all, fetch_one, execute
from config import SKILLS_DIR

log = logging.getLogger("agent-platform")


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_skills(user_id: int) -> List[Dict]:
    return await fetch_all(
        "SELECT id, name, description, created_at FROM skills WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,)
    )


async def get_skill(skill_id: int, user_id: int) -> Optional[Dict]:
    return await fetch_one(
        "SELECT * FROM skills WHERE id=%s AND user_id=%s",
        (skill_id, user_id)
    )


async def create_skill(user_id: int, name: str, description: str, content: str) -> Dict:
    now = _now()
    skill_id = await execute(
        "INSERT INTO skills (user_id, name, description, content, created_at) VALUES (%s, %s, %s, %s, %s)",
        (user_id, name, description, content, now)
    )
    return {
        "id": skill_id,
        "name": name,
        "description": description,
        "content": content,
        "created_at": now,
    }


async def delete_skill(skill_id: int, user_id: int) -> bool:
    result = await execute(
        "DELETE FROM skills WHERE id=%s AND user_id=%s",
        (skill_id, user_id)
    )
    return result > 0


async def get_agent_skills(agent_id: int) -> List[Dict]:
    return await fetch_all(
        "SELECT s.* FROM skills s "
        "JOIN agent_skills ao ON s.id=ao.skill_id "
        "WHERE ao.agent_id=%s",
        (agent_id,)
    )
