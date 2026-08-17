"""
MCP Client - connects to MCP Server via Streamable HTTP (JSON-RPC 2.0).
Dynamically discovers tools and executes them.
"""
import json
import uuid
import time
import logging
import httpx
from typing import Dict, List, Optional

log = logging.getLogger("agent-platform")


class McpClient:
    def __init__(self, base_url: str, endpoint: str = "/mcp"):
        self.mcp_url = f"{base_url}{endpoint}"
        self.session_id: Optional[str] = None
        self.initialized = False

    async def _send_request(self, method: str, params: dict = None) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
        }
        if params:
            payload["params"] = params

        log.info(f"[MCP请求] method={method} | url={self.mcp_url}")
        t0 = time.time()

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.mcp_url, json=payload, headers=headers)
            resp.raise_for_status()
        elapsed = int((time.time() - t0) * 1000)

        if not self.session_id and "Mcp-Session-Id" in resp.headers:
            self.session_id = resp.headers["Mcp-Session-Id"]
            log.info(f"[MCP] 获取 session_id={self.session_id}")

        content_type = resp.headers.get("Content-Type", "")

        if "text/event-stream" in content_type:
            for line in resp.text.split("\n"):
                line = line.strip()
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data:
                        try:
                            result = json.loads(data)
                            if "result" in result:
                                log.info(f"[MCP响应] method={method} | 耗时={elapsed}ms")
                                return result["result"]
                            elif "error" in result:
                                raise Exception(f"MCP error: {result['error']}")
                        except json.JSONDecodeError:
                            continue
            raise Exception(f"MCP SSE 响应中未找到有效数据")
        else:
            data = resp.json()
            if "result" in data:
                log.info(f"[MCP响应] method={method} | 耗时={elapsed}ms")
                return data["result"]
            elif "error" in data:
                raise Exception(f"MCP error: {data['error']}")
            return data

    async def _send_notification(self, method: str, params: dict = None):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        payload = {"jsonrpc": "2.0", "method": method}
        if params:
            payload["params"] = params

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.mcp_url, json=payload, headers=headers)
            resp.raise_for_status()

    async def initialize(self) -> dict:
        log.info(f"[MCP] 正在初始化会话 | url={self.mcp_url}")
        result = await self._send_request("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "agent-platform", "version": "1.0.0"}
        })
        await self._send_notification("notifications/initialized")
        self.initialized = True
        log.info(f"[MCP] 初始化成功")
        return result

    async def list_tools(self) -> List[dict]:
        if not self.initialized:
            await self.initialize()
        result = await self._send_request("tools/list")
        tools = result.get("tools", [])
        log.info(f"[MCP] 获取到 {len(tools)} 个工具")
        return tools

    async def call_tool_raw(self, name: str, arguments: dict = None) -> dict:
        if not self.initialized:
            await self.initialize()

        params = {"name": name}
        if arguments:
            params["arguments"] = arguments

        log.info(f"[MCP工具调用] name={name} | args={json.dumps(arguments or {}, ensure_ascii=False)}")
        t0 = time.time()
        result = await self._send_request("tools/call", params)
        elapsed = int((time.time() - t0) * 1000)

        log.info(f"[MCP工具结果] name={name} | 耗时={elapsed}ms")
        return result

    async def call_tool(self, name: str, arguments: dict = None) -> str:
        result = await self.call_tool_raw(name, arguments)

        content = result.get("content", [])
        if content and isinstance(content, list):
            texts = [item.get("text", "") for item in content if item.get("type") == "text"]
            full_text = "\n".join(texts)
            log.info(f"[MCP工具文本] name={name} | 返回长度={len(full_text)}")
            return full_text
        return json.dumps(result, ensure_ascii=False)


def mcp_tools_to_openai_format(mcp_tools: List[dict]) -> List[dict]:
    openai_tools = []
    for tool in mcp_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {
                    "type": "object",
                    "properties": {},
                })
            }
        })
    return openai_tools


def build_mcp_executors(mcp_clients: Dict[str, McpClient]) -> Dict[str, callable]:
    executors = {}
    for tool_name, (client, _) in mcp_clients.items():
        def make_executor(c, n):
            async def executor(**kwargs):
                return await c.call_tool(n, kwargs)
            return executor
        executors[tool_name] = make_executor(client, tool_name)
    return executors
