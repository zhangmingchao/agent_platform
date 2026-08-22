"""本地链路追踪处理器 —— 捕获智能体执行事件并写入 MySQL。"""
import logging
import time
from datetime import datetime
from typing import Dict, Optional

from ..database import execute

log = logging.getLogger("agent-platform")


class TraceContext:
    """管理单次追踪运行及其在智能体执行期间的 Span。"""

    def __init__(
        self,
        session_id: Optional[int],
        user_id: int,
        agent_id: int,
        model_name: str = "",
        workflow_run_id: Optional[int] = None,
        workflow_step_id: Optional[int] = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.model_name = model_name
        self.workflow_run_id = workflow_run_id
        self.workflow_step_id = workflow_step_id
        self.run_id = None
        self.spans: Dict[str, dict] = {}
        self.start_time = time.time()

    async def start(self, input_text: str):
        """在数据库中创建 trace_run 记录。"""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.run_id = await execute(
            "INSERT INTO trace_runs "
            "(session_id, user_id, agent_id, workflow_run_id, workflow_step_id, "
            "status, input_text, model, started_at, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                self.session_id,
                self.user_id,
                self.agent_id,
                self.workflow_run_id,
                self.workflow_step_id,
                "running",
                input_text[:5000],
                self.model_name,
                now,
                now,
            ),
        )
        log.info("[Trace] run #%s started (session=%s)", self.run_id, self.session_id)
        return self.run_id

    async def on_llm_start(self, run_id: str, name: str, input_data: str):
        """为 LLM 调用创建 trace_span。"""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        span_id = await execute(
            "INSERT INTO trace_spans (run_id, span_type, name, input_data, status, started_at, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (self.run_id, "llm", name or "LLM", input_data[:5000], "running", now, now),
        )
        self.spans[run_id] = {"span_id": span_id, "start": time.time()}

    async def on_llm_end(self, run_id: str, output: str, tokens: int = 0):
        """更新 Span 的输出和耗时。"""
        span = self.spans.get(run_id)
        if not span:
            return
        duration = int((time.time() - span["start"]) * 1000)
        await execute(
            "UPDATE trace_spans SET output_data=%s, tokens_used=%s, duration_ms=%s, status=%s WHERE id=%s",
            (output[:5000], tokens, duration, "success", span["span_id"]),
        )

    async def on_tool_start(self, run_id: str, name: str, input_data: str):
        """为工具调用创建 trace_span。"""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        span_id = await execute(
            "INSERT INTO trace_spans (run_id, span_type, name, input_data, status, started_at, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (self.run_id, "tool", name or "Tool", input_data[:5000], "running", now, now),
        )
        self.spans[run_id] = {"span_id": span_id, "start": time.time()}

    async def on_tool_end(self, run_id: str, output: str):
        """更新 Span 的输出和耗时。"""
        span = self.spans.get(run_id)
        if not span:
            return
        duration = int((time.time() - span["start"]) * 1000)
        await execute(
            "UPDATE trace_spans SET output_data=%s, duration_ms=%s, status=%s WHERE id=%s",
            (output[:5000], duration, "success", span["span_id"]),
        )

    async def finish(self, output_text: str, total_tokens: int = 0):
        """标记 trace_run 为已完成。"""
        duration = int((time.time() - self.start_time) * 1000)
        await execute(
            "UPDATE trace_runs SET status=%s, output_text=%s, total_tokens=%s, total_duration_ms=%s WHERE id=%s",
            ("success", output_text[:5000], total_tokens, duration, self.run_id),
        )
        log.info("[Trace] run #%s finished (%dms)", self.run_id, duration)

    async def error(self, error_msg: str):
        """标记 trace_run 为失败。"""
        duration = int((time.time() - self.start_time) * 1000)
        await execute(
            "UPDATE trace_runs SET status=%s, error_text=%s, total_duration_ms=%s WHERE id=%s",
            ("error", error_msg[:5000], duration, self.run_id),
        )
        log.info("[Trace] run #%s failed: %s", self.run_id, error_msg[:100])
