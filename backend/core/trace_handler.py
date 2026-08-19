"""Local trace handler — captures agent execution events and writes to MySQL."""
import logging
import time
from datetime import datetime
from typing import Dict, Optional

from ..database import execute

log = logging.getLogger("agent-platform")


class TraceContext:
    """Manages a single trace run and its spans during agent execution."""

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
        """Create trace_run in DB."""
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
        """Create a trace_span for LLM call."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        span_id = await execute(
            "INSERT INTO trace_spans (run_id, span_type, name, input_data, status, started_at, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (self.run_id, "llm", name or "LLM", input_data[:5000], "running", now, now),
        )
        self.spans[run_id] = {"span_id": span_id, "start": time.time()}

    async def on_llm_end(self, run_id: str, output: str, tokens: int = 0):
        """Update span with output and duration."""
        span = self.spans.get(run_id)
        if not span:
            return
        duration = int((time.time() - span["start"]) * 1000)
        await execute(
            "UPDATE trace_spans SET output_data=%s, tokens_used=%s, duration_ms=%s, status=%s WHERE id=%s",
            (output[:5000], tokens, duration, "success", span["span_id"]),
        )

    async def on_tool_start(self, run_id: str, name: str, input_data: str):
        """Create a trace_span for tool call."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        span_id = await execute(
            "INSERT INTO trace_spans (run_id, span_type, name, input_data, status, started_at, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (self.run_id, "tool", name or "Tool", input_data[:5000], "running", now, now),
        )
        self.spans[run_id] = {"span_id": span_id, "start": time.time()}

    async def on_tool_end(self, run_id: str, output: str):
        """Update span with output and duration."""
        span = self.spans.get(run_id)
        if not span:
            return
        duration = int((time.time() - span["start"]) * 1000)
        await execute(
            "UPDATE trace_spans SET output_data=%s, duration_ms=%s, status=%s WHERE id=%s",
            (output[:5000], duration, "success", span["span_id"]),
        )

    async def finish(self, output_text: str, total_tokens: int = 0):
        """Mark trace_run as finished."""
        duration = int((time.time() - self.start_time) * 1000)
        await execute(
            "UPDATE trace_runs SET status=%s, output_text=%s, total_tokens=%s, total_duration_ms=%s WHERE id=%s",
            ("success", output_text[:5000], total_tokens, duration, self.run_id),
        )
        log.info("[Trace] run #%s finished (%dms)", self.run_id, duration)

    async def error(self, error_msg: str):
        """Mark trace_run as failed."""
        duration = int((time.time() - self.start_time) * 1000)
        await execute(
            "UPDATE trace_runs SET status=%s, error_text=%s, total_duration_ms=%s WHERE id=%s",
            ("error", error_msg[:5000], duration, self.run_id),
        )
        log.info("[Trace] run #%s failed: %s", self.run_id, error_msg[:100])
