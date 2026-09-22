"""OpenAI 兼容协议模型适配器。"""

from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from ..models.llm_adapter import LlmAdapterCapabilities, LlmBuildConfig


class OpenAICompatibleAdapter:
    """通过 OpenAI Chat Completions 兼容接口调用模型的适配器。"""

    provider = "openai"
    display_name = "OpenAI Compatible"
    capabilities = LlmAdapterCapabilities(
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        supports_json_schema=False,
        supports_token_usage=True,
        supports_stream_usage=True,
        supports_reasoning=False,
        max_context_tokens=None,
        default_timeout_seconds=60,
        default_max_retries=2,
        notes=["DeepSeek、Qwen、OpenAI 兼容网关可复用该适配器"],
    )

    def __init__(
        self,
        provider: str = "openai",
        display_name: Optional[str] = None,
        capabilities: Optional[LlmAdapterCapabilities] = None,
    ) -> None:
        """初始化兼容适配器。

        Args:
            provider: 注册到平台的供应商标识。
            display_name: 面向用户或日志展示的适配器名称。
            capabilities: 供应商级能力覆盖；为空时使用 OpenAI 兼容默认能力。
        """
        self.provider = provider
        self.display_name = display_name or provider
        if capabilities is not None:
            self.capabilities = capabilities

    def build_chat_model(self, config: LlmBuildConfig) -> BaseChatModel:
        """构建 OpenAI 兼容 Chat 模型。"""
        kwargs = {
            "model": config.model_name,
            "base_url": config.base_url,
            "api_key": config.api_key,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream_usage": True,
            "callbacks": list(config.callbacks),
        }
        if config.timeout_seconds is not None:
            kwargs["timeout"] = config.timeout_seconds
        if config.max_retries is not None:
            kwargs["max_retries"] = config.max_retries
        return ChatOpenAI(**kwargs)
