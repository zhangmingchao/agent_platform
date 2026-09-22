"""用户 API Key 与外部聊天接口使用的强类型实体。"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InvocationSource(str, Enum):
    """Agent 调用来源，用于区分平台、外部 API 和工作流执行。"""

    PLATFORM = "platform"
    API = "api"
    WORKFLOW = "workflow"


@dataclass(frozen=True)
class ApiAuthenticatedUser:
    """由 API Key 认证得到的用户身份。

    Attributes:
        user_id: 密钥所属的平台用户 ID。
        username: 密钥所属的平台用户名。
        api_key_id: 当前请求使用的公开密钥 ID，用于限流和审计。
    """

    user_id: int
    username: str
    api_key_id: str


@dataclass(frozen=True)
class ApiKeyStatus:
    """当前用户 API Key 的可公开状态。

    Attributes:
        configured: 用户是否已经创建 API Key。
        key_prefix: 可用于识别密钥的脱敏前缀，不包含 secret。
        status: 密钥状态，取值为 active 或 revoked。
        created_at: 最近一次创建或轮换密钥的时间。
        last_used_at: 密钥最后一次通过认证的时间。
    """

    configured: bool
    key_prefix: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


@dataclass(frozen=True)
class IssuedApiKey:
    """新创建或轮换后的 API Key，只允许在签发响应中出现一次。

    Attributes:
        api_key: 需要用户立即保存的完整 API Key 明文。
        key_prefix: 后续页面用于识别密钥的非敏感前缀。
        created_at: 本次签发时间。
    """

    api_key: str
    key_prefix: str
    created_at: datetime


@dataclass(frozen=True)
class ApiKeyRevocationResult:
    """API Key 吊销操作结果。

    Attributes:
        revoked: 是否找到并吊销了当前用户的有效密钥。
    """

    revoked: bool


class ExternalChatMessage(BaseModel):
    """外部调用方提交的一条聊天历史消息。

    Attributes:
        role: 消息角色，只允许 user 或 assistant。
        content: 发送给模型的纯文本消息内容。
    """

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"] = Field(description="消息角色")
    content: str = Field(min_length=1, max_length=20_000, description="消息文本")

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """拒绝只包含空白字符的消息，同时保留原始文本格式。"""
        if not value.strip():
            raise ValueError("消息内容不能为空")
        return value


class ExternalChatRequest(BaseModel):
    """无状态外部聊天请求。

    Attributes:
        messages: 调用方维护的完整聊天历史，最后一条必须是 user。
        client_conversation_id: 调用方自己的会话标识，只用于 Trace 关联，不用于读取历史。
    """

    model_config = ConfigDict(extra="forbid")

    messages: List[ExternalChatMessage] = Field(min_length=1, max_length=100)
    client_conversation_id: Optional[str] = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_history(self) -> "ExternalChatRequest":
        """校验最后一条角色和历史总长度，防止无界上下文进入模型。"""
        if self.messages[-1].role != "user":
            raise ValueError("messages 最后一条必须是 user 消息")
        total_characters = sum(len(message.content) for message in self.messages)
        if total_characters > 100_000:
            raise ValueError("messages 总长度不能超过 100000 个字符")
        return self

    def latest_user_message(self) -> str:
        """返回本次请求最后一条用户消息。"""
        return self.messages[-1].content
