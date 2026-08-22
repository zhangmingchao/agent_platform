"""LangGraph 智能体事件的 SSE 流式包装器，集成链路追踪。"""
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional

from .trace_handler import TraceContext

log = logging.getLogger("agent-platform")


def sse_event(event_type: str, content: str = "") -> str:
    """将一个 SSE 事件编码为单行 JSON。"""
    payload = json.dumps(
        {"type": event_type, "content": content},
        ensure_ascii=False,
    )
    return f"data:{payload}\n\n"


async def stream_agent_response(
    agent_executor,
    user_message: str,
    thread_id: str,
    history_messages: Optional[List[Dict]] = None,
    max_tool_rounds: int = 6,
    trace_ctx: Optional[TraceContext] = None,
) -> AsyncGenerator[str, None]:
    """
    以 SSE 事件流式输出智能体响应。

    产生的事件类型：
    - chunk: Token 流式内容
    - tool_start: 正在调用的工具名称
    - tool_end: 工具结果（UI 展示时截断）
    - done: 智能体执行完毕
    - error: 错误信息

    如果提供了 trace_ctx，则为每次 LLM/工具调用写入 MySQL 追踪 Span。
    """
    from langchain_core.messages import AIMessage, HumanMessage

    today = datetime.now().strftime("%Y-%m-%d")

    # 将 MySQL 中的持久化聊天记录恢复成 LangChain 消息对象。
    # 最新一条用户消息已在 chat.py 中先写入数据库，因此这里会一起读出来。
    messages = []
    for item in history_messages or []:
        role = item.get("role")
        content = item.get("content") or ""
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    # 日期提示只加到当前用户这轮，避免污染历史消息。
    if messages and isinstance(messages[-1], HumanMessage):
        messages[-1].content = f"[当前日期：{today}] {messages[-1].content}"
    else:
        messages.append(HumanMessage(content=f"[当前日期：{today}] {user_message}"))

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": max_tool_rounds * 2 + 5,
    }

    try:
        async for event in agent_executor.astream_events(
            {"messages": messages},
            config=config,
            version="v2",
        ):
            kind = event["event"]
            run_id = event.get("run_id", "")

            if kind == "on_chat_model_start":
                if trace_ctx:
                    model_name = event.get("name", "LLM")
                    input_data = str(event.get("data", {}).get("input", ""))
                    await trace_ctx.on_llm_start(run_id, model_name, input_data)

            elif kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and chunk.content:
                    yield sse_event("chunk", chunk.content)

            elif kind == "on_chat_model_end":
                if trace_ctx:
                    output = str(event.get("data", {}).get("output", ""))
                    await trace_ctx.on_llm_end(run_id, output)

            elif kind == "on_tool_start":
                tool_name = event.get("name", "")
                if trace_ctx:
                    input_data = str(event.get("data", {}).get("input", ""))
                    await trace_ctx.on_tool_start(run_id, tool_name, input_data)
                yield sse_event("tool_start", tool_name)

            elif kind == "on_tool_end":
                tool_name = event.get("name", "")
                output = event.get("data", {}).get("output", "")
                if hasattr(output, "content"):
                    output_str = str(output.content)[:500]
                else:
                    output_str = str(output)[:500]
                if trace_ctx:
                    await trace_ctx.on_tool_end(run_id, output_str)
                yield sse_event("tool_end", output_str)

        yield sse_event("done")

    except Exception as exc:
        log.exception("[Stream] error: %s", exc)
        if trace_ctx:
            await trace_ctx.error(str(exc))
        yield sse_event("error", str(exc))
        yield sse_event("done")
