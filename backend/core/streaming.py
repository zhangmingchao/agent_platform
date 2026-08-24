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


def _build_multimodal_content(text: str, attachments_raw=None) -> object:
    """根据文本和附件构造多模态 content。无图片时返回纯字符串。"""
    if not attachments_raw:
        return text

    # attachments 可能是 JSON 字符串或已解析的列表
    images = attachments_raw
    if isinstance(attachments_raw, str):
        try:
            images = json.loads(attachments_raw)
        except json.JSONDecodeError:
            images = []
    if not isinstance(images, list) or not images:
        return text

    content = [{"type": "text", "text": text}]
    for img in images:
        if isinstance(img, str) and img.startswith("data:image/"):
            content.append({"type": "image_url", "image_url": {"url": img}})
    return content


async def stream_agent_response(
    agent_executor,
    user_message: str,
    thread_id: str,
    history_messages: Optional[List[Dict]] = None,
    max_tool_rounds: int = 6,
    trace_ctx: Optional[TraceContext] = None,
    images: Optional[List[str]] = None,
) -> AsyncGenerator[str, None]:
    """
    以 SSE 事件流式输出智能体响应。

    产生的事件类型：
    - thinking: 思考阶段的文本（LLM 在调用工具前的推理过程）
    - chunk: 最终回答的流式 Token
    - tool_start: 工具调用开始（JSON: {name, input}）
    - tool_end: 工具返回结果（截断后字符串）
    - reclassify: 阶段重分类通知（"answer"=思考实际是回答 / "thinking"=回答实际是思考）
    - done: 智能体执行完毕
    - error: 错误信息

    思维链（CoT）展示原理：
    - 跟踪 has_seen_tool 标记是否已看到工具调用
    - 工具调用前的 LLM 文本 → thinking 事件（思考过程）
    - 工具调用后的 LLM 文本 → chunk 事件（最终回答）
    - 无工具调用时直接回答 → 先发 thinking，on_chat_model_end 时发 reclassify:answer 修正
    - 多轮工具调用中误判 → on_chat_model_end 检查 tool_calls，发 reclassify:thinking 修正

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
            msg_content = _build_multimodal_content(content, item.get("attachments"))
            messages.append(HumanMessage(content=msg_content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    # 日期提示只加到当前用户这轮，避免污染历史消息。
    if messages and isinstance(messages[-1], HumanMessage):
        if isinstance(messages[-1].content, str):
            messages[-1].content = f"[当前日期：{today}] {messages[-1].content}"
        elif isinstance(messages[-1].content, list):
            for part in messages[-1].content:
                if part.get("type") == "text":
                    part["text"] = f"[当前日期：{today}] {part['text']}"
                    break
    else:
        if images:
            content = _build_multimodal_content(f"[当前日期：{today}] {user_message}", images)
            messages.append(HumanMessage(content=content))
        else:
            messages.append(HumanMessage(content=f"[当前日期：{today}] {user_message}"))

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": max_tool_rounds * 2 + 5,
    }

    # 思维链状态跟踪
    has_seen_tool = False              # 是否已看到任何工具调用
    current_call_text_phase = None    # 当前 LLM 调用的文本被发为了什么（"thinking" / "chunk"）

    try:
        async for event in agent_executor.astream_events(
            {"messages": messages},
            config=config,
            version="v2",
        ):
            kind = event["event"]
            run_id = event.get("run_id", "")

            if kind == "on_chat_model_start":
                current_call_text_phase = None  # 重置：新一轮 LLM 调用
                if trace_ctx:
                    model_name = event.get("name", "LLM")
                    input_data = str(event.get("data", {}).get("input", ""))
                    await trace_ctx.on_llm_start(run_id, model_name, input_data)

            elif kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if not chunk:
                    continue

                # 检查是否有工具调用片段（LLM 正在决定调工具）
                tool_call_chunks = getattr(chunk, "tool_call_chunks", None) or []
                if tool_call_chunks:
                    has_seen_tool = True

                # 处理文本内容
                if chunk.content:
                    if has_seen_tool:
                        # 已有工具调用完成 → 这是最终回答
                        if current_call_text_phase is None:
                            current_call_text_phase = "chunk"
                        yield sse_event("chunk", chunk.content)
                    else:
                        # 还没看到工具调用 → 可能是思考过程
                        if current_call_text_phase is None:
                            current_call_text_phase = "thinking"
                        yield sse_event("thinking", chunk.content)

            elif kind == "on_chat_model_end":
                output = event.get("data", {}).get("output")
                if trace_ctx:
                    await trace_ctx.on_llm_end(run_id, str(output or ""))

                # 检查输出是否包含 tool_calls
                output_tool_calls = getattr(output, "tool_calls", None) if output else None
                if output_tool_calls:
                    # 这次 LLM 调用产生了工具调用
                    if current_call_text_phase == "chunk":
                        # 之前的文本被误判为最终回答，实际是思考 → 通知前端修正
                        yield sse_event("reclassify", "thinking")
                    has_seen_tool = True
                elif not has_seen_tool:
                    # 没有工具调用，且从未看到过工具 → 直接回答
                    if current_call_text_phase == "thinking":
                        # 之前发出的 thinking 实际是最终回答 → 通知前端修正
                        yield sse_event("reclassify", "answer")
                    has_seen_tool = True  # 防止后续 LLM 调用重复触发

            elif kind == "on_tool_start":
                tool_name = event.get("name", "")
                tool_input_raw = event.get("data", {}).get("input", "")
                # 工具输入可能是 dict 或字符串
                if isinstance(tool_input_raw, dict):
                    tool_input = json.dumps(tool_input_raw, ensure_ascii=False)[:200]
                else:
                    tool_input = str(tool_input_raw)[:200]
                if trace_ctx:
                    await trace_ctx.on_tool_start(run_id, tool_name, tool_input)
                yield sse_event("tool_start", json.dumps(
                    {"name": tool_name, "input": tool_input}, ensure_ascii=False
                ))

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
