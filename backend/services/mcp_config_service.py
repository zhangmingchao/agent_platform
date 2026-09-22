"""MCP 配置业务操作。"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database import execute, fetch_all, fetch_one
from ..models.mcp import McpConfig, McpConfigInput

log = logging.getLogger(__name__)


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_mcp_configs(user_id: int) -> List[McpConfig]:
    """查询当前用户的全部 MCP 配置实体。

    Args:
        user_id: 当前登录用户 ID。

    Returns:
        按创建时间倒序排列的 MCP 配置实体。
    """
    rows: List[Dict[str, Any]] = await fetch_all(
        "SELECT id, user_id, name, base_url, endpoint, description, timeout_seconds, created_at "
        "FROM mcp_configs WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,)
    )
    return [McpConfig.from_mapping(row) for row in rows]


async def get_mcp_config(config_id: int, user_id: int) -> Optional[McpConfig]:
    """按照用户和配置 ID 查询 MCP 配置实体。

    Args:
        config_id: MCP 配置数据库主键。
        user_id: 当前登录用户 ID，用于所有权校验。

    Returns:
        找到时返回 MCP 配置实体，否则返回 ``None``。
    """
    row: Optional[Dict[str, Any]] = await fetch_one(
        "SELECT * FROM mcp_configs WHERE id=%s AND user_id=%s",
        (config_id, user_id)
    )
    return McpConfig.from_mapping(row) if row else None


async def create_mcp_config(user_id: int, data: McpConfigInput) -> McpConfig:
    """创建 MCP 配置并返回持久化实体。

    Args:
        user_id: 配置所属用户 ID。
        data: 已完成接口校验的 MCP 配置输入实体。

    Returns:
        包含数据库主键的 MCP 配置实体。
    """
    now = _now()
    config_id = await execute(
        "INSERT INTO mcp_configs "
        "(user_id, name, base_url, endpoint, description, timeout_seconds, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            user_id,
            data.name,
            data.base_url,
            data.endpoint,
            data.description,
            data.timeout_seconds,
            now,
        )
    )
    created = await get_mcp_config(config_id, user_id)
    if created is None:
        raise RuntimeError("MCP 配置创建成功后无法重新加载")
    return created


async def update_mcp_config(
    config_id: int,
    user_id: int,
    data: McpConfigInput,
) -> Optional[McpConfig]:
    """修改用户拥有的 MCP 配置。

    Args:
        config_id: 需要修改的 MCP 配置主键。
        user_id: 当前登录用户 ID，用于所有权校验。
        data: 已完成接口校验的 MCP 配置输入实体。

    Returns:
        修改后的 MCP 配置实体；配置不存在时返回 ``None``。
    """
    existing = await fetch_one(
        "SELECT id FROM mcp_configs WHERE id=%s AND user_id=%s",
        (config_id, user_id)
    )
    if not existing:
        return None

    await execute(
        "UPDATE mcp_configs SET name=%s, base_url=%s, endpoint=%s, description=%s, "
        "timeout_seconds=%s WHERE id=%s",
        (
            data.name,
            data.base_url,
            data.endpoint,
            data.description,
            data.timeout_seconds,
            config_id,
        )
    )
    return await get_mcp_config(config_id, user_id)


async def delete_mcp_config(config_id: int, user_id: int) -> bool:
    """删除用户拥有的 MCP 配置。

    Args:
        config_id: 需要删除的 MCP 配置主键。
        user_id: 当前登录用户 ID，用于所有权校验。

    Returns:
        找到并删除配置时返回 ``True``。
    """
    result = await execute(
        "DELETE FROM mcp_configs WHERE id=%s AND user_id=%s",
        (config_id, user_id)
    )
    return result > 0


async def get_agent_mcps(agent_id: int) -> List[McpConfig]:
    """查询当前 Agent 绑定的 MCP 配置实体。

    Args:
        agent_id: 需要加载工具的 Agent ID。

    Returns:
        当前 Agent 绑定的 MCP 配置实体列表。
    """
    rows: List[Dict[str, Any]] = await fetch_all(
        "SELECT m.* FROM mcp_configs m "
        "JOIN agent_mcps ao ON m.id=ao.mcp_id "
        "WHERE ao.agent_id=%s",
        (agent_id,)
    )
    return [McpConfig.from_mapping(row) for row in rows]
