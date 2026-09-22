"""Agent 整体执行时间控制。"""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from typing import TypeVar


EventType = TypeVar("EventType")


class AgentExecutionTimeoutError(TimeoutError):
    """表示一次 Agent 整体执行超过配置时限。

    Attributes:
        timeout_seconds: 当前 Agent 配置的整体执行时限。
    """

    def __init__(self, timeout_seconds: int) -> None:
        """创建 Agent 整体超时异常。

        Args:
            timeout_seconds: 本次 Agent 执行允许的最大秒数。
        """
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Agent 执行超过 {timeout_seconds} 秒，已自动终止")


async def stream_with_total_timeout(
    event_stream: AsyncIterator[EventType],
    timeout_seconds: int,
) -> AsyncGenerator[EventType, None]:
    """在一个共享截止时间内转发异步事件流。

    Args:
        event_stream: LangGraph 或其他执行器产生的异步事件流。
        timeout_seconds: 整个事件流允许执行的最大秒数。

    Yields:
        上游事件流按原顺序产生的事件。

    Raises:
        AgentExecutionTimeoutError: 整体执行时间达到上限。
    """
    timeout = max(1, int(timeout_seconds))
    event_iterator = event_stream.__aiter__()
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    try:
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise AgentExecutionTimeoutError(timeout)
            try:
                event = await asyncio.wait_for(anext(event_iterator), timeout=remaining)
            except StopAsyncIteration:
                break
            except TimeoutError as exc:
                # 工具自身抛出的 TimeoutError 发生在总截止时间之前时应保留原始语义。
                if loop.time() < deadline:
                    raise
                raise AgentExecutionTimeoutError(timeout) from exc
            yield event
    finally:
        close_stream = getattr(event_iterator, "aclose", None)
        if close_stream is not None:
            await close_stream()
