"""
MCP 客户端 —— 通过可流式 HTTP（JSON-RPC 2.0）连接 MCP 服务器。
动态发现工具并执行。
"""
import asyncio
import json
import uuid
import time
import logging
import httpx
from typing import Awaitable, Callable, Dict, List, Optional, TypeVar

log = logging.getLogger(__name__)
ResultType = TypeVar("ResultType")


class McpOperationTimeoutError(TimeoutError):
    """表示一次完整 MCP 操作超过配置时限。

    Attributes:
        operation: 超时的 MCP 操作名称。
        timeout_seconds: 当前 MCP 配置的超时秒数。
    """

    def __init__(self, operation: str, timeout_seconds: int) -> None:
        """创建 MCP 操作超时异常。

        Args:
            operation: 初始化、工具发现或工具调用的操作名称。
            timeout_seconds: 该 MCP Server 配置的整体超时秒数。
        """
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(f"MCP {operation} 超过 {timeout_seconds} 秒")


class McpClient:
    """通过 Streamable HTTP 访问一个 MCP Server。

    Attributes:
        mcp_url: MCP Server 的完整请求地址。
        timeout_seconds: 一次完整 MCP 操作的超时秒数。
        session_id: MCP Server 返回的会话标识。
        initialized: 当前客户端是否已经完成 MCP 初始化握手。
    """

    def __init__(
        self,
        base_url: str,
        endpoint: str = "/mcp",
        timeout_seconds: int = 30,
    ) -> None:
        """创建 MCP 客户端。

        Args:
            base_url: MCP Server 基础地址。
            endpoint: Streamable HTTP 端点路径。
            timeout_seconds: 初始化、发现或调用工具的整体超时秒数。
        """
        if timeout_seconds < 1 or timeout_seconds > 60:
            raise ValueError("MCP 超时时间必须在 1 到 60 秒之间")
        self.mcp_url = f"{base_url}{endpoint}"
        self.timeout_seconds = timeout_seconds
        self.session_id: Optional[str] = None
        self.initialized = False

    async def _run_operation(
        self,
        operation: str,
        action: Callable[[], Awaitable[ResultType]],
    ) -> ResultType:
        """使用配置的整体时限执行一次 MCP 操作。

        Args:
            operation: 用于错误信息的 MCP 操作名称。
            action: 实际执行初始化、工具发现或工具调用的异步函数。

        Returns:
            异步操作产生的原始结果。
        """
        try:
            async with asyncio.timeout(self.timeout_seconds):
                return await action()
        except TimeoutError as exc:
            raise McpOperationTimeoutError(operation, self.timeout_seconds) from exc

    async def _send_request(
        self,
        method: str,
        params: Optional[Dict] = None,
    ) -> Dict:
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

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
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

    async def _send_notification(
        self,
        method: str,
        params: Optional[Dict] = None,
    ) -> None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        payload = {"jsonrpc": "2.0", "method": method}
        if params:
            payload["params"] = params

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(self.mcp_url, json=payload, headers=headers)
            resp.raise_for_status()

    async def _initialize(self) -> Dict:
        """执行不额外创建超时边界的 MCP 初始化握手。"""
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

    async def initialize(self) -> Dict:
        """在配置的整体时限内初始化 MCP 会话。"""
        return await self._run_operation("初始化", self._initialize)

    async def _list_tools(self) -> List[Dict]:
        """执行不额外创建超时边界的初始化和工具发现。"""
        if not self.initialized:
            await self._initialize()
        result = await self._send_request("tools/list")
        tools = result.get("tools", [])
        log.info(f"[MCP] 获取到 {len(tools)} 个工具")
        return tools

    async def list_tools(self) -> List[dict]:
        """在配置的整体时限内完成初始化和工具发现。"""
        return await self._run_operation("工具发现", self._list_tools)

    async def _call_tool_raw(
        self,
        name: str,
        arguments: Optional[Dict] = None,
    ) -> Dict:
        """执行不额外创建超时边界的初始化和工具调用。"""
        if not self.initialized:
            await self._initialize()

        params = {"name": name}
        if arguments:
            params["arguments"] = arguments

        log.info(f"[MCP工具调用] name={name} | args={json.dumps(arguments or {}, ensure_ascii=False)}")
        t0 = time.time()
        result = await self._send_request("tools/call", params)
        elapsed = int((time.time() - t0) * 1000)

        log.info(f"[MCP工具结果] name={name} | 耗时={elapsed}ms")
        return result

    async def call_tool_raw(
        self,
        name: str,
        arguments: Optional[Dict] = None,
    ) -> Dict:
        """在配置的整体时限内完成初始化和原始工具调用。

        Args:
            name: MCP 工具名称。
            arguments: 发送给 MCP 工具的参数对象。

        Returns:
            MCP Server 返回的原始结果对象。
        """
        return await self._run_operation(
            f"工具调用 {name}",
            lambda: self._call_tool_raw(name, arguments),
        )

    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict] = None,
    ) -> str:
        """调用 MCP 工具并提取适合返回给模型的文本。

        Args:
            name: MCP 工具名称。
            arguments: 发送给 MCP 工具的参数对象。

        Returns:
            MCP 文本内容或 JSON 序列化结果。
        """
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
        def make_executor(c, n) -> Callable[..., Awaitable[str]]:
            async def executor(**kwargs) -> str:
                return await c.call_tool(n, kwargs)
            return executor
        executors[tool_name] = make_executor(client, tool_name)
    return executors
