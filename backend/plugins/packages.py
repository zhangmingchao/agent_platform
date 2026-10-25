"""Python 插件包协议与纯文件校验；不导入、不执行上传的 Python 代码。"""

from __future__ import annotations

import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ..models.plugin import PluginDebugInput, PluginManifest, PluginSettings, PluginToolDefinition


class ProcessToolDefinition(PluginToolDefinition):
    """进程工具契约；output_schema 校验成功业务数据，risk_level 为申请的调用风险。"""

    output_schema: dict[str, Any]
    risk_level: str = "medium"


class ProcessProbe(BaseModel):
    """连接检测声明；tool_name 为已有工具，arguments_template 用 {{参数名}} 引用检测输入。"""

    model_config = ConfigDict(extra="forbid")
    tool_name: str = Field(description="执行检测的包内工具名称")
    arguments_template: dict[str, Any] = Field(description="业务参数 JSON 模板，仅完整占位值替换检测参数")

    def parameter_keys(self) -> set[str]:
        """返回模板引用的检测字段名，安装时验证声明，执行时再按工具 Schema 校验真实值。"""
        def collect(value: Any) -> set[str]:
            """收集 value 中的完整占位符，保留普通字符串常量。"""
            if isinstance(value, str) and re.fullmatch(r"\{\{[a-zA-Z][a-zA-Z0-9_]*\}\}", value):
                return {value[2:-2]}
            children = value.values() if isinstance(value, dict) else value if isinstance(value, list) else []
            return {key for child in children for key in collect(child)}
        return collect(self.arguments_template)

    def request(self, parameters: PluginSettings) -> PluginDebugInput:
        """按 parameters 生成标准工具请求实体，模板值保留原始 JSON 类型。"""
        def expand(value: Any) -> Any:
            """递归替换 value 中完整的检测参数占位符。"""
            if isinstance(value, str) and re.fullmatch(r"\{\{[a-zA-Z][a-zA-Z0-9_]*\}\}", value):
                key = value[2:-2]
                if key not in parameters.values:
                    raise ValueError("连接检测缺少模板参数")
                return parameters.values[key]
            if isinstance(value, dict):
                return {key: expand(child) for key, child in value.items()}
            if isinstance(value, list):
                return [expand(child) for child in value]
            return value
        return PluginDebugInput(tool_name=self.tool_name, input=expand(self.arguments_template))


