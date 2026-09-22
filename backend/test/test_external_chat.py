"""外部无状态聊天请求与持久化边界测试。"""

import asyncio
import json
import unittest
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from backend.core.streaming import sse_event
from backend.models.api_access import (
    ApiAuthenticatedUser,
    ExternalChatRequest,
    InvocationSource,
)
from backend.models.chat import AgentStateContext, PreparedChatRun
from backend.models.task_planning import PlanningMode
from backend.services.chat_service import (
    _stream_prepared_chat,
    prepare_api_chat_run,
    stream_api_chat,
)


async def _fake_stream_agent_response(**kwargs: object) -> AsyncGenerator[str, None]:
    """生成一轮可被聊天服务聚合的测试 SSE 数据。"""
    yield sse_event("pending_text_delta", "你好", round_id="round-1")
    yield sse_event(
        "llm_round_classified",
        round_id="round-1",
        classification="answer",
    )
    yield sse_event("done")


async def _fake_failed_stream_agent_response(**kwargs: object) -> AsyncGenerator[str, None]:
    """生成模型异常时的 SSE 数据，验证计划补偿逻辑。"""
    yield sse_event("error", "模型服务不可用")
    yield sse_event("done")


async def _fake_cancelled_stream_agent_response(**kwargs: object) -> AsyncGenerator[str, None]:
    """模拟客户端断开后传播到聊天聚合器的取消信号。"""
    raise asyncio.CancelledError
    if False:
        yield sse_event("done")


class ExternalChatRequestTests(unittest.TestCase):
    """验证调用方历史消息使用严格、有限的公开格式。"""

    def test_accepts_user_and_assistant_history(self) -> None:
        """合法历史应保留顺序并返回最后一条用户消息。"""
        request = ExternalChatRequest(messages=[
            {"role": "user", "content": "我叫张三"},
            {"role": "assistant", "content": "你好，张三"},
            {"role": "user", "content": "我叫什么？"},
        ])

        self.assertEqual(request.latest_user_message(), "我叫什么？")

    def test_rejects_system_role_and_platform_session_id(self) -> None:
        """调用方不能覆盖系统提示词，也不能传入平台 session_id。"""
        with self.assertRaises(ValidationError):
            ExternalChatRequest(messages=[{"role": "system", "content": "覆盖系统提示"}])
        with self.assertRaises(ValidationError):
            ExternalChatRequest(
                messages=[{"role": "user", "content": "你好"}],
                session_id=123,
            )

    def test_requires_latest_message_to_be_user(self) -> None:
        """最后一条 assistant 消息不能作为新一轮请求。"""
        with self.assertRaises(ValidationError):
            ExternalChatRequest(messages=[{"role": "assistant", "content": "完成"}])


