"""工作流定义的校验与增删改查服务。"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from ..core.workflow_graph import normalize_workflow_steps, parse_workflow_config
from ..database import execute
from ..repositories.workflow_repository import (
    find_workflow_entity,
    list_workflow_entities,
)
from .agent_service import get_agent


def _now() -> str:
    """返回数据库使用的 UTC 时间文本。"""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def _validate_workflow_agents(
    user_id: int,
    config: Dict[str, Any],
) -> None:
    """校验配置引用的 Agent 均属于当前用户。

    参数：
    - ``user_id``：当前用户 ID；
    - ``config``：已经解析的工作流配置。
    """
    for step in normalize_workflow_steps(config):
        if not await get_agent(step["agent_id"], user_id):
            raise HTTPException(
                status_code=400,
                detail=f"Agent 不存在或无权限: {step['agent_id']}",
            )


async def list_workflows(user_id: int) -> List[Dict[str, Any]]:
    """查询用户工作流，并转换为 HTTP 响应结构。"""
    workflows = await list_workflow_entities(user_id)
    return [workflow.to_dict() for workflow in workflows]


async def get_workflow(
    workflow_id: int,
    user_id: int,
) -> Optional[Dict[str, Any]]:
    """查询单个工作流，并转换为 HTTP 响应结构。"""
    workflow = await find_workflow_entity(workflow_id, user_id)
    return workflow.to_dict() if workflow else None


async def create_workflow(
    user_id: int,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """校验配置并创建工作流定义。"""
    name = str(data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="工作流名称不能为空")
    config = parse_workflow_config(data.get("config") or data.get("config_json") or {})
    normalize_workflow_steps(config)
    await _validate_workflow_agents(user_id, config)
    now = _now()
    workflow_id = await execute(
        "INSERT INTO multi_agent_workflows "
        "(user_id, name, description, mode, config_json, is_active, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (
            user_id,
            name,
            str(data.get("description") or ""),
            str(data.get("mode") or config.get("mode") or "sequential"),
            json.dumps(config, ensure_ascii=False),
            1,
            now,
            now,
        ),
    )
    created = await get_workflow(workflow_id, user_id)
    if created is None:
        raise RuntimeError("工作流创建成功但无法读取")
    return created


async def update_workflow(
    workflow_id: int,
    user_id: int,
    data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """校验并更新工作流定义。"""
    existing = await get_workflow(workflow_id, user_id)
    if not existing:
        return None
    config = parse_workflow_config(
        data.get("config") or data.get("config_json") or existing["config"]
    )
    normalize_workflow_steps(config)
    await _validate_workflow_agents(user_id, config)
    name = str(data.get("name", existing["name"])).strip()
    if not name:
        raise HTTPException(status_code=400, detail="工作流名称不能为空")
    await execute(
        "UPDATE multi_agent_workflows SET name=%s, description=%s, mode=%s, "
        "config_json=%s, is_active=%s, updated_at=%s WHERE id=%s AND user_id=%s",
        (
            name,
            str(data.get("description", existing.get("description") or "")),
            str(data.get("mode", existing.get("mode") or config.get("mode") or "sequential")),
            json.dumps(config, ensure_ascii=False),
            int(data.get("is_active", existing.get("is_active", 1))),
            _now(),
            workflow_id,
            user_id,
        ),
    )
    return await get_workflow(workflow_id, user_id)


async def delete_workflow(workflow_id: int, user_id: int) -> bool:
    """删除属于当前用户的工作流定义。"""
    if not await find_workflow_entity(workflow_id, user_id):
        return False
    await execute(
        "DELETE FROM multi_agent_workflows WHERE id=%s AND user_id=%s",
        (workflow_id, user_id),
    )
    return True
