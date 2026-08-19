import asyncio
from typing import Any


class FakeMcpClient:
    async def call_tool(self,tool_name:str,arguments:str) -> dict[str, Any]:
        return {
            "tool": tool_name,
            "arguments": arguments,
            "result": f"{tool_name} 执行成功"
        }

def make_tool_executor(client: FakeMcpClient,tool_name:str):
    async def executor(**kwargs):
        return await client.call_tool(tool_name, kwargs)
    return executor

async def static_main():
    client = FakeMcpClient()
    print(await make_tool_executor(client, "weather")(city="北京"))
    print(await make_tool_executor(client, "order_info")(order_id="222"))

async def dynamic_main():
    client = FakeMcpClient()
    mcp_tools = [
        {"name":"weather"},
        {"name":"query_order"},
        {"name":"trace_id"}
    ]
    tool_register = {}
    for mcp_tool in mcp_tools:
        name = mcp_tool["name"]
#         获取一个execotor
        executor = make_tool_executor(client,name)
        tool_register[name] = executor

    # 模拟模型返回的 tool_calls
    tool_call = {
        "name": "query_order",
        "arguments": {"order_id": "O1001","date": "2026-10-11","user_id":"ui111"},
    }
    # 根据name 获取 executor
    executor = tool_register[tool_call["name"]]
    result = await executor(**tool_call["arguments"])
    print(result)





if __name__ == "__main__":
    asyncio.run(dynamic_main())





