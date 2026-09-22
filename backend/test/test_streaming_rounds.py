import json
import unittest
from typing import Any, AsyncIterator, Dict
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage, AIMessageChunk

from backend.core.streaming import sse_event, stream_agent_response
from backend.core.execution_control import AgentExecutionTimeoutError


def _decode_sse(raw_event) -> Dict[str, Any]:
    return json.loads(raw_event.removeprefix("data:").strip())


class _FakeAgent:
    async def astream_events(
        self,
        *_args,
        **_kwargs,
    ) -> AsyncIterator[Dict[str, Any]]:
        yield {"event": "on_chat_model_start", "run_id": "round-1", "name": "model", "data": {}}
        yield {
            "event": "on_chat_model_stream",
            "run_id": "round-1",
            "data": {"chunk": AIMessageChunk(content="我先查询天气。")},
        }
        yield {
            "event": "on_chat_model_end",
            "run_id": "round-1",
            "data": {"output": AIMessage(content="", tool_calls=[{"name": "weather", "args": {}, "id": "call-1"}])},
        }
        yield {"event": "on_tool_start", "run_id": "tool-1", "name": "weather", "data": {"input": {"city": "北京"}}}
        yield {"event": "on_tool_end", "run_id": "tool-1", "name": "weather", "data": {"output": "晴"}}
        yield {"event": "on_chat_model_start", "run_id": "round-2", "name": "model", "data": {}}
        yield {
            "event": "on_chat_model_stream",
            "run_id": "round-2",
            "data": {"chunk": AIMessageChunk(content="北京明天晴。")},
        }
        yield {
            "event": "on_chat_model_end",
            "run_id": "round-2",
            "data": {"output": AIMessage(content="北京明天晴。")},
        }


class _CapturingAgent:
    def __init__(self) -> None:
        self.initial_state = None

    async def astream_events(
        self,
        state,
        **_kwargs,
    ) -> AsyncIterator[Any]:
        """记录流式入口收到的 State，不产生模型事件。"""
        self.initial_state = state
        if False:
            yield None


