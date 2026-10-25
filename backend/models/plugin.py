"""插件定义、配置与诊断使用的强类型实体。"""

from datetime import datetime
from typing import Any, Literal, Optional
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, SerializeAsAny

ConfigValue = StrictStr | StrictInt | StrictBool | None


def validate_service_url(value: str) -> str:
    """校验 value 服务基础地址，禁止内嵌凭据、查询参数、片段和无效端口。"""
    value = value.strip().rstrip("/")
    if value:
        parsed = urlsplit(value)
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError("请输入 http/https 基础地址，不包含账号、查询参数或片段")
        try:
            parsed.port
        except ValueError as exc:
            raise ValueError("服务端口无效") from exc
    return value


class PluginField(BaseModel):
    """声明一个配置字段。

    key 为参数名，label 为显示名称，kind 决定控件类型，required 标记必填项。
    default 为默认值，minimum/maximum 为数字控件的上下界；max_length 限制文本长度。
    format 声明地址校验，placeholder 为输入提示，options 为枚举选项。
    """

    key: str
    label: str
    kind: Literal["string", "secret", "integer", "boolean", "select"]
    required: bool = False
    default: ConfigValue = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    max_length: int = Field(default=4096, ge=1, le=100000)
    format: Optional[Literal["url"]] = None
    placeholder: str = ""
    options: list["PluginFieldOption"] = Field(default_factory=list)


class PluginFieldOption(BaseModel):
    """枚举配置选项；label 为展示名称，value 为保存的字符串值。"""

    label: str
    value: str


class PluginCapabilities(BaseModel):
    """声明可展示的操作；connection_test、environment_import、debug 分别控制检测、导入和调试。"""

    connection_test: bool = False
    environment_import: bool = False
    debug: bool = False


class PluginManifest(BaseModel):
    """插件声明，作为内置目录、安装包和配置表单的共同数据源。

    id/name/version/description 分别为唯一标识、名称、版本和能力描述。
    source 为来源，executor 为服务端执行器标识，tools 为工具名称列表。
    skill_name/skill_files 指定配套技能名称与允许读取的文件路径。
    permissions 为能力权限声明，fields 为配置字段定义。
    capabilities 控制可选操作，test_fields 为检测参数，config_title 为配置标题。
    debug_panel 选择已注册的专用调试面板，默认使用通用 JSON 输入。
    """

    id: str
    name: str
    version: str
    description: str
    source: str
    executor: str
    tools: list[str]
    skill_name: Optional[str] = None
    skill_files: list[str] = Field(default_factory=list)
    permissions: list[str]
    fields: list[PluginField]
    capabilities: PluginCapabilities = Field(default_factory=PluginCapabilities)
    test_fields: list[PluginField] = Field(default_factory=list)
    config_title: str = "插件配置"
    debug_panel: Literal["generic", "bi-metadata"] = "generic"


class PluginConfigInput(BaseModel):
    """通用配置输入。

    values 为非敏感配置；secrets 为本次更新的密钥，空字符串保留旧值。
    clear_secrets 显式清除指定密钥，revision 为乐观锁版本。不接受历史 BI 扁平配置字段。
    """

    model_config = ConfigDict(extra="forbid")
    values: dict[str, ConfigValue] = Field(default_factory=dict)
    secrets: dict[str, str] = Field(default_factory=dict, repr=False)
    clear_secrets: list[str] = Field(default_factory=list)
    revision: int = Field(default=0, ge=0)



class PluginSettings(BaseModel):
    """已校验的执行配置；values 为普通配置，secrets 只在内存中解密且禁止 repr 回显。"""

    model_config = ConfigDict(frozen=True)
    values: dict[str, ConfigValue] = Field(default_factory=dict)
    secrets: dict[str, str] = Field(default_factory=dict, repr=False, exclude=True)


class PluginToggleInput(BaseModel):
    """插件启停请求；enabled 为期望状态，revision 为已读取的配置版本。"""

    enabled: bool
    revision: int = Field(ge=0)


class PluginProbeInput(BaseModel):
    """通用检测参数；parameters 按插件 test_fields 声明校验，由调用方明确提供 parameters 对象。"""

    model_config = ConfigDict(extra="forbid")
    parameters: dict[str, ConfigValue] = Field(default_factory=dict)



class PluginDebugInput(BaseModel):
    """通用调试参数；tool_name 指定声明中的工具，input 为其 Schema 参数，业务参数通过 input 对象提交。"""

    model_config = ConfigDict(extra="forbid")
    tool_name: Optional[str] = None
    input: dict[str, Any] = Field(default_factory=dict, repr=False)



class PluginToolDefinition(BaseModel):
    """工具公开定义；name 为名称，description 为描述，parameters 为参数 Schema，example_input 为可选示例。"""

    name: str
    description: str
    parameters: dict[str, Any]
    example_input: Optional[dict[str, Any]] = None


class PluginAgentSummary(BaseModel):
    """关联 Agent 摘要；id 用于跳转编辑，name 用于展示。"""

    id: int
    name: str


class PluginActivity(BaseModel):
    """脱敏操作记录。

    id 为分页游标，action 为操作类型，status 为执行状态，message 为安全摘要。
    duration_ms 为耗时毫秒数，agent_id/trace_run_id 关联调用方和追踪链路。
    created_at 为 UTC 创建时间。
    """

    id: int
    action: str
    status: str
    message: str
    duration_ms: int
    agent_id: Optional[int] = None
    trace_run_id: Optional[int] = None
    created_at: datetime


class PluginView(BaseModel):
    """插件公开视图，不返回任何形式的凭据。

    manifest 为插件声明，installed 表示当前用户存在安装版本，enabled 表示启用意图。
    config_values 为普通配置，configured_secrets 仅列出已保存密钥的字段名，revision 为乐观锁版本。
    config_status 表示无需配置/未配置/待完善/完整，health_status 和 health_message 为
    最近检测的状态及安全摘要，tested_at 为最近检测时间，updated_at 为配置更新时间。
    agents 为当前用户绑定此插件的 Agent 摘要列表。时间字段统一为 UTC。
    """

    manifest: SerializeAsAny[PluginManifest]
    installed: bool = False
    enabled: bool = False
    config_values: dict[str, ConfigValue] = Field(default_factory=dict)
    configured_secrets: list[str] = Field(default_factory=list)
    revision: int = 0
    config_status: str = "unconfigured"
    health_status: str = "untested"
    health_message: str = ""
    tested_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    agents: list[PluginAgentSummary] = Field(default_factory=list)
    # 包安装与配置保存是不同状态；内置/上传插件都必须为当前用户准备容器依赖。
    package_status: str = "not_installed"
    pending_version: Optional[str] = None
    package_error: str = ""


class PluginSkill(BaseModel):
    """只读插件技能文件；name 是技能名，path 是包内路径，content 是文件文本。"""

    name: str
    path: str
    content: str


class PluginOperationResult(BaseModel):
    """插件操作结果；ok 表示成功，message 为说明，result 为可选 CLI JSON 输出。"""

    ok: bool
    message: str
    duration_ms: int = 0
    result: Optional[str] = None
