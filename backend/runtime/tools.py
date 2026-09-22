"""将本地 Python Runtime 暴露为 LangChain 结构化工具。"""

import json
from typing import List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ..config import PYTHON_RUNTIME_ENABLED
from ..services.runtime_service import execute_python_code
from .models import RuntimeContext


class ExecutePythonInput(BaseModel):
    """ExecutePython 工具提供给大模型的入参结构。

    大模型调用该工具时，会生成类似下面的参数：
    {
        "code": "import pandas as pd\n...",
        "input_file_ids": ["fb0901ac-..."],
        "timeout_seconds": 30
    }

    code 是需要执行的完整 Python 代码；input_file_ids 是用户已上传文件的
    逻辑 ID；timeout_seconds 是本次代码执行的超时时间。
    """

    code: str = Field(description="需要执行的完整 Python 代码")
    input_file_ids: List[str] = Field(
        default_factory=list,
        description="代码需要读取的 Runtime 文件 ID 列表",
    )
    timeout_seconds: int = Field(default=30, ge=1, le=30, description="执行超时秒数")


def build_runtime_tools(
    context: Optional[RuntimeContext],
) -> List[StructuredTool]:
    """根据运行上下文构建受限 Python 执行工具。

    Args:
        context: 当前聊天或工作流的用户、工作空间和链路上下文。

    Returns:
        Runtime关闭或缺少上下文时返回空列表，否则只返回 `ExecutePython`。
    """
    if not PYTHON_RUNTIME_ENABLED or context is None:
        return []

    async def execute_python(
        code: str,
        input_file_ids: Optional[List[str]] = None,
        timeout_seconds: int = 30,
    ) -> str:
        """ExecutePython 的实际处理函数，返回 JSON 字符串。

        Args:
            code: 需要在受限 Runtime 中执行的完整 Python 代码。
            input_file_ids: 本次代码需要读取的 Runtime 文件 ID 列表。
            timeout_seconds: 本次代码执行的超时秒数，最大为 30 秒。

        执行完成后的返回结构：
        {
            "executionId": "本次代码执行ID",
            "status": "completed | failed | timed_out",
            "exitCode": 0,
            "stdout": "print 等产生的标准输出",
            "stderr": "Python 错误输出",
            "error": "失败或超时原因，成功时为空字符串",
            "result": "被执行代码中 result 变量的值",
            "artifacts": [
                {
                    "fileId": "Runtime 生成文件的逻辑ID",
                    "name": "生成的文件名",
                    "mimeType": "文件 MIME 类型",
                    "size": "文件字节数",
                    "url": "需要携带登录凭证的下载地址"
                }
            ]
        }

        如果代码未进入子进程就被安全策略拒绝，则返回：
        {"status": "rejected", "error": "具体拒绝原因"}
        """
        try:
            result = await execute_python_code(
                context,
                code,
                input_file_ids=input_file_ids,
                timeout_seconds=timeout_seconds,
            )
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            return json.dumps({"status": "rejected", "error": str(exc)}, ensure_ascii=False)

    # ExecutePython 的结构：
    # - coroutine：大模型发起工具调用后，LangGraph 真正执行的函数。
    # - name：提供给大模型的工具名称。
    # - description：告诉大模型该工具的能力、使用方式和边界。
    # - args_schema：将 ExecutePythonInput 转换为大模型可见的 JSON 入参结构。
    # 下面返回的是可传给 create_react_agent(tools=...) 的工具列表，
    # 不是 ExecutePython 执行完成后的 JSON 数据。
    return [
        StructuredTool.from_function(
            coroutine=execute_python,
            name="ExecutePython",
            description=(
                "在受限的本地 Python Runtime 中执行代码。输入文件通过 INPUT_FILES 字典按文件 ID 获取，"
                "例如单文件时使用 file_path = next(iter(INPUT_FILES.values()))；"
                "不要猜测 /mnt/data 等文件路径。"
                "只允许向 OUTPUT_DIR 写文件；将最终 JSON 赋值给 result，生成文件写入 OUTPUT_DIR。"
            ),
            args_schema=ExecutePythonInput,
        ),
    ]
