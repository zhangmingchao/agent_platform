"""受信任执行器注册表；插件差异集中在适配器，管理服务不再解释 BI 字段。"""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .. import config
from ..bi_cli.commands import parse_bi_cli_command
from ..bi_cli.errors import BiCliError
from ..bi_cli.models import BiCliSettings
from ..core.bi_cli_tool import _validate_arguments, build_bi_cli_tools
from ..models.plugin import PluginDebugInput, PluginSettings, PluginToolDefinition
from ..runtime.models import RuntimeContext


class JsonFormatInput(BaseModel):
    """JSON 工具参数；content 为原文，indent 为缩进空格数（0 表示压缩），sort_keys 控制键排序。"""

    model_config = ConfigDict(extra="forbid")
    content: str = Field(max_length=200000, description="待校验和格式化的 JSON 文本")
    indent: int = Field(default=2, ge=0, le=8, description="缩进空格数，0 表示压缩输出")
    sort_keys: bool = Field(default=False, description="是否按键名称排序")


class PluginExecutor:
    """插件执行器契约，统一声明工具、验证执行配置、诊断和可选环境导入。"""

    def validate(self, settings: PluginSettings) -> None:
        """验证 settings 的执行器特定约束，通用字段校验由配置模块完成。"""

    def build_tools(self, context: Optional[RuntimeContext], settings: PluginSettings) -> list[StructuredTool]:
        """按 context 运行上下文及 settings 配置生成固定白名单工具。"""
        raise NotImplementedError

    def definitions(self) -> list[PluginToolDefinition]:
        """读取工具 Schema，不执行工具或连接外部服务。"""
        return [PluginToolDefinition(name=tool.name, description=tool.description, parameters=tool.args_schema.model_json_schema())
                for tool in self.build_tools(None, PluginSettings())]

    async def debug(self, settings: PluginSettings, request: PluginDebugInput) -> str:
        """按 settings 执行 request 指定工具，参数只按对应工具的 Schema 校验。"""
        tools = self.build_tools(None, settings)
        name = request.tool_name or (tools[0].name if len(tools) == 1 else None)
        tool = next((tool for tool in tools if tool.name == name), None)
        if tool is None:
            raise ValueError("工具未在此插件中声明")
        try:
            arguments = tool.args_schema.model_validate(request.input).model_dump()
        except ValidationError as exc:
            raise ValueError("工具参数无效，请按工具 Schema 填写") from exc
        return str(await tool.ainvoke(arguments))

    async def probe(self, settings: PluginSettings, parameters: PluginSettings) -> str:
        """使用 settings 与 parameters 检测连接；未实现检测的执行器拒绝调用。"""
        raise ValueError("此插件不支持连接检测")

    def environment(self) -> PluginSettings:
        """读取此执行器支持的服务器环境配置；未声明支持时不开放导入。"""
        raise ValueError("此插件不支持环境配置导入")


class BiCliExecutor(PluginExecutor):
    """BI CLI 适配器，负责字段映射、命令白名单、产品权限检测和环境导入。"""

    def bi_settings(self, settings: PluginSettings) -> BiCliSettings:
        """将 settings 映射为 BI CLI 的强类型执行配置，不回显 Token。"""
        return BiCliSettings(
            base_url=str(settings.values.get("base_url") or ""), access_token=settings.secrets.get("token", ""),
            timeout_seconds=int(settings.values.get("timeout_seconds") or 30),
            max_output_bytes=int(settings.values.get("max_output_bytes") or 1048576),
        )

    def validate(self, settings: PluginSettings) -> None:
        """验证 settings 的 BI 地址、凭据及限制。"""
        self.bi_settings(settings).validate()

    def build_tools(self, context: Optional[RuntimeContext], settings: PluginSettings) -> list[StructuredTool]:
        """按 context/settings 构建 BiCli；插件审计由公共包装器负责，避免重复记录。"""
        return build_bi_cli_tools(context or RuntimeContext(user_id=0), self.bi_settings(settings), record_activity=False)

    async def debug(self, settings: PluginSettings, request: PluginDebugInput) -> str:
        """验证 request 的固定 CLI 命令后按 settings 执行，不接受帮助或 Shell 命令。"""
        try:
            arguments = _validate_arguments(request.input.get("arguments", []))
            if any(value in ("-h", "--help") for value in arguments):
                raise ValueError("不支持帮助命令")
            parse_bi_cli_command(arguments)
        except (ValueError, TypeError, BiCliError) as exc:
            raise ValueError("CLI 参数无效，请检查命令和必填参数") from exc
        return await super().debug(settings, request)

    async def probe(self, settings: PluginSettings, parameters: PluginSettings) -> str:
        """以 settings 执行 parameters 中产品的第一页单条只读查询。"""
        return await self.debug(settings, PluginDebugInput(tool_name="BiCli", input={"arguments": [
            "metadata", "events", "list", "--product-key", parameters.values["product_key"],
            "--page-num", "1", "--page-size", "1",
        ]}))

    def environment(self) -> PluginSettings:
        """读取 BI 环境变量为通用实体，只有用户显式导入时调用。"""
        return PluginSettings(values={"base_url": config.BI_DOCKER_BASE_URL,
                                      "timeout_seconds": config.BI_DOCKER_TIMEOUT_SECONDS,
                                      "max_output_bytes": config.BI_CLI_MAX_OUTPUT_BYTES},
                              secrets={"token": config.BI_DOCKER_TOKEN})


class LocalJsonExecutor(PluginExecutor):
    """本地 JSON 执行器，不访问网络，不需要服务配置或凭据。"""

    def definitions(self) -> list[PluginToolDefinition]:
        """返回工具 Schema 及可直接运行的示例输入，业务示例不写入通用页面代码。"""
        definitions = super().definitions()
        definitions[0].example_input = {"content": '{"name":"example","count":1}', "indent": 2, "sort_keys": False}
        return definitions

    def build_tools(self, context: Optional[RuntimeContext], settings: PluginSettings) -> list[StructuredTool]:
        """返回本地 JsonFormat 工具；context/settings 为统一协议参数，此执行器无需使用。"""
        async def format_json(content: str, indent: int = 2, sort_keys: bool = False) -> str:
            """解析 content，按 indent 缩进并依据 sort_keys 排序；标准库解析器不执行输入代码。"""
            try:
                parsed = json.loads(content)
                formatted = json.dumps(parsed, ensure_ascii=False, indent=indent or None,
                                       separators=(",", ":") if indent == 0 else None, sort_keys=sort_keys, allow_nan=False)
                return json.dumps({"ok": True, "data": {"formatted": formatted}, "message": "JSON 处理成功"}, ensure_ascii=False)
            except (ValueError, RecursionError, OverflowError):
                return json.dumps({"ok": False, "data": None, "error": {"code": "INVALID_JSON"}, "message": "JSON 文本无效"}, ensure_ascii=False)

        return [StructuredTool.from_function(coroutine=format_json, name="JsonFormat",
                                            description="在本地校验、格式化或压缩 JSON 文本，不访问网络。", args_schema=JsonFormatInput)]


_EXECUTORS: dict[str, PluginExecutor] = {"bi-cli": BiCliExecutor(), "local-json": LocalJsonExecutor()}


def get_executor(name: str) -> PluginExecutor:
    """按 name 获取代码中固定注册的执行器，禁止从清单动态导入任意模块。"""
    if name not in _EXECUTORS:
        raise ValueError("插件执行器未注册")
    return _EXECUTORS[name]
