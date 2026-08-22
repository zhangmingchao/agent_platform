"""将 MCP 工具转换为 LangChain StructuredTool 实例。"""
import json
import logging
from typing import Dict, List

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from ..mcp_client import McpClient

log = logging.getLogger("agent-platform")


def _create_pydantic_schema(input_schema: dict) -> type:
    """从 MCP 输入模式创建 Pydantic 模型。"""
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    fields = {}
    for name, prop in properties.items():
        prop_type = prop.get("type", "string")
        description = prop.get("description", "")

        if prop_type == "integer":
            py_type = int
        elif prop_type == "number":
            py_type = float
        elif prop_type == "boolean":
            py_type = bool
        else:
            py_type = str

        if name in required:
            fields[name] = (py_type, Field(description=description))
        else:
            fields[name] = (py_type, Field(default=None, description=description))

    if not fields:
        return BaseModel

    return create_model("MCPToolInput", **fields)


async def mcp_tools_to_langchain(client: McpClient) -> List[StructuredTool]:
    """发现 MCP 工具并转换为 LangChain StructuredTool。"""
    mcp_tools = await client.list_tools()
    langchain_tools = []

    for tool in mcp_tools:
        name = tool["name"]
        description = tool.get("description", "")
        input_schema = tool.get("inputSchema", {"type": "object", "properties": {}})
        args_schema = _create_pydantic_schema(input_schema)

        def make_executor(c, n):
            async def executor(**kwargs):
                return await c.call_tool(n, kwargs)
            return executor

        lc_tool = StructuredTool.from_function(
            coroutine=make_executor(client, name),
            name=name,
            description=description,
            args_schema=args_schema,
        )
        langchain_tools.append(lc_tool)

    log.info(f"[MCP] discovered {len(langchain_tools)} tools")
    return langchain_tools


async def build_mcp_langchain_tools(mcp_configs: List[Dict]) -> List[StructuredTool]:
    """从所有 MCP 配置构建 LangChain 工具。"""
    all_tools = []

    for mcp_cfg in mcp_configs:
        try:
            client = McpClient(mcp_cfg["base_url"], mcp_cfg["endpoint"])
            tools = await mcp_tools_to_langchain(client)
            all_tools.extend(tools)
            log.info(f"[MCP] {mcp_cfg['name']} loaded {len(tools)} tools")
        except Exception as e:
            log.warning(f"[MCP] {mcp_cfg['name']} connection failed: {e}")
    return all_tools
