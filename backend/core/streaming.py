"""LangGraph 智能体事件的 SSE 流式包装器，集成链路追踪。"""
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Mapping, Optional, Sequence, Union

from langgraph.graph.state import CompiledStateGraph

from ..models.agent_loop import AgentLoopEvent, AgentLoopPhase
from ..models.chat import AgentStateContext, ChatHistoryMessage
from ..models.session_event import SessionEventRecord, SessionEventSource, SessionEventType
from ..models.task_planning import PlanningMode
from ..services.session_event_service import append_session_event
from .agent_state import build_agent_state
from .execution_control import AgentExecutionTimeoutError, stream_with_total_timeout
from .trace_handler import TraceContext
from .token_usage import extract_token_usage

log = logging.getLogger(__name__)


def _agent_loop_sse(event: AgentLoopEvent) -> str:
    """将 Agent Loop 生命周期事件编码为 SSE。"""
    return sse_event("agent_loop_event", **event.to_sse_metadata())


async def _append_agent_loop_event(
    event: AgentLoopEvent,
    trace_ctx: Optional[TraceContext],
) -> None:
    """将 Agent Loop 生命周期事件追加到 Session 事件日志。

    Args:
        event: 当前生命周期事件。
        trace_ctx: 当前 Trace 上下文；为空时表示缺少持久化归属，跳过写入。
    """
    if trace_ctx is None or not isinstance(trace_ctx.run_id, int):
        return
    await append_session_event(
        SessionEventRecord(
            user_id=trace_ctx.user_id,
            session_id=trace_ctx.session_id,
            trace_run_id=trace_ctx.run_id,
            agent_id=trace_ctx.agent_id,
            workflow_run_id=trace_ctx.workflow_run_id,
            workflow_step_id=trace_ctx.workflow_step_id,
            event_source=SessionEventSource.AGENT_LOOP,
            event_type=SessionEventType.AGENT_LOOP,
            turn_id=event.turn_id,
            step_id=event.step_id or "",
            run_id=event.run_id or "",
            phase=event.phase.value,
            name=event.name,
            status=str(event.metadata.get("status") or ""),
            payload=event.to_sse_metadata(),
        )
    )


