"""将受控 BI CLI 暴露为 LangChain 结构化工具。"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ..bi_cli.models import BiCliExitCode, BiCliResult
from ..config import (
    BI_CLI_ENABLED,
    BI_CLI_MAX_OUTPUT_BYTES,
    BI_DOCKER_TIMEOUT_SECONDS,
)
from ..runtime.models import RuntimeContext


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_FORBIDDEN_ARGUMENT_FRAGMENTS = (";", "|", "&&", "||", ">", "<", "`", "$(", "\n", "\r", "\x00")


class BiCliInput(BaseModel):
    """Agent 调用受控 BI CLI 时使用的参数实体。

    Attributes:
        arguments: 不包含 `bi` 程序名的参数数组，例如
            `["metadata", "events", "list", "--product-key", "app_001"]`。
    """

    arguments: List[str] = Field(
        description=(
            "BI CLI 参数数组，不包含可执行文件名。只支持 metadata 下的 "
            "analysis-bodies、events、user-properties、event-properties、metrics 列表命令"
        )
    )


@dataclass(frozen=True)
class BiCliProcessResult:
    """受控 BI CLI 子进程的标准输出结果。

    Attributes:
        exit_code: BI CLI 返回的退出码。
        stdout: CLI 的单行 JSON 标准输出。
        stderr: 进程启动或参数解析错误，正常执行时为空。
    """

    exit_code: int
    stdout: str
    stderr: str = ""


def _validate_arguments(arguments: List[str]) -> List[str]:
    """校验模型提供的 CLI 参数，不允许扩展为任意 Shell 命令。

    Args:
        arguments: 模型通过 `BiCli` Tool Call 提交的参数数组。

    Returns:
        完成长度和危险字符校验的参数副本。

    Raises:
        ValueError: 参数为空、数量过多、内容过长或包含 Shell 控制符。
    """
    if not arguments:
        raise ValueError("BiCli arguments 不能为空")
    if len(arguments) > 32:
        raise ValueError("BiCli arguments 数量不能超过 32")
    normalized: List[str] = []
    total_length = 0
    for value in arguments:
        if not isinstance(value, str):
            raise ValueError("BiCli arguments 中的每一项都必须是字符串")
        if len(value) > 500:
            raise ValueError("BiCli 单个参数长度不能超过 500")
        if any(fragment in value for fragment in _FORBIDDEN_ARGUMENT_FRAGMENTS):
            raise ValueError("BiCli 参数包含不允许的 Shell 控制符")
        total_length += len(value)
        normalized.append(value)
    if total_length > 4096:
        raise ValueError("BiCli 参数总长度不能超过 4096")
    return normalized


async def _execute_bi_cli_process(
    arguments: List[str],
    request_id: str,
) -> BiCliProcessResult:
    """使用参数数组启动固定 BI CLI 模块，始终禁用 Shell 解析。

    Args:
        arguments: 已完成白名单前置校验的 CLI 参数数组。
        request_id: 当前 Agent Trace 对应的跨系统请求标识。

    Returns:
        包含退出码和标准输出的强类型进程结果。
    """
    environment = dict(os.environ)
    environment["BI_CLI_REQUEST_ID"] = request_id
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "backend.bi_cli",
        *arguments,
        cwd=str(_PROJECT_ROOT),
        env=environment,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(),
            timeout=BI_DOCKER_TIMEOUT_SECONDS + 5,
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return BiCliProcessResult(
            exit_code=int(BiCliExitCode.UPSTREAM_ERROR),
            stdout=BiCliResult.failure(
                command_name="",
                request_id=request_id,
                exit_code=BiCliExitCode.UPSTREAM_ERROR,
                error_code="TIMEOUT",
                message="BI CLI 执行超时",
                retryable=True,
            ).to_json(),
        )
    return BiCliProcessResult(
        exit_code=int(process.returncode or 0),
        stdout=stdout_bytes.decode("utf-8", errors="replace").strip(),
        stderr=stderr_bytes.decode("utf-8", errors="replace").strip(),
    )


def _process_output(result: BiCliProcessResult, request_id: str) -> str:
    """规范化子进程输出，避免超大或非 JSON 内容进入模型上下文。

    Args:
        result: CLI 子进程返回的强类型结果。
        request_id: 当前 Agent 请求标识。

    Returns:
        保证为 JSON 对象字符串的 ToolMessage 内容。
    """
    output_bytes = result.stdout.encode("utf-8")
    if len(output_bytes) > BI_CLI_MAX_OUTPUT_BYTES:
        return BiCliResult.failure(
            command_name="",
            request_id=request_id,
            exit_code=BiCliExitCode.OUTPUT_TOO_LARGE,
            error_code="OUTPUT_TOO_LARGE",
            message="BI CLI 输出超过平台限制，请缩小查询范围",
        ).to_json()
    if result.stdout:
        try:
            parsed = json.loads(result.stdout)
            if isinstance(parsed, dict):
                return result.stdout
        except json.JSONDecodeError:
            pass
    error_text = result.stderr[:500] if result.stderr else "BI CLI 没有返回有效 JSON"
    return BiCliResult.failure(
        command_name="",
        request_id=request_id,
        exit_code=BiCliExitCode.UPSTREAM_ERROR,
        error_code="CLI_PROCESS_ERROR",
        message=f"{error_text} (exit_code={result.exit_code})",
    ).to_json()


def build_bi_cli_tools(context: Optional[RuntimeContext]) -> List[StructuredTool]:
    """按配置构建只读 BI CLI 工具。

    Args:
        context: 当前 Agent 的用户、会话和 Trace 上下文。

    Returns:
        未启用或缺少运行上下文时返回空列表，否则返回唯一的 `BiCli` 工具。
    """
    if not BI_CLI_ENABLED or context is None:
        return []

    async def execute_bi_cli(arguments: List[str]) -> str:
        """执行固定 BI CLI，并将结构化结果作为 ToolMessage 返回。

        Args:
            arguments: 模型提交的 BI CLI 参数数组，不包含程序名称。

        Returns:
            统一的单行 JSON 工具结果。
        """
        try:
            validated_arguments = _validate_arguments(arguments)
        except ValueError as exc:
            return BiCliResult.failure(
                command_name="",
                request_id="",
                exit_code=BiCliExitCode.USAGE_ERROR,
                error_code="INVALID_ARGUMENTS",
                message=str(exc),
            ).to_json()
        trace_ctx = context.trace_ctx
        request_id = ""
        if trace_ctx is not None:
            request_id = str(trace_ctx.request_id or f"trace-{trace_ctx.run_id or 'pending'}")
        result = await _execute_bi_cli_process(validated_arguments, request_id)
        return _process_output(result, request_id)

    return [
        StructuredTool.from_function(
            coroutine=execute_bi_cli,
            name="BiCli",
            description=(
                "通过受控 BI CLI 查询分析主体、事件、用户属性、事件属性和指标列表。"
                "仅支持只读 metadata 命令，参数必须以字符串数组传入；"
                "使用前应先读取 BI 元数据 Skill。"
            ),
            args_schema=BiCliInput,
        )
    ]
