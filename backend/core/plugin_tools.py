"""通用插件工具包装器，统一配置快照、脱敏和审计，再交由既有权限流水线执行。"""

from time import monotonic
from typing import Any

from langchain_core.tools import StructuredTool

from ..plugins.registry import get_manifest
from ..runtime.models import RuntimeContext
from ..services.plugin_service import RuntimePlugin, record_plugin_call, redacted_result


def build_plugin_tools(context: RuntimeContext, entries: list[RuntimePlugin]) -> list[StructuredTool]:
    """按 context 与 entries 独立配置构建插件工具，禁止跨插件工具名称或执行器串用。"""
    tools: list[StructuredTool] = []
    for entry in entries:
        manifest = entry.manifest or get_manifest(entry.plugin_id)
        from ..plugins.packages import ProcessManifest, public_tool_name
        from ..plugins.process_tools import build_process_tools
        built = build_process_tools(context, ProcessManifest.model_validate(manifest.model_dump()), entry.settings)
        expected = [public_tool_name(manifest.id, name) for name in manifest.tools]
        if sorted(tool.name for tool in built) != sorted(expected):
            raise ValueError(f"插件 {manifest.name} 的工具与声明不一致")
        for tool in built:
            tools.append(_wrap_plugin_tool(context, entry, tool))
    return tools


def _wrap_plugin_tool(context: RuntimeContext, entry: RuntimePlugin, tool: StructuredTool) -> StructuredTool:
    """为 context 中 entry 对应的 tool 绑定独立闭包，避免循环变量导致错用插件配置。"""
    async def execute(**arguments: Any) -> str:
        """执行 arguments 工具输入，返回脱敏结果并记录当前插件的安全摘要。"""
        started = monotonic()
        output = str(await tool.ainvoke(arguments))
        output = redacted_result(output, entry.manifest or get_manifest(entry.plugin_id), entry.settings)
        await record_plugin_call(context, output, int((monotonic() - started) * 1000), entry.plugin_id)
        return output

    return StructuredTool.from_function(coroutine=execute, name=tool.name, description=tool.description, args_schema=tool.args_schema, metadata=tool.metadata)