def _model_output_text(output: Any) -> str:
    """提取模型结束事件中的文本，兼容字符串和多段内容。"""
    content = getattr(output, "content", output)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, Mapping):
                parts.append(str(item.get("text") or item.get("content") or ""))
        return "".join(parts)
    return ""


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
    agent_executor: CompiledStateGraph,
    user_message: str,
    thread_id: str,
    history_messages: Optional[Sequence[Union[ChatHistoryMessage, Mapping[str, Any]]]] = None,
    max_tool_rounds: int = 6,
    execution_timeout_seconds: int = 120,
    trace_ctx: Optional[TraceContext] = None,
    images: Optional[List[str]] = None,
    state_context: Optional[Union[AgentStateContext, Mapping[str, Any]]] = None,
) -> AsyncGenerator[str, None]:
    """
    以 SSE 事件流式输出智能体响应。

    产生的事件类型：
    - llm_round_start: 一轮模型调用开始
    - agent_loop_event: Agent Loop 生命周期阶段事件
    - pending_text_delta: 尚未分类的流式文本
    - llm_round_classified: 本轮文本分类为 thinking 或 answer
    - tool_started/tool_completed: 带稳定 tool_run_id 的工具事件
    - done: 智能体执行完毕
    - error: 错误信息

    展示的是模型主动输出的执行说明，不是供应商隐藏的内部思维链。文本先实时发送，
    再在每轮结束时依据 tool_calls 分类，避免全局状态导致连续工具调用时误判。

    如果提供了 trace_ctx，则为每次 LLM/工具调用写入追踪 Span。

    Args:
        agent_executor: 已编译的 LangGraph Agent 执行器。
        user_message: 当前用户输入。
        thread_id: 本次 LangGraph 执行使用的线程标识。
        history_messages: 平台或调用方维护的聊天历史。
        max_tool_rounds: 单次 Agent 最大工具迭代次数。
        execution_timeout_seconds: Agent 整体执行超时秒数。
        trace_ctx: 本次执行关联的 Trace 上下文。
        images: 当前消息附带的 Base64 图片。
        state_context: 注入 LangGraph State 的业务上下文。

    Yields:
        编码后的 SSE 事件字符串。
    """
    from langchain_core.messages import AIMessage, HumanMessage

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

    # # 日期提示只加到当前用户这轮，避免污染历史消息。
    # if messages and isinstance(messages[-1], HumanMessage):
    #     if isinstance(messages[-1].content, str):
    #         messages[-1].content = f"[当前日期：{today}] {messages[-1].content}"
    #     elif isinstance(messages[-1].content, list):
    #         for part in messages[-1].content:
    #             if part.get("type") == "text":
    #                 part["text"] = f"[当前日期：{today}] {part['text']}"
    #                 break
    # else:
    #     if images:
    #         content = _build_multimodal_content(f"[当前日期：{today}] {user_message}", images)
    #         messages.append(HumanMessage(content=content))
    #     else:
    #         messages.append(HumanMessage(content=f"[当前日期：{today}] {user_message}"))

    # 将现有消息和轻量业务上下文统一放入自定义 State；未传业务字段时行为与旧实现一致。
    if isinstance(state_context, AgentStateContext):
        runtime_file_ids = state_context.runtime_file_ids
        available_skills = state_context.available_skills
        loaded_skills = state_context.loaded_skills
        current_input = state_context.current_input
        current_node_id = state_context.current_node_id
        approval_status = ""
        planning_mode = state_context.planning_mode.value
    else:
        state_context = state_context or {}
        runtime_file_ids = state_context.get("runtime_file_ids")
        available_skills = state_context.get("available_skills")
        loaded_skills = state_context.get("loaded_skills")
        current_input = state_context.get("current_input", user_message)
        current_node_id = state_context.get("current_node_id")
        approval_status = state_context.get("approval_status", "")
        planning_mode = str(state_context.get("planning_mode") or "disabled")
    initial_state = build_agent_state(
        messages,
        runtime_file_ids=runtime_file_ids,
        available_skills=available_skills,
        loaded_skills=loaded_skills,
        current_input=current_input,
        current_node_id=current_node_id,
        approval_status=approval_status,
        planning_mode=planning_mode,
    )
    planning_enabled = planning_mode == PlanningMode.EXPLICIT.value
    recursion_limit = (
        max(40, max_tool_rounds * 2 + 20)
        if planning_enabled
        else max_tool_rounds * 2 + 5
    )
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit,
    }

    # 每次模型调用都是独立轮次；按 run_id 记录，避免多轮工具调用互相污染状态。
    rounds: Dict[str, Dict[str, Any]] = {}
    latest_round_id = ""
    turn_id = thread_id
    step_no = 0
    current_step_id = ""
    current_step_closed = True

    def start_step(run_id: str, node_name: str) -> AgentLoopEvent:
        """创建步骤开始事件，并更新当前步骤状态。"""
        nonlocal step_no, current_step_id, current_step_closed
        step_no += 1
        current_step_id = f"{turn_id}:step-{step_no}"
        current_step_closed = False
        return AgentLoopEvent(
            phase=AgentLoopPhase.STEP_START,
            turn_id=turn_id,
            step_id=current_step_id,
            step_no=step_no,
            run_id=run_id,
            name=node_name,
        )

    def end_step(reason: str) -> Optional[AgentLoopEvent]:
        """创建步骤结束事件；当前没有打开步骤时返回空。"""
        nonlocal current_step_closed
        if current_step_closed or not current_step_id:
            return None
        current_step_closed = True
        return AgentLoopEvent(
            phase=AgentLoopPhase.STEP_END,
            turn_id=turn_id,
            step_id=current_step_id,
            step_no=step_no,
            metadata={"reason": reason},
        )

    async def emit_loop_event(event: AgentLoopEvent) -> str:
        """持久化并编码一个 Agent Loop 事件。"""
        await _append_agent_loop_event(event, trace_ctx)
        return _agent_loop_sse(event)

    try:
        yield await emit_loop_event(
            AgentLoopEvent(
                phase=AgentLoopPhase.TURN_START,
                turn_id=turn_id,
                metadata={
                    "thread_id": thread_id,
                    "max_tool_rounds": max_tool_rounds,
                    "timeout_seconds": execution_timeout_seconds,
                },
            )
        )
        event_stream = agent_executor.astream_events(
            initial_state,
            config=config,
            version="v2",
        )
        async for event in stream_with_total_timeout(
            event_stream,
            execution_timeout_seconds,
        ):
            kind = event["event"]
            run_id = event.get("run_id", "")

            if kind == "on_chat_model_start":
                previous_step_end = end_step("next_llm_round")
                if previous_step_end:
                    yield await emit_loop_event(previous_step_end)
                latest_round_id = str(run_id)
                node_name = str(event.get("metadata", {}).get("langgraph_node") or "")
                yield await emit_loop_event(start_step(str(run_id), node_name))
                yield await emit_loop_event(
                    AgentLoopEvent(
                        phase=AgentLoopPhase.LLM_START,
                        turn_id=turn_id,
                        step_id=current_step_id,
                        step_no=step_no,
                        run_id=str(run_id),
                        name=str(event.get("name") or "LLM"),
                        metadata={"node_name": node_name},
                    )
                )
                # 规划节点输出的是供后端解析的 JSON，不属于执行说明或最终答案。
                # 前端只通过 plan_created 事件展示解析、持久化后的计划实体。
                suppress_output = planning_enabled and node_name == "create_task_plan"
                rounds[latest_round_id] = {
                    "text": [],
                    "node_name": node_name,
                    "suppress_output": suppress_output,
                }
                if not suppress_output:
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
                    round_info = rounds.setdefault(
                        round_key,
                        {"text": [], "node_name": "", "suppress_output": False},
                    )
                    if round_info.get("suppress_output"):
                        continue
                    round_info["text"].append(str(chunk.content))
                    yield sse_event("pending_text_delta", str(chunk.content), round_id=round_key)

            elif kind == "on_chat_model_end":
                output = event.get("data", {}).get("output")
                if trace_ctx:
                    usage = extract_token_usage(output)
                    await trace_ctx.on_llm_end(
                        run_id,
                        str(output or ""),
                        tokens=usage.total_tokens,
                    )
                yield await emit_loop_event(
                    AgentLoopEvent(
                        phase=AgentLoopPhase.LLM_END,
                        turn_id=turn_id,
                        step_id=current_step_id,
                        step_no=step_no,
                        run_id=str(run_id),
                        name=str(event.get("name") or "LLM"),
                        metadata={
                            "tokens": extract_token_usage(output).total_tokens,
                        },
                    )
                )

                # 完整输出包含工具调用时，本轮文本属于执行说明；否则属于正式回答。
                output_tool_calls = getattr(output, "tool_calls", None) if output else None
                round_key = str(run_id)
                round_info = rounds.setdefault(
                    round_key,
                    {"text": [], "node_name": "", "suppress_output": False},
                )
                if round_info.get("suppress_output"):
                    continue
                if not round_info["text"]:
                    fallback_text = _model_output_text(output)
                    if fallback_text:
                        round_info["text"].append(fallback_text)
                        yield sse_event(
                            "pending_text_delta",
                            fallback_text,
                            round_id=round_key,
                        )
                node_name = str(
                    event.get("metadata", {}).get("langgraph_node")
                    or round_info.get("node_name")
                    or ""
                )
                is_final_plan_answer = planning_enabled and node_name == "finalize_plan"
                yield sse_event(
                    "llm_round_classified",
                    round_id=round_key,
                    classification=(
                        "answer"
                        if is_final_plan_answer or (not planning_enabled and not output_tool_calls)
                        else "thinking"
                    ),
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
                yield await emit_loop_event(
                    AgentLoopEvent(
                        phase=AgentLoopPhase.TOOL_START,
                        turn_id=turn_id,
                        step_id=current_step_id,
                        step_no=step_no,
                        run_id=str(run_id),
                        name=str(tool_name),
                        metadata={"parent_round_id": latest_round_id},
                    )
                )
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
                yield await emit_loop_event(
                    AgentLoopEvent(
                        phase=AgentLoopPhase.TOOL_END,
                        turn_id=turn_id,
                        step_id=current_step_id,
                        step_no=step_no,
                        run_id=str(run_id),
                        name=str(tool_name),
                        metadata={"parent_round_id": latest_round_id},
                    )
                )
                yield sse_event(
                    "tool_completed", output_str, name=tool_name,
                    tool_run_id=str(run_id), parent_round_id=latest_round_id,
                )

            elif kind == "on_custom_event":
                event_name = str(event.get("name") or "")
                if event_name not in {
                    "plan_created",
                    "plan_step_started",
                    "plan_step_completed",
                    "plan_step_failed",
                    "plan_completed",
                }:
                    continue
                event_data = event.get("data")
                metadata = dict(event_data) if isinstance(event_data, Mapping) else {}
                content = str(metadata.pop("content", ""))
                yield sse_event(event_name, content, **metadata)

        final_step_end = end_step("turn_completed")
        if final_step_end:
            yield await emit_loop_event(final_step_end)
        yield await emit_loop_event(
            AgentLoopEvent(
                phase=AgentLoopPhase.TURN_END,
                turn_id=turn_id,
                metadata={"status": "completed"},
            )
        )
        yield sse_event("done")

    except AgentExecutionTimeoutError as exc:
        log.warning("[Stream] agent timeout: %s", exc)
        if trace_ctx:
            await trace_ctx.timeout(str(exc))
        timeout_step_end = end_step("timeout")
        if timeout_step_end:
            yield await emit_loop_event(timeout_step_end)
        yield await emit_loop_event(
            AgentLoopEvent(
                phase=AgentLoopPhase.TURN_TIMEOUT,
                turn_id=turn_id,
                metadata={
                    "status": "timeout",
                    "timeout_seconds": exc.timeout_seconds,
                    "error": str(exc),
                },
            )
        )
        yield sse_event(
            "error",
            str(exc),
            code="agent_timeout",
            timeout_seconds=exc.timeout_seconds,
        )
        yield sse_event("done")
    except Exception as exc:
        log.exception("[Stream] error: %s", exc)
        if trace_ctx:
            await trace_ctx.error(str(exc))
        error_step_end = end_step("error")
        if error_step_end:
            yield await emit_loop_event(error_step_end)
        yield await emit_loop_event(
            AgentLoopEvent(
                phase=AgentLoopPhase.TURN_ERROR,
                turn_id=turn_id,
                metadata={"status": "error", "error": str(exc)},
            )
        )
        yield sse_event("error", str(exc))
        yield sse_event("done")
