"""安全转换 Pydantic 风格的 Schema 描述语言。

这里仅使用 ``ast`` 检查并读取声明，不会调用 ``exec``、``eval`` 或导入用户代码。
"""

import ast
import json
from typing import Any, Dict, List, Tuple

from .agent_output import validate_output_schema


_PRIMITIVE_TYPES = {
    "str": {"type": "string"},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
    "Any": {},
}
_FIELD_KEYWORDS = {
    "description", "default", "default_factory", "title",
    "ge", "gt", "le", "lt", "min_length", "max_length", "pattern",
}
_CONSTRAINT_MAP = {
    "ge": "minimum", "gt": "exclusiveMinimum", "le": "maximum", "lt": "exclusiveMaximum",
    "min_length": "minLength", "max_length": "maxLength", "pattern": "pattern",
}


def _error(node: ast.AST, message: str) -> ValueError:
    return ValueError(f"第 {getattr(node, 'lineno', '?')} 行：{message}")


def _literal(node: ast.AST) -> Any:
    """只接受 JSON 可表示的字面量，不求值任意 Python 表达式。"""
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError) as exc:
        raise _error(node, "这里只允许字符串、数字、布尔值、None、列表或字典字面量") from exc
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise _error(node, "默认值必须可以转换为 JSON") from exc
    return value


def _subscript_items(node: ast.Subscript) -> List[ast.AST]:
    return list(node.slice.elts) if isinstance(node.slice, ast.Tuple) else [node.slice]


def _annotation_to_schema(node: ast.AST, class_names: set) -> Dict[str, Any]:
    if isinstance(node, ast.Name):
        if node.id in _PRIMITIVE_TYPES:
            return dict(_PRIMITIVE_TYPES[node.id])
        if node.id in class_names:
            return {"$ref": f"#/$defs/{node.id}"}
        raise _error(node, f"不支持的字段类型：{node.id}")

    if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Name):
        raise _error(node, "字段类型必须使用受支持的简单类型")

    container = node.value.id
    items = _subscript_items(node)
    if container in {"list", "List"} and len(items) == 1:
        return {"type": "array", "items": _annotation_to_schema(items[0], class_names)}
    if container in {"dict", "Dict"} and len(items) == 2:
        key = items[0]
        if not isinstance(key, ast.Name) or key.id != "str":
            raise _error(key, "字典键目前只支持 str")
        return {"type": "object", "additionalProperties": _annotation_to_schema(items[1], class_names)}
    if container == "Optional" and len(items) == 1:
        return {"anyOf": [_annotation_to_schema(items[0], class_names), {"type": "null"}]}
    if container == "Literal" and items:
        values = [_literal(item) for item in items]
        return {"enum": values}
    raise _error(node, f"不支持的复合类型：{container}")


def _parse_field_value(node: ast.AST) -> Tuple[bool, Any, Dict[str, Any]]:
    """返回 (是否有默认值, 默认值, JSON Schema 约束)。"""
    if not isinstance(node, ast.Call):
        return True, _literal(node), {}
    if not isinstance(node.func, ast.Name) or node.func.id != "Field":
        raise _error(node, "字段默认值只允许字面量或 Field(...) 描述")
    if len(node.args) > 1:
        raise _error(node, "Field 最多只能有一个位置参数")

    positional_required = bool(node.args) and isinstance(node.args[0], ast.Constant) and node.args[0].value is Ellipsis
    has_default = bool(node.args) and not positional_required
    default = _literal(node.args[0]) if node.args and not positional_required else None
    constraints: Dict[str, Any] = {}
    seen = set()
    for keyword in node.keywords:
        if keyword.arg is None or keyword.arg not in _FIELD_KEYWORDS:
            raise _error(keyword.value, f"Field 不支持参数：{keyword.arg or '**kwargs'}")
        if keyword.arg in seen:
            raise _error(keyword.value, f"Field 参数重复：{keyword.arg}")
        seen.add(keyword.arg)
        if keyword.arg == "default":
            if has_default:
                raise _error(keyword.value, "Field 默认值不能重复指定")
            if isinstance(keyword.value, ast.Constant) and keyword.value.value is Ellipsis:
                has_default, default = False, None
            else:
                has_default, default = True, _literal(keyword.value)
        elif keyword.arg == "default_factory":
            if has_default:
                raise _error(keyword.value, "Field 默认值不能重复指定")
            if not isinstance(keyword.value, ast.Name) or keyword.value.id not in {"list", "dict"}:
                raise _error(keyword.value, "default_factory 只支持 list 或 dict")
            has_default, default = True, [] if keyword.value.id == "list" else {}
        elif keyword.arg in {"description", "title"}:
            constraints[keyword.arg] = _literal(keyword.value)
        else:
            constraints[_CONSTRAINT_MAP[keyword.arg]] = _literal(keyword.value)
    return has_default, default, constraints


