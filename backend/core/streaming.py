"""LangGraph 智能体事件的 SSE 流式包装器，集成链路追踪。"""
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Mapping, Optional, Sequence, Union

from ..models.chat import AgentStateContext, ChatHistoryMessage
from .agent_state import build_agent_state
from .trace_handler import TraceContext

log = logging.getLogger(__name__)


def sse_event(event_type: str, content: str = "", **metadata: Any) -> str:
    """将一个 SSE 事件编码为单行 JSON，并允许携带轮次、工具等关联字段。"""
    payload_data = {"type": event_type, "content": content}
    payload_data.update(metadata)
    payload = json.dumps(payload_data, ensure_ascii=False)
    return f"data:{payload}\n\n"


def _build_multimodal_content(text: str, attachments_raw=None) -> object:
    """根据文本、图片和 Runtime 文件构造模型消息。"""
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

    runtime_files = [item for item in images if isinstance(item, dict) and item.get("kind") == "runtime_file"]
    if runtime_files:
        lines = ["", "[可用 Runtime 文件]"]
        lines.extend(
            f"- {item.get('name', '未命名文件')}，file_id={item.get('id')}"
            for item in runtime_files
        )
        text += "\n".join(lines)

    content = [{"type": "text", "text": text}]
    for item in images:
        if isinstance(item, str) and item.startswith("data:image/"):
            content.append({"type": "image_url", "image_url": {"url": item}})
    return content if len(content) > 1 else text


async def stream_agent_response(
    agent_executor,
    user_message: str,
    thread_id: str,
    history_messages: Optional[Sequence[Union[ChatHistoryMessage, Mapping[str, Any]]]] = None,
    max_tool_rounds: int = 6,
    trace_ctx: Optional[TraceContext] = None,
    images: Optional[List[str]] = None,
    state_context: Optional[Union[AgentStateContext, Mapping[str, Any]]] = None,
) -> AsyncGenerator[str, None]:
    """
    以 SSE 事件流式输出智能体响应。

    产生的事件类型：
    - llm_round_start: 一轮模型调用开始
    - pending_text_delta: 尚未分类的流式文本
    - llm_round_classified: 本轮文本分类为 thinking 或 answer
    - tool_started/tool_completed: 带稳定 tool_run_id 的工具事件
    - done: 智能体执行完毕
    - error: 错误信息

    展示的是模型主动输出的执行说明，不是供应商隐藏的内部思维链。文本先实时发送，
    再在每轮结束时依据 tool_calls 分类，避免全局状态导致连续工具调用时误判。

    如果提供了 trace_ctx，则为每次 LLM/工具调用写入追踪 Span。
    """
    from langchain_core.messages import AIMessage, HumanMessage

    today = datetime.now().strftime("%Y-%m-%d")

    # 将 MySQL 中的持久化聊天记录恢复成 LangChain 消息对象。
    # 最新一条用户消息已在 chat.py 中先写入数据库，因此这里会一起读出来。
    messages = []
    for item in history_messages or []:
        if isinstance(item, ChatHistoryMessage):
            role = item.role
            content = item.content
            attachments = item.attachments
        else:
            role = item.get("role")
            content = item.get("content") or ""
            attachments = item.get("attachments")
        if not content:
            continue
        if role == "user":
            msg_content = _build_multimodal_content(content, attachments)
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

    # 将现有消息和轻量业务上下文统一放入自定义 State；未传业务字段时行为与旧实现一致。
    if isinstance(state_context, AgentStateContext):
        runtime_file_ids = state_context.runtime_file_ids
        available_skills = state_context.available_skills
        loaded_skills = state_context.loaded_skills
        current_input = state_context.current_input
        current_node_id = state_context.current_node_id
        approval_status = ""
    else:
        state_context = state_context or {}
        runtime_file_ids = state_context.get("runtime_file_ids")
        available_skills = state_context.get("available_skills")
        loaded_skills = state_context.get("loaded_skills")
        current_input = state_context.get("current_input", user_message)
        current_node_id = state_context.get("current_node_id")
        approval_status = state_context.get("approval_status", "")
    initial_state:AgentPlatformState = build_agent_state(
        messages,
        runtime_file_ids=runtime_file_ids,
        available_skills=available_skills,
        loaded_skills=loaded_skills,
        current_input=current_input,
        current_node_id=current_node_id,
        approval_status=approval_status,
    )

    # 每次模型调用都是独立轮次；按 run_id 记录，避免多轮工具调用互相污染状态。
    rounds: Dict[str, Dict[str, Any]] = {}
    latest_round_id = ""

    try:
        async for event in agent_executor.astream_events(
            initial_state,
            config=config,
            version="v2",
        ):
            kind = event["event"]
            run_id = event.get("run_id", "")

            if kind == "on_chat_model_start":
                latest_round_id = str(run_id)
                rounds[latest_round_id] = {"text": []}
                yield sse_event("llm_round_start", round_id=latest_round_id)
                if trace_ctx:
                    model_name = event.get("name", "LLM")
                    input_data = str(event.get("data", {}).get("input", ""))
                    await trace_ctx.on_llm_start(run_id, model_name, input_data)

            elif kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if not chunk:
                    continue

                # 当前尚不知道整轮是否会调用工具，先以 pending 事件实时发送。
                if chunk.content:
                    round_key = str(run_id)
                    rounds.setdefault(round_key, {"text": []})["text"].append(str(chunk.content))
                    yield sse_event("pending_text_delta", str(chunk.content), round_id=round_key)

            elif kind == "on_chat_model_end":
                output = event.get("data", {}).get("output")
                if trace_ctx:
                    await trace_ctx.on_llm_end(run_id, str(output or ""))

                # 完整输出包含工具调用时，本轮文本属于执行说明；否则属于正式回答。
                output_tool_calls = getattr(output, "tool_calls", None) if output else None
                round_key = str(run_id)
                yield sse_event(
                    "llm_round_classified",
                    round_id=round_key,
                    classification="thinking" if output_tool_calls else "answer",
                )

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
                yield sse_event(
                    "tool_started", name=tool_name, input=tool_input,
                    tool_run_id=str(run_id), parent_round_id=latest_round_id,
                )

            elif kind == "on_tool_end":
                tool_name = event.get("name", "")
                output = event.get("data", {}).get("output", "")
                if hasattr(output, "content"):
                    output_str = str(output.content)[:500]
                else:
                    output_str = str(output)[:500]
                if trace_ctx:
                    await trace_ctx.on_tool_end(run_id, output_str)
                yield sse_event(
                    "tool_completed", output_str, name=tool_name,
                    tool_run_id=str(run_id), parent_round_id=latest_round_id,
                )

        yield sse_event("done")

    except Exception as exc:
        log.exception("[Stream] error: %s", exc)
        if trace_ctx:
            await trace_ctx.error(str(exc))
        yield sse_event("error", str(exc))
        yield sse_event("done")
