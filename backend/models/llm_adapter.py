"""LLM Adapter 使用的强类型实体。"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LlmAdapterCapabilities:
    """模型适配器能力声明。

    Attributes:
        supports_streaming: 是否支持流式输出。
        supports_tools: 是否支持工具调用。
        supports_vision: 是否支持图片输入。
        supports_json_schema: 是否支持结构化 JSON 输出约束。
        supports_token_usage: 是否支持返回 Token 用量。
        supports_stream_usage: 是否支持流式 Token 用量。
        supports_reasoning: 是否支持 reasoning 或 thinking 参数。
        max_context_tokens: 最大上下文 Token 数；未知时为空。
        default_timeout_seconds: 该适配器建议的默认请求超时时间。
        default_max_retries: 该适配器建议的默认重试次数。
        notes: 额外能力说明，用于调试和未来前端展示。
    """

    supports_streaming: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    supports_json_schema: bool = False
    supports_token_usage: bool = True
    supports_stream_usage: bool = True
    supports_reasoning: bool = False
    max_context_tokens: Optional[int] = None
    default_timeout_seconds: int = 60
    default_max_retries: int = 2
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class LlmBuildConfig:
    """构建 LangChain Chat Model 所需的统一配置。

    Attributes:
        provider: 模型供应商标识，例如 openai、deepseek、qwen。
        model_name: 供应商侧模型 ID。
        api_key: 调用模型使用的 API Key。
        base_url: OpenAI 兼容接口基础地址；可为空。
        temperature: 采样温度。
        max_tokens: 单次最大输出 Token 数。
        callbacks: LangChain Callback 列表。
        timeout_seconds: 单次模型请求超时时间；为空时使用 LangChain 默认值。
        max_retries: 模型请求最大重试次数；为空时使用 LangChain 默认值。
    """

    provider: str
    model_name: str
    api_key: str
    base_url: Optional[str]
    temperature: float
    max_tokens: int
    callbacks: List[Any] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None


@dataclass(frozen=True)
class LlmAdapterDescriptor:
    """模型适配器注册信息。

    Attributes:
        provider: 供应商标识。
        display_name: 展示名称。
        adapter_name: 适配器实现名称。
        capabilities: 该适配器声明的能力。
    """

    provider: str
    display_name: str
    adapter_name: str
    capabilities: LlmAdapterCapabilities

    def to_dict(self) -> Dict[str, Any]:
        """转换为 API 可返回的 JSON 兼容结构。"""
        return {
            "provider": self.provider,
            "displayName": self.display_name,
            "adapterName": self.adapter_name,
            "capabilities": {
                "supportsStreaming": self.capabilities.supports_streaming,
                "supportsTools": self.capabilities.supports_tools,
                "supportsVision": self.capabilities.supports_vision,
                "supportsJsonSchema": self.capabilities.supports_json_schema,
                "supportsTokenUsage": self.capabilities.supports_token_usage,
                "supportsStreamUsage": self.capabilities.supports_stream_usage,
                "supportsReasoning": self.capabilities.supports_reasoning,
                "maxContextTokens": self.capabilities.max_context_tokens,
                "defaultTimeoutSeconds": self.capabilities.default_timeout_seconds,
                "defaultMaxRetries": self.capabilities.default_max_retries,
                "notes": list(self.capabilities.notes),
            },
        }
