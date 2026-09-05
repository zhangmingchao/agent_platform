"""Agent 领域实体。"""

from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Mapping, Optional


def _json_object(value: Any, fallback: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """将 MySQL JSON 字段统一转换为字典。"""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return fallback
    return dict(value) if isinstance(value, Mapping) else fallback


@dataclass(frozen=True)
class Agent:
    """跨聊天、工作流和 HTTP 接口共享的 Agent 领域实体。"""

    id: int
    user_id: Optional[int]
    name: str
    description: str
    system_prompt: str
    prompt_variables: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]]
    model: str
    model_config_id: Optional[int]
    temperature: float
    iteration_count: int
    skills: List[Dict[str, Any]] = field(default_factory=list)
    mcps: List[Dict[str, Any]] = field(default_factory=list)
    # 保留未显式建模的时间字段，确保现有 API 响应兼容。
    extra: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
        *,
        skills: Optional[List[Dict[str, Any]]] = None,
        mcps: Optional[List[Dict[str, Any]]] = None,
    ) -> "Agent":
        """将数据库记录转换为 Agent 实体。"""
        known_fields = {
            "id", "user_id", "name", "description", "system_prompt",
            "prompt_variables", "output_schema", "model", "model_config_id",
            "temperature", "iteration_count", "skills", "mcps",
        }
        return cls(
            id=int(data["id"]),
            user_id=(int(data["user_id"]) if data.get("user_id") is not None else None),
            name=str(data.get("name") or ""),
            description=str(data.get("description") or ""),
            system_prompt=str(data.get("system_prompt") or ""),
            prompt_variables=_json_object(data.get("prompt_variables"), {}) or {},
            output_schema=_json_object(data.get("output_schema"), None),
            model=str(data.get("model") or "deepseek-chat"),
            model_config_id=(int(data["model_config_id"]) if data.get("model_config_id") else None),
            temperature=float(data.get("temperature") if data.get("temperature") is not None else 0.7),
            iteration_count=int(data.get("iteration_count") or 6),
            skills=list(skills if skills is not None else data.get("skills") or []),
            mcps=list(mcps if mcps is not None else data.get("mcps") or []),
            extra={key: value for key, value in data.items() if key not in known_fields},
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为兼容现有 API 响应和 Agent 工厂的字典。"""
        result = dict(self.extra)
        result.update({
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "prompt_variables": dict(self.prompt_variables),
            "output_schema": self.output_schema,
            "model": self.model,
            "model_config_id": self.model_config_id,
            "temperature": self.temperature,
            "iteration_count": self.iteration_count,
            "skills": list(self.skills),
            "mcps": list(self.mcps),
        })
        return result

    def with_system_prompt(self, system_prompt: str) -> Dict[str, Any]:
        """为单次运行生成替换提示词后的工厂参数，不修改不可变实体。"""
        result = self.to_dict()
        result["system_prompt"] = system_prompt
        return result

    def to_summary_dict(self) -> Dict[str, Any]:
        """生成兼容 Agent 列表接口的摘要结构。"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "prompt_variables": dict(self.prompt_variables),
            "output_schema": self.output_schema,
            "model": self.model,
            "model_config_id": self.model_config_id,
            "temperature": self.temperature,
            "iteration_count": self.iteration_count,
            "created_at": self.extra.get("created_at"),
            "updated_at": self.extra.get("updated_at"),
        }