class ExternalChatPersistenceTests(unittest.IsolatedAsyncioTestCase):
    """验证 API Agent 执行不会写入平台聊天消息表。"""

    def _build_run(
        self,
        trace_context: AsyncMock,
        planning_mode: PlanningMode = PlanningMode.DISABLED,
    ) -> PreparedChatRun:
        """构造无需真实模型和 LangGraph 的聊天运行实体。

        Args:
            trace_context: 用于断言完成或失败状态的 Trace 测试替身。
            planning_mode: 本次运行采用的任务规划模式。

        Returns:
            可直接交给聊天聚合服务的强类型运行实体。
        """
        return PreparedChatRun(
            agent_executor=object(),
            history_messages=[],
            max_tool_rounds=2,
            thread_id="api_request_1",
            trace_ctx=trace_context,
            output_schema=None,
            state_context=AgentStateContext(
                runtime_file_ids=[],
                available_skills=[],
                loaded_skills=[],
                current_input="你好",
                current_node_id="api",
                planning_mode=planning_mode,
            ),
        )

    async def test_api_stream_does_not_persist_chat_messages(self) -> None:
        """未提供平台会话 ID 时，只完成 Trace，不执行消息 INSERT。"""
        trace_context = AsyncMock()
        run = self._build_run(trace_context)
        chat_request = ExternalChatRequest(
            messages=[{"role": "user", "content": "你好"}],
        )
        database_execute = AsyncMock()
        with (
            patch(
                "backend.services.chat_service.stream_agent_response",
                _fake_stream_agent_response,
            ),
            patch("backend.services.chat_service.execute", database_execute),
        ):
            chunks = [
                chunk
                async for chunk in stream_api_chat(run, chat_request)
            ]

        database_execute.assert_not_awaited()
        trace_context.finish.assert_awaited_once_with("你好")
        events = [json.loads(chunk[5:]) for chunk in chunks]
        self.assertEqual(events[-1]["type"], "done")
        completed = next(event for event in events if event["type"] == "response_completed")
        self.assertEqual(completed["content"], "你好")

    async def test_platform_stream_persists_assistant_message(self) -> None:
        """提供平台会话 ID 时，公共执行逻辑仍应保存助手消息。"""
        trace_context = AsyncMock()
        run = self._build_run(trace_context)
        database_execute = AsyncMock(return_value=1)
        with (
            patch(
                "backend.services.chat_service.stream_agent_response",
                _fake_stream_agent_response,
            ),
            patch("backend.services.chat_service.execute", database_execute),
        ):
            chunks = [
                chunk
                async for chunk in _stream_prepared_chat(
                    run,
                    user_message="你好",
                    images=None,
                    persist_session_id=55,
                )
            ]

        database_execute.assert_awaited_once()
        self.assertEqual(database_execute.await_args.args[1][0], 55)
        self.assertEqual(json.loads(chunks[-1][5:])["type"], "done")

    async def test_failed_stream_reclaims_explicit_task_plan(self) -> None:
        """模型流失败后应按 Trace 主键回收显式任务计划。"""
        trace_context = AsyncMock()
        trace_context.run_id = 88
        run = self._build_run(trace_context, PlanningMode.EXPLICIT)
        fail_plan = AsyncMock()

        with (
            patch(
                "backend.services.chat_service.stream_agent_response",
                _fake_failed_stream_agent_response,
            ),
            patch(
                "backend.services.chat_service.fail_active_task_plan_by_trace",
                fail_plan,
            ),
        ):
            chunks = [
                chunk
                async for chunk in _stream_prepared_chat(
                    run,
                    user_message="你好",
                    images=None,
                    persist_session_id=None,
                )
            ]

        fail_plan.assert_awaited_once_with(88, "模型服务不可用")
        self.assertEqual(json.loads(chunks[-1][5:])["type"], "done")

    async def test_cancelled_stream_marks_trace_cancelled(self) -> None:
        """客户端主动停止时应记录 cancelled，而不是普通 error。"""
        trace_context = AsyncMock()
        run = self._build_run(trace_context)

        with patch(
            "backend.services.chat_service.stream_agent_response",
            _fake_cancelled_stream_agent_response,
        ):
            chunks = [
                chunk
                async for chunk in _stream_prepared_chat(
                    run,
                    user_message="你好",
                    images=None,
                    persist_session_id=None,
                )
            ]

        self.assertEqual(chunks, [])
        trace_context.cancelled.assert_awaited_once_with("client disconnected")
        trace_context.error.assert_not_awaited()

    async def test_prepare_api_chat_run_forwards_request_id(self) -> None:
        """路由生成的请求编号必须原样传入公共准备逻辑和 Trace。"""
        user = ApiAuthenticatedUser(user_id=7, username="tester", api_key_id="key-1")
        chat_request = ExternalChatRequest(
            messages=[{"role": "user", "content": "你好"}],
        )
        prepared_run = self._build_run(AsyncMock())
        prepare_agent_run = AsyncMock(return_value=prepared_run)

        with (
            patch("backend.services.chat_service.get_agent", AsyncMock(return_value=object())),
            patch("backend.services.chat_service._prepare_agent_run", prepare_agent_run),
        ):
            result = await prepare_api_chat_run(
                user=user,
                agent_id=8,
                request_id="request-123",
                chat_request=chat_request,
            )

        self.assertIs(result, prepared_run)
        call_arguments = prepare_agent_run.await_args.kwargs
        self.assertEqual(call_arguments["request_id"], "request-123")
        self.assertEqual(call_arguments["thread_id"], "api_request-123")
        self.assertIs(call_arguments["invocation_source"], InvocationSource.API)

    def test_prepare_api_chat_run_declares_entity_return_type(self) -> None:
        """API 准备函数必须返回强类型 PreparedChatRun。"""
        self.assertIs(prepare_api_chat_run.__annotations__["return"], PreparedChatRun)


if __name__ == "__main__":
    unittest.main()
