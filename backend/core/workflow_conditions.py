"""工作流文本条件与结构化字段条件判断器。"""

import json
import re
from typing import Any, List, Mapping, Optional, Sequence

from ..models.workflow_condition import WorkflowConditionResult, WorkflowConditionRule

_MISSING = object()


def _parse_structured_text(current_input: str) -> Optional[Any]:
    """解析 Agent 输出的 JSON 文本。

    参数：
    - ``current_input``：上一个工作流节点输出的原始文本。

    返回值：解析成功时返回 JSON 值，解析失败时返回 ``None``。兼容 ```json 代码块。
    """
    candidate = (current_input or "").strip()
    fenced = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        candidate,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        candidate = fenced.group(1)
    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return None


def _read_field_path(data: Any, field_path: str) -> Any:
    """按点号路径读取结构化字段。

    参数：
    - ``data``：已经解析的 JSON 对象或数组；
    - ``field_path``：字段路径，例如 ``result.level`` 或 ``items.0.name``。

    返回值：字段存在时返回真实值，不存在时返回内部缺失标记。
    """
    if not field_path:
        return _MISSING
    current = data
    for part in field_path.split("."):
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return _MISSING
    return current


def _parse_expected_value(value: Any) -> Any:
    """把前端输入转换为可比较的 JSON 标量。

    参数：
    - ``value``：条件配置中的期望值；数字、布尔值和 null 会按 JSON 类型解析，
      普通文本保持字符串。若要匹配字符串 ``"1"``，前端应输入带双引号的 ``"1"``。
    """
    if not isinstance(value, str):
        return value
    text = value.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _compare_structured_value(actual: Any, operator: str, expected: Any) -> bool:
    """执行结构化字段比较。

    参数：
    - ``actual``：通过字段路径读取到的真实值或缺失标记；
    - ``operator``：eq、ne、gt、gte、lt、lte、contains、exists、not_exists；
    - ``expected``：经过 JSON 类型转换后的期望值。
    """
    if operator == "exists":
        return actual is not _MISSING
    if operator == "not_exists":
        return actual is _MISSING
    if actual is _MISSING:
        return False
    if operator in {"eq", "ne"}:
        # JSON 中布尔值、数字和字符串是不同类型，避免 Python 将 True 与 1 判为相等。
        is_equal = type(actual) is type(expected) and actual == expected
        return is_equal if operator == "eq" else not is_equal
    if operator == "contains":
        if isinstance(actual, (str, list, tuple, set, Mapping)):
            return expected in actual
        return False
    if operator in {"gt", "gte", "lt", "lte"}:
        try:
            if operator == "gt":
                return actual > expected
            if operator == "gte":
                return actual >= expected
            if operator == "lt":
                return actual < expected
            return actual <= expected
        except TypeError:
            return False
    return False


def evaluate_workflow_conditions(
    conditions: Sequence[Mapping[str, Any]],
    current_input: str,
) -> WorkflowConditionResult:
    """按配置顺序判断工作流条件并返回命中结果实体。

    参数：
    - ``conditions``：条件节点中的分支配置列表；
    - ``current_input``：上一个节点输出文本，结构化规则会尝试将其解析为 JSON。

    返回值：包含分支下标、命中规则和实际字段值的 ``WorkflowConditionResult``。
    """
    rules: List[WorkflowConditionRule] = [
        WorkflowConditionRule.from_mapping(item) for item in conditions
    ]
    structured_data: Any = _MISSING

    for index, rule in enumerate(rules):
        if rule.condition_type == "else":
            continue
        if rule.condition_type == "contains":
            keyword = str(rule.value or "")
            if keyword and keyword in (current_input or ""):
                return WorkflowConditionResult(index, rule)
        elif rule.condition_type == "regex":
            expression = str(rule.value or "")
            if not expression:
                continue
            try:
                if re.search(expression, current_input or ""):
                    return WorkflowConditionResult(index, rule)
            except re.error:
                continue
        elif rule.condition_type == "structured":
            if structured_data is _MISSING:
                parsed = _parse_structured_text(current_input)
                structured_data = parsed if parsed is not None else None
            actual = _read_field_path(structured_data, rule.field_path)
            expected = _parse_expected_value(rule.value)
            if _compare_structured_value(actual, rule.operator, expected):
                visible_actual = None if actual is _MISSING else actual
                return WorkflowConditionResult(index, rule, visible_actual)

    for index, rule in enumerate(rules):
        if rule.condition_type == "else":
            return WorkflowConditionResult(index, rule)
    return WorkflowConditionResult(0, rules[0] if rules else None)
