import logging

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..config import HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS, MCP_CALL_RATE_LIMIT
from ..mcp_client import McpClient
from ..models.mcp import McpConfigInput
from ..rate_limit import RateLimitRule, enforce_rate_limit
from ..services.mcp_config_service import (
    create_mcp_config,
    delete_mcp_config,
    get_mcp_config,
    list_mcp_configs,
    update_mcp_config,
)

router = APIRouter(prefix="/api/mcp-configs", tags=["MCP Configurations"])
log = logging.getLogger(__name__)
MCP_CALL_RULE = RateLimitRule(
    name="mcp-call-user",
    limit=MCP_CALL_RATE_LIMIT,
    window_seconds=HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS,
)


class McpConfigPayload(BaseModel):
    """创建或修改 MCP Server 的请求结构。

    Attributes:
        name: MCP Server 展示名称。
        base_url: MCP Server 基础地址。
        endpoint: Streamable HTTP 端点路径。
        description: MCP Server 用途说明。
        timeout_seconds: 一次完整 MCP 操作的超时秒数。
    """

    name: str = Field(default="New MCP", min_length=1, max_length=200)
    base_url: str = Field(default="http://localhost:18888", min_length=1, max_length=500)
    endpoint: str = Field(default="/mcp", min_length=1, max_length=100)
    description: str = Field(default="", max_length=5000)
    timeout_seconds: int = Field(default=30, ge=1, le=60)

    def to_entity(self) -> McpConfigInput:
        """转换为业务服务使用的 MCP 输入实体。"""
        return McpConfigInput(
            name=self.name.strip(),
            base_url=self.base_url.strip().rstrip("/"),
            endpoint=self.endpoint.strip(),
            description=self.description.strip(),
            timeout_seconds=self.timeout_seconds,
        )


@router.get("")
async def api_list_mcp_configs(
    user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    configs = await list_mcp_configs(user["user_id"])
    return [config.to_dict() for config in configs]


@router.get("/{config_id}")
async def api_get_mcp_config(
    config_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    cfg = await get_mcp_config(config_id, user["user_id"])
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return cfg.to_dict()


@router.post("")
async def api_create_mcp(
    payload: McpConfigPayload,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    config = await create_mcp_config(user["user_id"], payload.to_entity())
    return config.to_dict()


@router.put("/{config_id}")
async def api_update_mcp(
    config_id: int,
    payload: McpConfigPayload,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    cfg = await update_mcp_config(config_id, user["user_id"], payload.to_entity())
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return cfg.to_dict()


@router.delete("/{config_id}")
async def api_delete_mcp(
    config_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, bool]:
    success = await delete_mcp_config(config_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return {"success": True}


@router.get("/{config_id}/tools")
async def api_list_mcp_tools(
    config_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    cfg = await get_mcp_config(config_id, user["user_id"])
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")

    try:
        client = McpClient(cfg.base_url, cfg.endpoint, cfg.timeout_seconds)
        tools = await client.list_tools()
        return {"tools": tools}
    except Exception as exc:
        log.exception("获取 MCP 工具失败: config_id=%s", config_id)
        raise HTTPException(status_code=502, detail=f"连接 MCP 失败: {exc}")


@router.post("/{config_id}/call")
async def api_call_mcp_tool(
    config_id: int,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    await enforce_rate_limit(MCP_CALL_RULE, str(user["user_id"]))
    cfg = await get_mcp_config(config_id, user["user_id"])
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")

    body = await request.json()
    tool_name = body.get("name", "").strip()
    arguments = body.get("arguments", {})
    if not tool_name:
        raise HTTPException(status_code=400, detail="需要工具名称")
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="arguments 必须是 JSON 对象")

    try:
        client = McpClient(cfg.base_url, cfg.endpoint, cfg.timeout_seconds)
        result = await client.call_tool_raw(tool_name, arguments)
        return {"result": result}
    except Exception as exc:
        log.exception("调用 MCP 工具失败: config_id=%s tool=%s", config_id, tool_name)
        raise HTTPException(status_code=502, detail=f"调用 MCP 工具失败: {exc}")