class ProcessManifest(PluginManifest):
    """可分发包声明。

    protocol_version 为进程协议版本；entrypoint 为包内 Python 入口。
    tool_definitions 为完整工具契约，tools 与其名称保持一致。
    timeout_seconds 为单次执行上限；环境配置以 PLUGIN_VALUES/PLUGIN_SECRETS JSON 注入。
    """

    model_config = ConfigDict(extra="forbid")
    protocol_version: int = 1
    entrypoint: str = "executor/main.py"
    tool_definitions: list[ProcessToolDefinition]
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    # 需要平台文件输入时指定工具参数字段，该字段必须为文件 ID 字符串数组。
    file_input_parameter: str | None = None
    probe: ProcessProbe | None = Field(default=None, description="可选连接检测，仍使用同一容器工具执行协议")

    @model_validator(mode="after")
    def validate_contract(self) -> "ProcessManifest":
        """校验本声明的标识、版本、工具 Schema 和允许的第一版能力。"""
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,59}", self.id):
            raise ValueError("插件标识只允许小写字母、数字、连字符，最长 60 字符")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?", self.version):
            raise ValueError("插件版本必须为 major.minor.patch 格式")
        if self.executor != "python-process" or self.protocol_version != 1:
            raise ValueError("仅支持 python-process 执行器和协议版本 1")
        safe_package_path(self.entrypoint)
        if not self.entrypoint.endswith(".py"):
            raise ValueError("插件入口必须是 Python 文件")
        names = [tool.name for tool in self.tool_definitions]
        if not names or len(names) > 30 or len(set(names)) != len(names) or sorted(names) != sorted(self.tools):
            raise ValueError("工具名称必须唯一，且与 tools 声明一致，最多 30 个")
        for tool in self.tool_definitions:
            if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,47}", tool.name):
                raise ValueError("工具名称格式无效")
            if tool.risk_level not in ("medium", "high"):
                raise ValueError("上传代码的工具风险只能为 medium 或 high")
            if tool.parameters.get("type") != "object":
                raise ValueError("工具输入 Schema 根节点必须是 object")
            validate_schema(tool.parameters)
            validate_schema(tool.output_schema)
        if self.file_input_parameter:
            for tool in self.tool_definitions:
                parameter = tool.parameters.get("properties", {}).get(self.file_input_parameter)
                if parameter is None or parameter.get("type") != "array" or parameter.get("items", {}).get("type") != "string":
                    raise ValueError("文件输入字段必须在所有工具中声明为字符串数组")
        keys = [field.key for field in self.fields]
        if len(keys) != len(set(keys)) or any(not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", key) for key in keys):
            raise ValueError("配置字段名称无效或重复")
        if self.capabilities.environment_import:
            raise ValueError("进程插件不支持宿主环境配置导入")
        if self.capabilities.connection_test != (self.probe is not None):
            raise ValueError("连接检测能力必须与 probe 声明一致")
        if self.probe:
            if self.probe.tool_name not in names:
                raise ValueError("连接检测只能调用声明中的工具")
            test_keys = [field.key for field in self.test_fields]
            if len(test_keys) != len(set(test_keys)) or any(not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", key) for key in test_keys):
                raise ValueError("检测字段名称无效或重复")
            if any(field.kind == "secret" for field in self.test_fields):
                raise ValueError("检测字段不能携带密钥，请使用插件配置中的密钥字段")
            if self.probe.parameter_keys() - set(test_keys):
                raise ValueError("连接检测模板引用未声明的检测字段")
        for path in self.skill_files:
            safe_package_path(path)
        return self


class CheckedPackage(BaseModel):
    """校验后的包；manifest 为声明，digest 为原始 ZIP 摘要，files 为普通文件数量。"""

    manifest: ProcessManifest
    digest: str
    files: int


class PluginFailure(BaseModel):
    """可传输失败实体；code 为稳定错误码，message 为面向调用方的说明。"""

    code: str
    message: str


class PluginArtifact(BaseModel):
    """平台生成文件引用；插件不能自行指定下载地址。"""

    file_id: str = Field(description="平台登记的文件 ID")
    name: str = Field(description="展示文件名")
    size: int = Field(description="文件字节数")
    url: str = Field(description="要求用户认证的下载接口")


class ProcessResult(BaseModel):
    """单次工具业务结果；ok 表示成功，data 按输出 Schema 校验，error 表示业务失败。"""

    model_config = ConfigDict(extra="forbid")
    ok: StrictBool
    data: Any = None
    error: PluginFailure | None = None
    # 插件不提供下载路径；artifacts 由平台登记输出文件后填入。
    artifacts: list[PluginArtifact] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_outcome(self) -> "ProcessResult":
        """拒绝同时成功与失败或失败缺少原因的结果。"""
        if self.ok == (self.error is not None):
            raise ValueError("成功结果不能带 error，失败结果必须带 error")
        json.dumps(self.data, allow_nan=False)
        return self


def safe_package_path(name: str) -> PurePosixPath:
    """将 name 校验为普通包内相对路径，拒绝越界、反斜线和平台特殊路径。"""
    path = PurePosixPath(name)
    if not name or "\\" in name or ":" in name or "\x00" in name or path.is_absolute() or any(part in ("..", ".", "") for part in name.split("/")):
        raise ValueError("插件包包含非法相对路径")
    if name.startswith("/") or len(name) > 240:
        raise ValueError("插件路径过长或不是相对路径")
    return path


def validate_schema(schema: dict[str, Any]) -> None:
    """校验 schema 为本地 JSON Schema；拒绝远程引用，避免校验触发网络访问。"""
    Draft202012Validator.check_schema(schema)
    json.dumps(schema, allow_nan=False)

    def visit(value: object) -> None:
        """递归检查 value 中的引用，只允许文档内引用。"""
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ("$ref", "$dynamicRef") and (not isinstance(child, str) or not child.startswith("#")):
                    raise ValueError("工具 Schema 只允许文档内引用")
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(schema)


def validate_dependencies(content: str) -> None:
    """校验 content 中固定版本的 PyPI 依赖；拒绝 URL、选项、可编辑包和构建脚本入口。"""
    for line in content.splitlines():
        value = line.strip()
        if value and not value.startswith("#") and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*==[A-Za-z0-9][A-Za-z0-9_.+!-]*", value):
            raise ValueError("requirements.lock 仅允许 package==version，每行一个固定版本依赖")


def check_package(content: bytes, destination: Path | None = None) -> CheckedPackage:
    """校验 content ZIP；destination 指定时在全部校验通过后解压到新的目标目录。"""
    if len(content) > 20 * 1024 * 1024:
        raise ValueError("插件包超过 20MB")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 1000 or sum(item.file_size for item in entries) > 80 * 1024 * 1024:
                raise ValueError("插件解压后超过 80MB 或 1000 个条目")
            files: dict[str, bytes] = {}
            seen: set[str] = set()
            for item in entries:
                name = item.filename.rstrip("/")
                safe_package_path(name)
                if name in seen or name.casefold() in {key.casefold() for key in seen}:
                    raise ValueError("插件包包含重复路径")
                seen.add(name)
                mode = item.external_attr >> 16
                if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)) or item.flag_bits & 1:
                    raise ValueError("插件包不允许链接、特殊文件或加密文件")
                if not item.is_dir():
                    files[name] = archive.read(item)
            if "manifest.json" not in files or "requirements.lock" not in files:
                raise ValueError("插件包缺少 manifest.json 或 requirements.lock")
            manifest = ProcessManifest.model_validate_json(files["manifest.json"])
            if manifest.entrypoint not in files or any(path not in files for path in manifest.skill_files):
                raise ValueError("声明的入口或 Skill 文件不存在")
            validate_dependencies(files["requirements.lock"].decode("utf-8"))
            if destination is not None:
                destination.mkdir(parents=True, exist_ok=False)
                for name, data in files.items():
                    target = destination.joinpath(*PurePosixPath(name).parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
            return CheckedPackage(manifest=manifest, digest=hashlib.sha256(content).hexdigest(), files=len(files))
    except (zipfile.BadZipFile, UnicodeError, KeyError) as exc:
        raise ValueError("插件包不是有效的 UTF-8 ZIP 包") from exc


def public_tool_name(plugin_id: str, tool_name: str) -> str:
    """由 plugin_id 与 tool_name 生成稳定模型工具名称，长度限制为 64 字符。"""
    name = f"plugin__{plugin_id.replace('-', '_')}__{tool_name}"
    if len(name) <= 64:
        return name
    return name[:51] + "_" + hashlib.sha256(name.encode()).hexdigest()[:12]
