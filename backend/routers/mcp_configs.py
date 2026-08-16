import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth import get_current_user
from ..mcp_client import McpClient
from ..services.mcp_config_service import (
    create_mcp_config,
    delete_mcp_config,
    get_mcp_config,
    list_mcp_configs,
    update_mcp_config,
)

router = APIRouter(prefix="/api/mcp-configs", tags=["MCP Configurations"])
log = logging.getLogger("agent-platform")


async def _run_mcp_request(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args))


@router.get("")
async def api_list_mcp_configs(user: dict = Depends(get_current_user)):
    return await list_mcp_configs(user["user_id"])


@router.get("/{config_id}")
async def api_get_mcp_config(config_id: int, user: dict = Depends(get_current_user)):
    cfg = await get_mcp_config(config_id, user["user_id"])
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return cfg


@router.post("")
async def api_create_mcp(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    return await create_mcp_config(user["user_id"], body)


@router.put("/{config_id}")
async def api_update_mcp(config_id: int, request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    cfg = await update_mcp_config(config_id, user["user_id"], body)
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return cfg


@router.delete("/{config_id}")
async def api_delete_mcp(config_id: int, user: dict = Depends(get_current_user)):
    success = await delete_mcp_config(config_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return {"success": True}


@router.get("/{config_id}/tools")
async def api_list_mcp_tools(config_id: int, user: dict = Depends(get_current_user)):
    cfg = await get_mcp_config(config_id, user["user_id"])
    if not cfg:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")

    try:
        client = McpClient(cfg["base_url"], cfg["endpoint"])
        tools = await _run_mcp_request(client.list_tools)
        return {"tools": tools}
    except Exception as exc:
        log.exception("获取 MCP 工具失败: config_id=%s", config_id)
        raise HTTPException(status_code=502, detail=f"连接 MCP 失败: {exc}")


@router.post("/{config_id}/call")
async def api_call_mcp_tool(config_id: int, request: Request, user: dict = Depends(get_current_user)):
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
        client = McpClient(cfg["base_url"], cfg["endpoint"])
        result = await _run_mcp_request(client.call_tool_raw, tool_name, arguments)
        return {"result": result}
    except Exception as exc:
        log.exception("调用 MCP 工具失败: config_id=%s tool=%s", config_id, tool_name)
        raise HTTPException(status_code=502, detail=f"调用 MCP 工具失败: {exc}")
