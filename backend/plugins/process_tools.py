"""将上传声明转换为 LangChain 工具，调用体只向插件执行服务提交任务。"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool

from ..models.plugin import PluginSettings
from ..runtime.models import RuntimeContext
from .packages import ProcessManifest, ProcessToolDefinition, public_tool_name


def build_process_tools(context: RuntimeContext, manifest: ProcessManifest, settings: PluginSettings) -> list[StructuredTool]:
    """按 context 身份、manifest 版本与 settings 配置构建工具，Schema 完整保留嵌套和数组。"""
    def build(definition: ProcessToolDefinition) -> StructuredTool:
        """为 definition 创建独立闭包，避免多个工具错用名称和参数。"""
        async def execute(**arguments: Any) -> str:
            """将 arguments 交给执行服务，返回校验且脱敏的业务结果 JSON。"""
            from ..services.plugin_package_service import execute_process_plugin
            return await execute_process_plugin(context, manifest, definition.name, arguments, settings.values, settings.secrets)
        return StructuredTool.from_function(
            coroutine=execute,
            name=public_tool_name(manifest.id, definition.name),
            description=definition.description,
            args_schema=definition.parameters,
            metadata={"plugin_process": True, "risk_level": definition.risk_level},
        )
    return [build(definition) for definition in manifest.tool_definitions]
