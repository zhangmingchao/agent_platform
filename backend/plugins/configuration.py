"""按插件字段声明校验配置，不在公共保存流程中假定地址或 Token。"""

from ..models.plugin import ConfigValue, PluginConfigInput, PluginField, PluginSettings, validate_service_url


def validate_fields(fields: list[PluginField], data: PluginConfigInput, previous: PluginSettings, complete: bool) -> PluginSettings:
    """校验 fields 声明的 data，previous 用于保留密钥，complete 控制是否要求必填项完整。"""
    known = {field.key: field for field in fields}
    unknown = (set(data.values) | set(data.secrets) | set(data.clear_secrets)) - set(known)
    if unknown:
        raise ValueError("包含未声明的配置字段：" + "、".join(sorted(unknown)))
    values: dict[str, ConfigValue] = {}
    secrets: dict[str, str] = {}
    for field in fields:
        if field.kind == "secret":
            if field.key in data.values:
                raise ValueError(f"{field.label} 必须通过密钥字段提交")
            supplied = data.secrets.get(field.key, "")
            if supplied and field.key in data.clear_secrets:
                raise ValueError(f"不能同时设置和清除 {field.label}")
            value = "" if field.key in data.clear_secrets else (supplied or previous.secrets.get(field.key, ""))
            if len(value) > field.max_length:
                raise ValueError(f"{field.label} 超过最大长度 {field.max_length}")
            secrets[field.key] = value
        else:
            if field.key in data.secrets or field.key in data.clear_secrets:
                raise ValueError(f"{field.label} 不是密钥字段")
            value = data.values.get(field.key, previous.values.get(field.key, field.default))
            if value == "" and field.kind in ("integer", "boolean"):
                raise ValueError(f"{field.label} 的类型不正确")
            if value is not None and value != "":
                if field.kind == "integer":
                    if type(value) is not int or (field.minimum is not None and value < field.minimum) or (field.maximum is not None and value > field.maximum):
                        raise ValueError(f"{field.label} 必须是范围内的整数")
                elif field.kind == "boolean":
                    if type(value) is not bool:
                        raise ValueError(f"{field.label} 必须是布尔值")
                else:
                    if not isinstance(value, str) or len(value) > field.max_length:
                        raise ValueError(f"{field.label} 必须是长度不超过 {field.max_length} 的文本")
                    value = value.strip()
                    if value and field.format == "url":
                        value = validate_service_url(value)
                    if field.kind == "select" and value not in {option.value for option in field.options}:
                        raise ValueError(f"{field.label} 不在可选值中")
            values[field.key] = value
        if complete and field.required and (value is None or value == ""):
            raise ValueError(f"请填写 {field.label}")
    return PluginSettings(values=values, secrets=secrets)


def settings_complete(fields: list[PluginField], settings: PluginSettings) -> bool:
    """根据 fields 必填项判断 settings 是否完整，不返回包含密钥的中间字典。"""
    try:
        validate_fields(fields, PluginConfigInput(), settings, complete=True)
        return True
    except ValueError:
        return False
