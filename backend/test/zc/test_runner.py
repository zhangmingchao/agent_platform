import asyncio
import dataclasses
import typing
from typing import Any,Dict,Awaitable


@dataclasses.dataclass
class NativeWorkflowState:
    status:str
    work_id:int

AgentNodeRunner = typing.Callable[
    [Dict[str,Any],NativeWorkflowState,str,int],
    Awaitable[str],
]


async def execute_node_weather(data:dict[str,Any],state:NativeWorkflowState,nodeId:str,retry:int) -> str:
    await asyncio.sleep(1)
    prompt = data.get("prompt", "")
    return (
        f"LLM 节点执行完成："
        f"workflow={state.work_id}, "
        f"node={nodeId}, "
        f"retry={retry}, "
        f"prompt={prompt}"
    )

async def execute_node_http(data:dict[str,Any],state:NativeWorkflowState,nodeId:str,retry:int) -> str:
    await asyncio.sleep(1)
    url = data.get("url", "")
    return (
        f"HTTP 节点执行完成："
        f"workflow={state.work_id}, "
        f"node={nodeId}, "
        f"url={url}"
    )

async def execute_ndoe(runner:AgentNodeRunner,data:dict[str,Any],node_id:str,retry:int,state:NativeWorkflowState) -> str:
    state.status = "running"
    result = await runner(data,state,node_id,retry)
    state.status = "success"
    return result



async def main() -> None:
    state = NativeWorkflowState(status="pendding",work_id=3)
    llm_result = await execute_ndoe(
        runner=execute_node_weather,
        data={"prompt":"查询今天的天气"},
        node_id="天气查询",
        retry=3,
        state=state,
    )

    print(llm_result)
    print("当前状态：", state.status)

    llm_result = await execute_ndoe(
        runner=execute_node_http,
        data={"prompt":"查询今天的天气","url":"http://www.baidu.com"},
        node_id="天气查询",
        retry=3,
        state=state,
    )

    print(llm_result)
    print("当前状态：", state.status)


if __name__ == "__main__":
    asyncio.run(main())





