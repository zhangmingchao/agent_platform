"""链路追踪处理器：Run 汇总写 MySQL，Span 明细写 MongoDB。"""
import logging
import time
from datetime import datetime
from typing import Dict, Optional

from ..database import execute
from ..models.api_access import InvocationSource
from ..services.mongo_trace_service import create_trace_span, finish_trace_span

log = logging.getLogger(__name__)


class TraceContext:
    """管理单次追踪运行及其在智能体执行期间的 Span。

    Attributes:
        request_id: 对外暴露的一次请求唯一编号；平台聊天和工作流调用为空。
        run_id: ``trace_runs`` 表中的内部自增主键，创建 Trace 后写入。
        spans: 当前仍在执行的 Span，键为 LangChain 事件运行 ID。
        total_tokens: 当前 Trace 已完成的模型调用 Token 总数。
    """

    def __init__(
        self,
        session_id: Optional[int],
        user_id: int,
        agent_id: int,
        model_name: str = "",
        workflow_run_id: Optional[int] = None,
        workflow_step_id: Optional[int] = None,
        invocation_source: InvocationSource = InvocationSource.PLATFORM,
        request_id: Optional[str] = None,
        client_conversation_id: Optional[str] = None,
        parent_trace_run_id: Optional[int] = None,
    ) -> None:
        """初始化一次 Agent 调用链上下文。

        Args:
            parent_trace_run_id: 子 Agent 的父 Trace ID；顶层执行为空。
            session_id: 平台聊天会话 ID；API 和工作流调用可以为空。
            user_id: 本次调用所属的平台用户 ID。
            agent_id: 本次执行使用的 Agent ID。
            model_name: Trace 中展示的模型名称。
            workflow_run_id: 工作流运行 ID，普通聊天为空。
            workflow_step_id: 工作流步骤 ID，普通聊天为空。
            invocation_source: 调用来源，取值为 platform、api 或 workflow。
            request_id: 对外暴露的一次请求唯一编号，仅外部 API 调用使用。
            client_conversation_id: 外部调用方自己的会话关联标识。
        """
        # 子任务追踪记录关联父 Trace；各自 total_tokens 只计本执行，避免重复汇总。
        self.parent_trace_run_id = parent_trace_run_id
        self.session_id = session_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.model_name = model_name
        self.workflow_run_id = workflow_run_id
        self.workflow_step_id = workflow_step_id
        self.invocation_source = invocation_source
        self.request_id = request_id
        self.client_conversation_id = client_conversation_id
        self.run_id = None
        self.spans: Dict[str, dict] = {}
        self.start_time = time.time()
        self.total_tokens = 0

    async def start(self, input_text: str) -> Optional[int]:
        """在数据库中创建 trace_run 记录。"""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.run_id = await execute(
            "INSERT INTO trace_runs "
            "(session_id, user_id, agent_id, invocation_source, request_id, "
            "client_conversation_id, workflow_run_id, workflow_step_id, parent_trace_run_id, "
            "status, input_text, model, started_at, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                self.session_id,
                self.user_id,
                self.agent_id,
                self.invocation_source.value,
                self.request_id,
                self.client_conversation_id,
                self.workflow_run_id,
                self.workflow_step_id,
                self.parent_trace_run_id,
                "running",
                input_text[:5000],
                self.model_name,
                now,
                now,
            ),
        )
        log.info(
            "[Trace] run #%s started (source=%s request=%s session=%s)",
            self.run_id,
            self.invocation_source.value,
            self.request_id,
            self.session_id,
        )
        return self.run_id

    async def on_llm_start(self, run_id: str, name: str, input_data: str) -> None:
        """在 MongoDB 中创建 LLM Span。"""
        span_id = await create_trace_span(
            trace_run_id=self.run_id,
            user_id=self.user_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            workflow_run_id=self.workflow_run_id,
            workflow_step_id=self.workflow_step_id,
            event_run_id=run_id,
            span_type="llm",
            name=name or "LLM",
            input_data=input_data,
        )
        self.spans[run_id] = {"span_id": span_id, "start": time.time()}

    async def on_llm_end(self, run_id: str, output: str, tokens: int = 0) -> None:
        """更新 Span 的输出和耗时。"""
        span = self.spans.pop(run_id, None)
        if not span:
            return
        duration = int((time.time() - span["start"]) * 1000)
        self.total_tokens += max(0, tokens)
        await finish_trace_span(
            span["span_id"], output_data=output, tokens_used=tokens,
            duration_ms=duration, status="success",
        )

    async def on_tool_start(self, run_id: str, name: str, input_data: str) -> None:
        """在 MongoDB 中创建 Tool Span。"""
        span_id = await create_trace_span(
            trace_run_id=self.run_id,
            user_id=self.user_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            workflow_run_id=self.workflow_run_id,
            workflow_step_id=self.workflow_step_id,
            event_run_id=run_id,
            span_type="tool",
            name=name or "Tool",
            input_data=input_data,
        )
        self.spans[run_id] = {"span_id": span_id, "start": time.time()}

    async def on_tool_end(self, run_id: str, output: str) -> None:
        """更新 Span 的输出和耗时。"""
        span = self.spans.pop(run_id, None)
        if not span:
            return
        duration = int((time.time() - span["start"]) * 1000)
        await finish_trace_span(
            span["span_id"], output_data=output,
            duration_ms=duration, status="success",
        )

    async def finish(self, output_text: str, total_tokens: Optional[int] = None) -> None:
        """标记 trace_run 为已完成。"""
        duration = int((time.time() - self.start_time) * 1000)
        final_total_tokens = self.total_tokens if total_tokens is None else total_tokens
        await execute(
            "UPDATE trace_runs SET status=%s, output_text=%s, total_tokens=%s, total_duration_ms=%s WHERE id=%s",
            ("success", output_text[:5000], final_total_tokens, duration, self.run_id),
        )
        log.info("[Trace] run #%s finished (%dms)", self.run_id, duration)

    async def error(self, error_msg: str) -> None:
        """标记 trace_run 为执行失败。

        Args:
            error_msg: 导致 Agent 执行失败的错误信息。
        """
        await self._terminate("error", error_msg)

    async def cancelled(self, reason: str) -> None:
        """标记 trace_run 为用户取消。

        Args:
            reason: 用户停止生成或客户端断开连接的原因。
        """
        await self._terminate("cancelled", reason)

    async def timeout(self, error_msg: str) -> None:
        """标记 trace_run 为 Agent 整体执行超时。

        Args:
            error_msg: 包含配置时限的超时错误信息。
        """
        await self._terminate("timeout", error_msg)

    async def _terminate(self, status: str, error_msg: str) -> None:
        """使用指定终止状态结束 Trace Run 和活动 Span。

        Args:
            status: Trace 最终状态，取值为 error、cancelled 或 timeout。
            error_msg: 写入 Trace Run 和活动 Span 的错误说明。
        """
        duration = int((time.time() - self.start_time) * 1000)
        await execute(
            "UPDATE trace_runs SET status=%s, error_text=%s, total_duration_ms=%s WHERE id=%s",
            (status, error_msg[:5000], duration, self.run_id),
        )
        for span in list(self.spans.values()):
            await finish_trace_span(
                span["span_id"], duration_ms=int((time.time() - span["start"]) * 1000),
                status=status, error_text=error_msg,
            )
        self.spans.clear()
        log.info(
            "[Trace] run #%s terminated status=%s: %s",
            self.run_id,
            status,
            error_msg[:100],
        )
