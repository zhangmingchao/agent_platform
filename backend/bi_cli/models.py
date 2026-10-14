"""BI CLI 使用的强类型配置、请求和返回实体。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Mapping, Optional, Sequence, Tuple


class BiHttpMethod(str, Enum):
    """BI CLI 第一期允许使用的 HTTP 方法。"""

    GET = "GET"
    POST = "POST"


class BiCliExitCode(IntEnum):
    """BI CLI 进程退出码，便于 Agent 区分错误是否可恢复。"""

    SUCCESS = 0
    USAGE_ERROR = 2
    UNAUTHENTICATED = 3
    PERMISSION_DENIED = 4
    NOT_FOUND = 5
    RATE_LIMITED = 6
    UPSTREAM_ERROR = 7
    CONFIGURATION_ERROR = 8
    OUTPUT_TOO_LARGE = 9


@dataclass(frozen=True)
class BiCliSettings:
    """调用 `bi-docker` 所需的运行配置。

    Attributes:
        base_url: `bi-docker` HTTP 基础地址，可包含服务的 context-path。
        access_token: 只读 BI 账号的登录 Token。
        timeout_seconds: 单次 HTTP 请求允许的最大秒数。
        max_output_bytes: 上游响应允许进入模型上下文的最大字节数。
        request_id: 本次 Agent 请求的链路标识，用于跨系统排查问题。
    """

    base_url: str
    access_token: str
    timeout_seconds: int = 30
    max_output_bytes: int = 1024 * 1024
    request_id: str = ""

    def validate(self) -> None:
        """校验执行 CLI 所需配置，不返回松散字典。

        Raises:
            ValueError: 基础地址、Token 或数值范围无效。
        """
        normalized_url = self.base_url.strip().lower()
        if not normalized_url.startswith(("http://", "https://")):
            raise ValueError("BI_DOCKER_BASE_URL 必须是 http 或 https 地址")
        if not self.access_token.strip():
            raise ValueError("未配置 BI_DOCKER_TOKEN，无法调用 BI 接口")
        if self.timeout_seconds <= 0:
            raise ValueError("BI_DOCKER_TIMEOUT_SECONDS 必须大于 0")
        if self.max_output_bytes <= 0:
            raise ValueError("BI_CLI_MAX_OUTPUT_BYTES 必须大于 0")


@dataclass(frozen=True)
class BiApiRequest:
    """一个经过命令白名单转换后的 `bi-docker` 请求。

    Attributes:
        command_name: 稳定的 CLI 能力名称，用于输出和 Trace。
        method: 固定为第一期允许的 GET 或 POST。
        path: 相对于 `BI_DOCKER_BASE_URL` 的接口路径。
        product_key: 当前查询的产品标识，同时写入 `pk` 请求头。
        query_items: URL 查询参数；使用键值序列支持数组类型参数。
        json_body: POST 请求体；GET 请求保持为空。
    """

    command_name: str
    method: BiHttpMethod
    path: str
    product_key: str
    query_items: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)
    json_body: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class BiCliResult:
    """BI CLI 的统一结构化执行结果。

    Attributes:
        ok: 上游 HTTP 和业务状态是否都成功。
        command_name: 本次执行的稳定命令名称。
        request_id: 跨 `agent_platform` 与 `bi-docker` 的链路标识。
        exit_code: CLI 进程退出码。
        data: `ResultModel.data` 中的业务数据。
        message: 上游提示或本地错误说明。
        error_code: 稳定的 CLI 错误代码；成功时为空。
        retryable: Agent 是否可以在不修改业务参数的情况下重试。
        http_status: 上游 HTTP 状态码；请求未发出时为空。
        upstream_code: `bi-docker ResultModel.code`；无法解析时为空。
        time_zone: `bi-docker` 返回的数据时区。
    """

    ok: bool
    command_name: str
    request_id: str
    exit_code: BiCliExitCode
    data: Any = None
    message: str = ""
    error_code: str = ""
    retryable: bool = False
    http_status: Optional[int] = None
    upstream_code: Optional[int] = None
    time_zone: Optional[str] = None

    @classmethod
    def success(
        cls,
        command_name: str,
        request_id: str,
        data: Any,
        *,
        message: str = "",
        http_status: int = 200,
        upstream_code: int = 200,
        time_zone: Optional[str] = None,
    ) -> "BiCliResult":
        """创建一次成功结果。

        Args:
            command_name: 已执行的 CLI 能力名称。
            request_id: 本次跨系统请求标识。
            data: 上游返回的业务数据。
            message: 上游成功提示。
            http_status: 上游 HTTP 状态码。
            upstream_code: `ResultModel.code`。
            time_zone: 上游返回的数据时区。

        Returns:
            可序列化为 CLI JSON 的成功实体。
        """
        return cls(
            ok=True,
            command_name=command_name,
            request_id=request_id,
            exit_code=BiCliExitCode.SUCCESS,
            data=data,
            message=message,
            http_status=http_status,
            upstream_code=upstream_code,
            time_zone=time_zone,
        )

    @classmethod
    def failure(
        cls,
        command_name: str,
        request_id: str,
        exit_code: BiCliExitCode,
        error_code: str,
        message: str,
        *,
        retryable: bool = False,
        http_status: Optional[int] = None,
        upstream_code: Optional[int] = None,
    ) -> "BiCliResult":
        """创建一次失败结果。

        Args:
            command_name: 执行失败的 CLI 能力名称；解析前失败时可为空。
            request_id: 本次跨系统请求标识。
            exit_code: 进程应该返回的标准退出码。
            error_code: 供 Agent 判断错误类别的稳定代码。
            message: 面向用户和模型的中文错误说明。
            retryable: 相同参数是否允许重试。
            http_status: 上游 HTTP 状态码。
            upstream_code: `ResultModel.code`。

        Returns:
            可序列化为 CLI JSON 的失败实体。
        """
        return cls(
            ok=False,
            command_name=command_name,
            request_id=request_id,
            exit_code=exit_code,
            message=message,
            error_code=error_code,
            retryable=retryable,
            http_status=http_status,
            upstream_code=upstream_code,
        )

    def to_mapping(self) -> Mapping[str, Any]:
        """转换为 CLI 输出边界使用的 JSON 兼容结构。"""
        return {
            "ok": self.ok,
            "command": self.command_name,
            "requestId": self.request_id,
            "data": self.data,
            "message": self.message,
            "error": (
                {
                    "code": self.error_code,
                    "retryable": self.retryable,
                }
                if not self.ok
                else None
            ),
            "metadata": {
                "httpStatus": self.http_status,
                "upstreamCode": self.upstream_code,
                "timeZone": self.time_zone,
            },
        }

    def to_json(self) -> str:
        """序列化为标准输出使用的单行 JSON。"""
        return json.dumps(self.to_mapping(), ensure_ascii=False, separators=(",", ":"), default=str)


def compact_query_items(items: Sequence[Tuple[str, Any]]) -> Tuple[Tuple[str, Any], ...]:
    """移除值为空的查询参数，并保留数组参数的重复键能力。

    Args:
        items: 命令转换阶段生成的查询参数序列。

    Returns:
        可以直接交给 HTTPX 的不可变键值序列。
    """
    return tuple((name, value) for name, value in items if value is not None and value != "")