class _FakePlannedAgent:
    """生成计划事件、步骤模型输出和最终汇总输出。"""

    async def astream_events(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """按真实外层规划图的事件顺序生成测试事件。"""
        yield {
            "event": "on_chat_model_start",
            "run_id": "planner-round",
            "name": "model",
            "metadata": {"langgraph_node": "create_task_plan"},
            "data": {},
        }
        yield {
            "event": "on_chat_model_stream",
            "run_id": "planner-round",
            "metadata": {"langgraph_node": "create_task_plan"},
            "data": {"chunk": AIMessageChunk(content='{"goal":"生成报告"}')},
        }
        yield {
            "event": "on_chat_model_end",
            "run_id": "planner-round",
            "metadata": {"langgraph_node": "create_task_plan"},
            "data": {"output": AIMessage(content='{"goal":"生成报告"}')},
        }
        yield {
            "event": "on_custom_event",
            "name": "plan_created",
            "data": {"plan": {"id": 1, "goal": "生成报告", "steps": []}},
        }
        yield {
            "event": "on_chat_model_start",
            "run_id": "step-round",
            "name": "model",
            "metadata": {"langgraph_node": "execute_plan_step"},
            "data": {},
        }
        yield {
            "event": "on_chat_model_stream",
            "run_id": "step-round",
            "data": {"chunk": AIMessageChunk(content="步骤结果")},
        }
        yield {
            "event": "on_chat_model_end",
            "run_id": "step-round",
            "metadata": {"langgraph_node": "execute_plan_step"},
            "data": {"output": AIMessage(content="步骤结果")},
        }
        yield {
            "event": "on_chat_model_start",
            "run_id": "final-round",
            "name": "model",
            "metadata": {"langgraph_node": "finalize_plan"},
            "data": {},
        }
        yield {
            "event": "on_chat_model_stream",
            "run_id": "final-round",
            "data": {"chunk": AIMessageChunk(content="最终报告")},
        }
        yield {
            "event": "on_chat_model_end",
            "run_id": "final-round",
            "metadata": {"langgraph_node": "finalize_plan"},
            "data": {"output": AIMessage(content="最终报告")},
        }


class StreamingRoundTests(unittest.IsolatedAsyncioTestCase):
    async def test_each_llm_round_is_classified_independently(self) -> None:
        events = []
        async for raw_event in stream_agent_response(_FakeAgent(), "天气", "session-1"):
            events.append(_decode_sse(raw_event))

        classifications = {
            event["round_id"]: event["classification"]
            for event in events
            if event["type"] == "llm_round_classified"
        }
        self.assertEqual(classifications, {"round-1": "thinking", "round-2": "answer"})

        tool_started = next(event for event in events if event["type"] == "tool_started")
        tool_completed = next(event for event in events if event["type"] == "tool_completed")
        self.assertEqual(tool_started["tool_run_id"], "tool-1")
        self.assertEqual(tool_completed["tool_run_id"], "tool-1")

        lifecycle_phases = [
            event["phase"]
            for event in events
            if event["type"] == "agent_loop_event"
        ]
        self.assertEqual(lifecycle_phases[0], "turn/start")
        self.assertIn("step/start", lifecycle_phases)
        self.assertIn("llm/start", lifecycle_phases)
        self.assertIn("tool/start", lifecycle_phases)
        self.assertIn("tool/end", lifecycle_phases)
        self.assertEqual(lifecycle_phases[-1], "turn/end")

    def test_sse_event_accepts_protocol_metadata(self) -> None:
        event = _decode_sse(sse_event("pending_text_delta", "文本", round_id="round-1"))
        self.assertEqual(event, {"type": "pending_text_delta", "content": "文本", "round_id": "round-1"})

    async def test_stream_injects_custom_business_state(self) -> None:
        """聊天流入口应将文件、Skill 和当前输入放入自定义 State。"""
        agent = _CapturingAgent()
        events = []
        async for raw_event in stream_agent_response(
            agent,
            "分析 Excel",
            "session-1",
            state_context={
                "runtime_file_ids": ["file-1"],
                "available_skills": ["Excel分析"],
                "current_node_id": "chat",
            },
        ):
            events.append(_decode_sse(raw_event))

        self.assertEqual(events[-1]["type"], "done")
        self.assertEqual(agent.initial_state["runtime_file_ids"], ["file-1"])
        self.assertEqual(agent.initial_state["available_skills"], ["Excel分析"])
        self.assertEqual(agent.initial_state["current_input"], "分析 Excel")
        self.assertEqual(agent.initial_state["current_node_id"], "chat")

    async def test_planned_agent_only_classifies_finalizer_as_answer(self) -> None:
        """计划步骤输出应进入执行说明，只有最终汇总进入正式回答。"""
        events = []
        async for raw_event in stream_agent_response(
            _FakePlannedAgent(),
            "生成报告",
            "planning-1",
            state_context={"planning_mode": "explicit"},
        ):
            events.append(_decode_sse(raw_event))

        classifications = {
            event["round_id"]: event["classification"]
            for event in events
            if event["type"] == "llm_round_classified"
        }
        self.assertEqual(
            classifications,
            {"step-round": "thinking", "final-round": "answer"},
        )
        visible_text = "".join(
            event.get("content", "")
            for event in events
            if event["type"] == "pending_text_delta"
        )
        self.assertNotIn('{"goal":"生成报告"}', visible_text)
        created = next(event for event in events if event["type"] == "plan_created")
        self.assertEqual(created["plan"]["goal"], "生成报告")

    async def test_agent_total_timeout_emits_specific_error(self) -> None:
        """Agent 达到整体时限时应产生可识别的超时事件并结束 Trace。"""
        trace_context = AsyncMock()

        async def timed_out_stream(
            event_stream: AsyncIterator[Dict[str, Any]],
            timeout_seconds: int,
        ) -> AsyncIterator[Dict[str, Any]]:
            """模拟通用执行控制器达到整体时限。"""
            del event_stream
            raise AgentExecutionTimeoutError(timeout_seconds)
            if False:
                yield {}

        with patch(
            "backend.core.streaming.stream_with_total_timeout",
            timed_out_stream,
        ):
            events = [
                _decode_sse(raw_event)
                async for raw_event in stream_agent_response(
                    _CapturingAgent(),
                    "生成报告",
                    "timeout-1",
                    execution_timeout_seconds=120,
                    trace_ctx=trace_context,
                )
            ]

        timeout_event = next(event for event in events if event["type"] == "error")
        self.assertEqual(timeout_event["code"], "agent_timeout")
        self.assertEqual(timeout_event["timeout_seconds"], 120)
        trace_context.timeout.assert_awaited_once()
        self.assertEqual(events[-1]["type"], "done")


if __name__ == "__main__":
    unittest.main()
