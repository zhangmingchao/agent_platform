"""调用 `bi-docker` 只读接口的异步客户端。"""

from __future__ import annotations

from typing import Any, Mapping, Optional

import httpx

from .models import BiApiRequest, BiCliExitCode, BiCliResult, BiCliSettings


_AUTHENTICATION_CODES = {401, 405, 406, 407, 408, 409}
_PERMISSION_CODES = {420, 1005, 4001}


class BiApiClient:
    """执行白名单 BI 请求并统一处理 HTTP 与业务错误。

    Attributes:
        settings: BI 服务地址、认证信息及执行限制。
        transport: HTTPX 传输实现，生产环境为空，测试时可注入 MockTransport。
    """

    def __init__(
        self,
        settings: BiCliSettings,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        """创建 BI API 客户端。

        Args:
            settings: BI 地址、只读 Token、超时和输出限制。
            transport: 测试或特殊网络环境使用的 HTTPX 传输实现。
        """
        self.settings = settings
        self.transport = transport

    def _headers(self, request: BiApiRequest) -> Mapping[str, str]:
        """构造请求头，Token 只停留在 HTTP 客户端边界。

        Args:
            request: 当前白名单请求，提供产品标识。

        Returns:
            包含认证 Token、产品标识及可选请求 ID 的只读映射。
        """
        headers = {
            "Accept": "application/json",
            "token": self.settings.access_token,
            "pk": request.product_key,
        }
        if self.settings.request_id:
            headers["X-Request-Id"] = self.settings.request_id
        return headers

    def _failure_from_status(
        self,
        request: BiApiRequest,
        message: str,
        *,
        http_status: int,
        upstream_code: Optional[int] = None,
    ) -> BiCliResult:
        """将 HTTP 或 `ResultModel.code` 转换成稳定的 CLI 错误。

        Args:
            request: 当前执行的白名单请求。
            message: 上游错误信息或本地兜底说明。
            http_status: 上游 HTTP 状态码。
            upstream_code: ``ResultModel.code`` 业务状态码。

        Returns:
            Agent 可稳定识别错误类别和重试属性的失败实体。
        """
        effective_code = upstream_code if upstream_code is not None else http_status
        if effective_code in _AUTHENTICATION_CODES or http_status == 401:
            exit_code = BiCliExitCode.UNAUTHENTICATED
            error_code = "UNAUTHENTICATED"
        elif effective_code in _PERMISSION_CODES or http_status == 403:
            exit_code = BiCliExitCode.PERMISSION_DENIED
            error_code = "PERMISSION_DENIED"
        elif http_status == 404:
            exit_code = BiCliExitCode.NOT_FOUND
            error_code = "NOT_FOUND"
        elif http_status == 429:
            exit_code = BiCliExitCode.RATE_LIMITED
            error_code = "RATE_LIMITED"
        else:
            exit_code = BiCliExitCode.UPSTREAM_ERROR
            error_code = "UPSTREAM_ERROR"
        return BiCliResult.failure(
            command_name=request.command_name,
            request_id=self.settings.request_id,
            exit_code=exit_code,
            error_code=error_code,
            message=message,
            retryable=http_status == 429 or http_status >= 500,
            http_status=http_status,
            upstream_code=upstream_code,
        )

    async def execute(self, request: BiApiRequest) -> BiCliResult:
        """执行一个已经过命令白名单校验的 BI 请求。

        Args:
            request: CLI 参数转换得到的只读 HTTP 请求实体。

        Returns:
            成功数据或标准化错误组成的强类型 CLI 结果。
        """
        self.settings.validate()
        url = f"{self.settings.base_url.rstrip('/')}{request.path}"
        try:
            async with httpx.AsyncClient(
                timeout=float(self.settings.timeout_seconds),
                transport=self.transport,
            ) as client:
                response = await client.request(
                    request.method.value,
                    url,
                    headers=self._headers(request),
                    params=list(request.query_items),
                    json=request.json_body,
                )
        except httpx.TimeoutException:
            return BiCliResult.failure(
                command_name=request.command_name,
                request_id=self.settings.request_id,
                exit_code=BiCliExitCode.UPSTREAM_ERROR,
                error_code="TIMEOUT",
                message=f"BI 接口调用超过 {self.settings.timeout_seconds} 秒",
                retryable=True,
            )
        except httpx.HTTPError as exc:
            return BiCliResult.failure(
                command_name=request.command_name,
                request_id=self.settings.request_id,
                exit_code=BiCliExitCode.UPSTREAM_ERROR,
                error_code="NETWORK_ERROR",
                message=f"BI 接口网络异常: {exc}",
                retryable=True,
            )

        if len(response.content) > self.settings.max_output_bytes:
            return BiCliResult.failure(
                command_name=request.command_name,
                request_id=self.settings.request_id,
                exit_code=BiCliExitCode.OUTPUT_TOO_LARGE,
                error_code="OUTPUT_TOO_LARGE",
                message=(
                    f"BI 接口响应为 {len(response.content)} 字节，超过 "
                    f"{self.settings.max_output_bytes} 字节限制，请缩小查询范围"
                ),
                http_status=response.status_code,
            )

        try:
            payload: Any = response.json()
        except ValueError:
            return self._failure_from_status(
                request,
                "BI 接口没有返回合法 JSON",
                http_status=response.status_code,
            )
        if not isinstance(payload, dict):
            return self._failure_from_status(
                request,
                "BI 接口返回结构不是 JSON 对象",
                http_status=response.status_code,
            )

        raw_upstream_code = payload.get("code")
        try:
            upstream_code = int(raw_upstream_code) if raw_upstream_code is not None else None
        except (TypeError, ValueError):
            upstream_code = None
        message = str(payload.get("msg") or payload.get("message") or "")
        if response.is_error or upstream_code not in (None, 200):
            return self._failure_from_status(
                request,
                message or f"BI 接口调用失败，HTTP {response.status_code}",
                http_status=response.status_code,
                upstream_code=upstream_code,
            )
        return BiCliResult.success(
            command_name=request.command_name,
            request_id=self.settings.request_id,
            data=payload.get("data"),
            message=message,
            http_status=response.status_code,
            upstream_code=upstream_code or 200,
            time_zone=(str(payload["timeZone"]) if payload.get("timeZone") is not None else None),
        )
