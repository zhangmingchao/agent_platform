"""将本地 Python Runtime 暴露为 LangChain 结构化工具。"""

import json
from typing import Dict, List, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ..config import PYTHON_RUNTIME_ENABLED
from ..services.runtime_service import execute_python_code, resolve_skill_script
from .models import RuntimeContext


class ExecutePythonInput(BaseModel):
    """LLM 生成代码执行工具的输入。"""

    code: str = Field(description="需要执行的完整 Python 代码")
    input_file_ids: List[str] = Field(
        default_factory=list,
        description="代码需要读取的 Runtime 文件 ID 列表",
    )
    timeout_seconds: int = Field(default=60, ge=1, le=120, description="执行超时秒数")


class RunSkillScriptInput(BaseModel):
    """Skill 固定脚本执行工具的输入。"""

    skill_name: str = Field(description="已经激活的 Skill 名称")
    script_path: str = Field(description="Skill 目录内的 .py 脚本相对路径")
    arguments: Dict = Field(default_factory=dict, description="通过 RUNTIME_ARGS 传给脚本的参数")
    input_file_ids: List[str] = Field(
        default_factory=list,
        description="脚本需要读取的 Runtime 文件 ID 列表",
    )
    timeout_seconds: int = Field(default=60, ge=1, le=120, description="执行超时秒数")


def build_runtime_tools(
    skills: List[Dict],
    context: Optional[RuntimeContext],
) -> List[StructuredTool]:
    """根据运行上下文构建通用 Python 和 Skill 脚本工具。"""
    if not PYTHON_RUNTIME_ENABLED or context is None:
        return []

    skills_map = {skill["name"]: skill for skill in skills}

    async def execute_python(
        code: str,
        input_file_ids: Optional[List[str]] = None,
        timeout_seconds: int = 60,
    ) -> str:
        """执行模型生成代码并将结构化执行结果返回给模型。"""
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

    async def run_skill_script(
        skill_name: str,
        script_path: str,
        arguments: Optional[Dict] = None,
        input_file_ids: Optional[List[str]] = None,
        timeout_seconds: int = 60,
    ) -> str:
        """执行指定 Skill 中经过路径校验的 Python 脚本。"""
        skill = skills_map.get(skill_name)
        if not skill:
            return json.dumps({"status": "rejected", "error": "Skill 不存在或未绑定到 Agent"}, ensure_ascii=False)
        try:
            path = resolve_skill_script(skill["id"], script_path)
            result = await execute_python_code(
                context,
                path.read_text(encoding="utf-8"),
                input_file_ids=input_file_ids,
                timeout_seconds=timeout_seconds,
                source_type="skill_script",
                skill_id=skill["id"],
                arguments=arguments,
            )
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            return json.dumps({"status": "rejected", "error": str(exc)}, ensure_ascii=False)

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
        StructuredTool.from_function(
            coroutine=run_skill_script,
            name="RunSkillScript",
            description=(
                "执行已激活 Skill 包内的 Python 脚本。脚本通过 INPUT_FILES、OUTPUT_DIR 和 "
                "RUNTIME_ARGS 获取输入，不允许执行未绑定 Skill 的脚本。"
            ),
            args_schema=RunSkillScriptInput,
        ),
    ]