def _parse_class(node: ast.ClassDef, class_names: set) -> Dict[str, Any]:
    if node.decorator_list:
        raise _error(node, "Schema 类不允许使用装饰器")
    if len(node.bases) != 1 or not isinstance(node.bases[0], ast.Name) or node.bases[0].id != "BaseModel":
        raise _error(node, "Schema 类必须且只能继承 BaseModel")

    properties: Dict[str, Any] = {}
    required = []
    for statement in node.body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
            continue  # 允许类文档字符串。
        if isinstance(statement, ast.Pass):
            continue
        if not isinstance(statement, ast.AnnAssign) or not isinstance(statement.target, ast.Name):
            raise _error(statement, "类中只允许带类型标注的字段声明")

        field_name = statement.target.id
        if field_name.startswith("_"):
            raise _error(statement, "字段名不能以下划线开头")
        field_schema = _annotation_to_schema(statement.annotation, class_names)
        if statement.value is None:
            has_default, default, constraints = False, None, {}
        else:
            has_default, default, constraints = _parse_field_value(statement.value)
        field_schema.update(constraints)
        if has_default:
            field_schema["default"] = default
        else:
            required.append(field_name)
        properties[field_name] = field_schema

    schema: Dict[str, Any] = {
        "title": node.name,
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


def python_schema_to_json_schema(source: str) -> Dict[str, Any]:
    """把安全的 Pydantic 风格描述转换为标准 JSON Schema。"""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Python Schema 不能为空")
    if len(source) > 20_000:
        raise ValueError("Python Schema 不能超过 20000 个字符")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"第 {exc.lineno or '?'} 行：Python Schema 语法错误：{exc.msg}") from exc

    classes = []
    for statement in tree.body:
        # 为复制现成示例提供便利，但导入声明本身不会被执行。
        if isinstance(statement, ast.ImportFrom):
            names = {alias.name for alias in statement.names}
            allowed_imports = {
                "pydantic": {"BaseModel", "Field"},
                "typing": {"Any", "Dict", "List", "Literal", "Optional"},
            }
            if statement.module not in allowed_imports or not names.issubset(allowed_imports[statement.module]):
                raise _error(statement, "只允许导入受支持的 pydantic 或 typing 类型")
            continue
        if isinstance(statement, ast.ClassDef):
            classes.append(statement)
            continue
        raise _error(statement, "顶层只允许 Schema 类定义")
    if not classes:
        raise ValueError("至少需要定义一个继承 BaseModel 的 Schema 类")

    class_names = {item.name for item in classes}
    parsed = {item.name: _parse_class(item, class_names) for item in classes}
    root = dict(parsed[classes[-1].name])
    root_ref = f"#/$defs/{classes[-1].name}"
    if any(root_ref in json.dumps(schema, ensure_ascii=False) for schema in parsed.values()):
        raise ValueError("根输出模型暂不支持递归引用")
    nested = {name: schema for name, schema in parsed.items() if name != classes[-1].name}
    if nested:
        root["$defs"] = nested
    return validate_output_schema(root) or {}


def _schema_type_to_python(schema: Dict[str, Any]) -> str:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "enum" in schema:
        return "Literal[" + ", ".join(repr(item) for item in schema["enum"]) + "]"
    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and len(any_of) == 2 and {item.get("type") for item in any_of} == {"null", next((item.get("type") for item in any_of if item.get("type") != "null"), None)}:
        non_null = next(item for item in any_of if item.get("type") != "null")
        return f"Optional[{_schema_type_to_python(non_null)}]"
    schema_type = schema.get("type")
    if schema_type == "string": return "str"
    if schema_type == "integer": return "int"
    if schema_type == "number": return "float"
    if schema_type == "boolean": return "bool"
    if schema_type == "array": return f"list[{_schema_type_to_python(schema.get('items', {}))}]"
    if schema_type == "object" and isinstance(schema.get("additionalProperties"), dict):
        return f"dict[str, {_schema_type_to_python(schema['additionalProperties'])}]"
    if schema_type == "object": return "dict[str, Any]"
    return "Any"


def _render_class(name: str, schema: Dict[str, Any]) -> str:
    required = set(schema.get("required", []))
    lines = [f"class {name}(BaseModel):"]
    for field_name, field_schema in schema.get("properties", {}).items():
        field_type = _schema_type_to_python(field_schema)
        arguments = []
        if field_name not in required:
            arguments.append(f"default={field_schema.get('default')!r}")
        for schema_key, field_key in (("description", "description"), ("title", "title"), ("minimum", "ge"), ("exclusiveMinimum", "gt"), ("maximum", "le"), ("exclusiveMaximum", "lt"), ("minLength", "min_length"), ("maxLength", "max_length"), ("pattern", "pattern")):
            if schema_key in field_schema:
                arguments.append(f"{field_key}={field_schema[schema_key]!r}")
        suffix = f" = Field({', '.join(arguments)})" if arguments else ""
        lines.append(f"    {field_name}: {field_type}{suffix}")
    if len(lines) == 1:
        lines.append("    pass")
    return "\n".join(lines)


def json_schema_to_python_schema(schema: Any) -> str:
    """把平台保存的 JSON Schema 转成规范化的 Pydantic 风格描述。"""
    normalized = validate_output_schema(schema)
    if not normalized or normalized.get("type") != "object":
        raise ValueError("当前只支持将 object 类型的 JSON Schema 转为 Python Schema")
    sections = []
    for name, nested in normalized.get("$defs", {}).items():
        sections.append(_render_class(name, nested))
    sections.append(_render_class(normalized.get("title") or "StructuredOutput", normalized))
    return "\n\n".join(sections)
