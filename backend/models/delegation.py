"""委托工具的参数与返回实体，避免业务层传递无约束字典。"""
from typing import Literal

from pydantic import BaseModel, Field


class DelegateTaskInput(BaseModel):
    """模型提供的子任务说明；目标权限由服务端白名单决定。"""

    agent_id: int = Field(gt=0, description="授权目标 Agent ID")
    task: str = Field(min_length=1, max_length=10000, description="明确的子任务、要求和交付标准")
    context: str = Field(default="", max_length=20000, description="完成任务必要的背景、资料和已知文件 ID，不自动附带完整聊天历史")


class DelegationResult(BaseModel):
    """子任务结束后提供给主模型及界面的公开结果。"""

    delegation_id: str = Field(description="本次委托唯一标识")
    agent_id: int = Field(description="目标 Agent ID")
    agent_name: str = Field(default="", description="目标 Agent 展示名")
    status: Literal['completed', 'failed', 'timed_out', 'rejected', 'cancelled'] = Field(description="子任务状态")
    result: str = Field(default="", description="子 Agent 最终答案，最多 20000 字符")
    error: str = Field(default="", description="失败原因，不包含模型凭据")
    trace_run_id: int | None = Field(default=None, description="子 Trace ID，用于追踪")
