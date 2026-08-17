"""SSE streaming wrapper for LangGraph agent events with trace integration."""
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional

from .trace_handler import TraceContext

log = logging.getLogger("agent-platform")


def sse_event(event_type: str, content: str = "") -> str:
    """Encode one SSE event as single-line JSON."""
    payload = json.dumps(
        {"type": event_type, "content": content},
        ensure_ascii=False,
    )
    return f"data:{payload}\n\n"


async def stream_agent_response(
    agent_executor,
    user_message: str,
    thread_id: str,
    max_tool_rounds: int = 6,
    trace_ctx: Optional[TraceContext] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream agent response as SSE events.

    Yields:
    - chunk: token streaming content
    - tool_start: tool name being called
    - tool_end: tool result (truncated for UI)
    - done: agent finished
    - error: error message

    If trace_ctx is provided, writes trace spans to MySQL for each LLM/tool call.
    """
    from langchain_core.messages import HumanMessage

    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"[当前日期：{today}] {user_message}"

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": max_tool_rounds * 2 + 5,
    }

    try:
        async for event in agent_executor.astream_events(
            {"messages": [HumanMessage(content=prompt)]},
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
