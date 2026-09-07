"""工作流条件判断使用的强类型实体。"""

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class WorkflowConditionRule:
    """描述条件节点中的一条分支规则。

    字段含义：
    - ``label``：前端展示的分支名称；
    - ``condition_type``：规则类型，支持 contains、regex、structured、else；
    - ``value``：关键词、正则表达式或结构化比较的期望值；
    - ``field_path``：结构化数据字段路径，例如 ``type`` 或 ``result.level``；
    - ``operator``：结构化比较操作符，例如 eq、gt、contains、exists。
    """

    label: str
    condition_type: str
    value: Any = None
    field_path: str = ""
    operator: str = "eq"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "WorkflowConditionRule":
        """将工作流配置字典转换为条件规则实体。

        参数：
        - ``data``：前端保存到工作流节点中的单条条件配置。
        """
        return cls(
            label=str(data.get("label") or ""),
            condition_type=str(data.get("type") or "else"),
            value=data.get("value"),
            field_path=str(data.get("field") or "").strip(),
            operator=str(data.get("operator") or "eq"),
        )


@dataclass(frozen=True)
class WorkflowConditionResult:
    """条件节点一次判断的结果。

    字段含义：
    - ``branch_index``：命中的条件数组下标；
    - ``rule``：实际命中的规则实体；没有配置规则时为 ``None``；
    - ``actual_value``：结构化字段判断读取到的真实值，便于调试与追踪。
    """

    branch_index: int
    rule: Optional[WorkflowConditionRule]
    actual_value: Any = None

