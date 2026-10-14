"""BI CLI 进程入口和统一 JSON 输出。"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Optional, Sequence

from ..config import (
    BI_CLI_MAX_OUTPUT_BYTES,
    BI_DOCKER_BASE_URL,
    BI_DOCKER_TIMEOUT_SECONDS,
    BI_DOCKER_TOKEN,
)
from .client import BiApiClient
from .commands import parse_bi_cli_command
from .errors import BiCliError
from .models import BiCliExitCode, BiCliResult, BiCliSettings


def _settings() -> BiCliSettings:
    """从服务端环境变量构建 CLI 配置实体。"""
    return BiCliSettings(
        base_url=BI_DOCKER_BASE_URL,
        access_token=BI_DOCKER_TOKEN,
        timeout_seconds=BI_DOCKER_TIMEOUT_SECONDS,
        max_output_bytes=BI_CLI_MAX_OUTPUT_BYTES,
        request_id=os.getenv("BI_CLI_REQUEST_ID", "").strip(),
    )


async def run(arguments: Sequence[str]) -> BiCliResult:
    """解析并执行一次 BI CLI 命令。

    Args:
        arguments: 不包含 `bi` 可执行文件名称的参数序列。

    Returns:
        可以直接输出给 Agent 的强类型执行结果。
    """
    settings = _settings()
    try:
        request = parse_bi_cli_command(arguments)
        settings.validate()
    except BiCliError as exc:
        failure = exc.failure
        return BiCliResult.failure(
            command_name="",
            request_id=settings.request_id,
            exit_code=failure.exit_code,
            error_code=failure.error_code,
            message=failure.message,
            retryable=failure.retryable,
        )
    except ValueError as exc:
        return BiCliResult.failure(
            command_name="",
            request_id=settings.request_id,
            exit_code=BiCliExitCode.CONFIGURATION_ERROR,
            error_code="CONFIGURATION_ERROR",
            message=str(exc),
        )
    return await BiApiClient(settings).execute(request)


def main(arguments: Optional[Sequence[str]] = None) -> int:
    """执行命令、打印单行 JSON 并返回标准退出码。

    Args:
        arguments: 测试或嵌入调用传入的参数；为空时读取 `sys.argv`。

    Returns:
        与 `BiCliResult.exit_code` 一致的进程退出码。
    """
    result = asyncio.run(run(list(arguments) if arguments is not None else sys.argv[1:]))
    print(result.to_json())
    return int(result.exit_code)
