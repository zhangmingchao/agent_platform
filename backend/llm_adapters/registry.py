"""LLM Adapter 注册表。"""

from typing import Dict, List

from .base import LlmAdapter
from .openai_compatible import OpenAICompatibleAdapter
from ..models.llm_adapter import LlmAdapterCapabilities, LlmAdapterDescriptor


_ADAPTERS: Dict[str, LlmAdapter] = {
    "openai": OpenAICompatibleAdapter(
        "openai",
        "OpenAI",
        LlmAdapterCapabilities(
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            supports_json_schema=True,
            supports_token_usage=True,
            supports_stream_usage=True,
            supports_reasoning=True,
            max_context_tokens=128000,
            default_timeout_seconds=60,
            default_max_retries=2,
            notes=["OpenAI 官方接口能力随具体模型变化，注册表只声明平台默认能力"],
        ),
    ),
    "deepseek": OpenAICompatibleAdapter(
        "deepseek",
        "DeepSeek",
        LlmAdapterCapabilities(
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,
            supports_json_schema=False,
            supports_token_usage=True,
            supports_stream_usage=True,
            supports_reasoning=True,
            max_context_tokens=64000,
            default_timeout_seconds=60,
            default_max_retries=1,
            notes=["DeepSeek 通过 OpenAI 兼容接口接入，reasoning 能力取决于具体模型"],
        ),
    ),
    "qwen": OpenAICompatibleAdapter(
        "qwen",
        "Qwen",
        LlmAdapterCapabilities(
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            supports_json_schema=True,
            supports_token_usage=True,
            supports_stream_usage=True,
            supports_reasoning=False,
            max_context_tokens=128000,
            default_timeout_seconds=60,
            default_max_retries=2,
            notes=["Qwen 通过 OpenAI 兼容接口接入，vision/JSON 能力取决于具体模型"],
        ),
    ),
}


def normalize_provider(provider: object) -> str:
    """规范化模型供应商标识。

    Args:
        provider: 数据库或接口传入的供应商值。

    Returns:
        小写供应商标识；空值默认使用 openai。
    """
    return str(provider or "openai").strip().lower() or "openai"


def get_llm_adapter(provider: object) -> LlmAdapter:
    """按供应商获取模型适配器。

    Args:
        provider: 模型供应商标识。

    Returns:
        已注册适配器。未知供应商回退到 OpenAI 兼容适配器，允许用户通过 base_url
        接入兼容网关。
    """
    normalized = normalize_provider(provider)
    return _ADAPTERS.get(
        normalized,
        OpenAICompatibleAdapter(normalized, f"{normalized} (OpenAI Compatible)"),
    )


def list_llm_adapters() -> List[LlmAdapterDescriptor]:
    """列出当前内置注册的模型适配器。"""
    return [
        LlmAdapterDescriptor(
            provider=provider,
            display_name=adapter.display_name,
            adapter_name=adapter.__class__.__name__,
            capabilities=adapter.capabilities,
        )
        for provider, adapter in sorted(_ADAPTERS.items())
    ]
