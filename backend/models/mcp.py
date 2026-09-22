"""MCP Server 配置使用的领域实体。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class McpConfigInput:
    """创建或修改 MCP Server 时使用的输入实体。

    Attributes:
        name: MCP Server 的展示名称。
        base_url: MCP Server 的基础地址。
        endpoint: Streamable HTTP 的端点路径。
        description: MCP Server 的用途说明。
        timeout_seconds: 一次完整 MCP 操作允许的最大秒数。
    """

    name: str
    base_url: str
    endpoint: str
    description: str
    timeout_seconds: int = 30


@dataclass(frozen=True)
class McpConfig:
    """已经持久化的 MCP Server 配置实体。

    Attributes:
        id: MCP 配置数据库主键。
        user_id: 配置所属的平台用户 ID。
        name: MCP Server 的展示名称。
        base_url: MCP Server 的基础地址。
        endpoint: Streamable HTTP 的端点路径。
        description: MCP Server 的用途说明。
        timeout_seconds: 初始化、工具发现或工具调用的整体超时秒数。
        created_at: 配置创建时间。
    """

    id: int
    user_id: int
    name: str
    base_url: str
    endpoint: str
    description: str
    timeout_seconds: int = 30
    created_at: Optional[datetime] = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "McpConfig":
        """从数据库记录构造 MCP 配置实体。

        Args:
            data: 数据库返回的 MCP 配置字段映射。

        Returns:
            完成默认值规范化的 MCP 配置实体。
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None
        return cls(
            id=int(data.get("id") or 0),
            user_id=int(data.get("user_id") or 0),
            name=str(data.get("name") or ""),
            base_url=str(data.get("base_url") or ""),
            endpoint=str(data.get("endpoint") or "/mcp"),
            description=str(data.get("description") or ""),
            timeout_seconds=int(data.get("timeout_seconds") or 30),
            created_at=created_at if isinstance(created_at, datetime) else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为 HTTP 响应使用的可序列化结构。"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "base_url": self.base_url,
            "endpoint": self.endpoint,
            "description": self.description,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at,
        }

    def to_factory_dict(self) -> Dict[str, Any]:
        """转换为 Agent 工具工厂所需的 MCP 配置结构。"""
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "endpoint": self.endpoint,
            "description": self.description,
            "timeout_seconds": self.timeout_seconds,
        }
