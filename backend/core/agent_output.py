"""Agent 提示词模板渲染与结构化输出校验。"""

import json
import re
from typing import Any, Dict, Optional

from jsonschema import Draft202012Validator, SchemaError, ValidationError

_VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


def parse_json_object(value: Any, field_name: str, *, allow_none: bool = True) -> Optional[Dict]:
    """将数据库或接口中的 JSON 值规范化为对象。"""
    if value in (None, "") and allow_none:
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{field_name} 不是合法 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} 必须是 JSON 对象")
    return value


def validate_output_schema(schema: Any) -> Optional[Dict]:
    """校验并返回 JSON Schema；空值表示不启用结构化输出。"""
    normalized = parse_json_object(schema, "output_schema")
    if normalized is None:
        return None
    try:
        Draft202012Validator.check_schema(normalized)
    except SchemaError as exc:
        raise ValueError(f"output_schema 无效: {exc.message}") from exc
    return normalized


def render_prompt_template(template: str, defaults: Any, runtime: Dict[str, Any]) -> str:
    """使用自定义默认变量和可信运行时变量渲染 ``{{variable}}``。"""
    variables = parse_json_object(defaults, "prompt_variables") or {}
    variables = {**variables, **runtime}

    def replace(match: re.Match) -> str:
        name = match.group(1)
        return str(variables[name]) if name in variables else match.group(0)

    return _VARIABLE_PATTERN.sub(replace, template or "")


def append_schema_instruction(prompt: str, schema: Any) -> str:
    """向系统提示词追加结构化输出约束。"""
    normalized = validate_output_schema(schema)
    if not normalized:
        return prompt
    instruction = (
        "你必须将最终答案输出为一个合法 JSON，不能使用 Markdown 代码块，也不能添加 JSON 之外的文字。"
        "输出必须符合以下 JSON Schema：\n"
        + json.dumps(normalized, ensure_ascii=False)
    )
    return f"{prompt}\n\n{instruction}" if prompt else instruction


def parse_and_validate_structured_output(text: str, schema: Any) -> Optional[Dict]:
    """解析模型最终文本并按 Draft 2020-12 JSON Schema 校验。"""
    normalized = validate_output_schema(schema)
    if not normalized:
        return None
    candidate = (text or "").strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"结构化输出不是合法 JSON: {exc.msg}") from exc
    try:
        Draft202012Validator(normalized).validate(data)
    except ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path) or "$"
        raise ValueError(f"结构化输出不符合 Schema（{path}）: {exc.message}") from exc
    return data
