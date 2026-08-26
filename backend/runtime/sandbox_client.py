"""独立 Sandbox Service 客户端。

Runtime Worker 不接触 Docker Socket，只把已准备好的任务交给专用沙箱服务执行。
"""

from typing import Dict

import httpx

from ..config import (
    SANDBOX_REQUEST_TIMEOUT_SECONDS,
    SANDBOX_SERVICE_TOKEN,
    SANDBOX_SERVICE_URL,
)


class SandboxServiceError(RuntimeError):
    """Sandbox Service 不可用或拒绝执行。"""


async def execute_in_sandbox(payload: Dict) -> Dict:
    """提交一次代码执行，并返回标准沙箱执行结果。"""
    timeout = max(
        SANDBOX_REQUEST_TIMEOUT_SECONDS,
        int(payload.get("timeoutSeconds") or 30) + 10,
    )
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{SANDBOX_SERVICE_URL}/v1/executions",
                json=payload,
                headers={"Authorization": f"Bearer {SANDBOX_SERVICE_TOKEN}"},
            )
    except httpx.HTTPError as exc:
        raise SandboxServiceError(f"无法连接 Sandbox Service：{exc}") from exc

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = response.text
        raise SandboxServiceError(f"Sandbox Service 拒绝执行：{detail or response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise SandboxServiceError("Sandbox Service 返回了无效 JSON") from exc
