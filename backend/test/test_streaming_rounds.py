import json
import unittest

from langchain_core.messages import AIMessage, AIMessageChunk

from backend.core.streaming import sse_event, stream_agent_response


def _decode_sse(raw_event):
    return json.loads(raw_event.removeprefix("data:").strip())


class _FakeAgent:
    async def astream_events(self, *_args, **_kwargs):
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
    def __init__(self):
        self.initial_state = None

    async def astream_events(self, state, **_kwargs):
        """记录流式入口收到的 State，不产生模型事件。"""
        self.initial_state = state
        if False:
            yield None


class StreamingRoundTests(unittest.IsolatedAsyncioTestCase):
    async def test_each_llm_round_is_classified_independently(self):
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

    def test_sse_event_accepts_protocol_metadata(self):
        event = _decode_sse(sse_event("pending_text_delta", "文本", round_id="round-1"))
        self.assertEqual(event, {"type": "pending_text_delta", "content": "文本", "round_id": "round-1"})

    async def test_stream_injects_custom_business_state(self):
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


if __name__ == "__main__":
    unittest.main()
