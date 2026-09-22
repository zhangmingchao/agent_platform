"""LLM Adapter 抽象接口。"""

from typing import Protocol

from langchain_core.language_models.chat_models import BaseChatModel

from ..models.llm_adapter import LlmAdapterCapabilities, LlmBuildConfig


class LlmAdapter(Protocol):
    """所有模型适配器需要实现的统一接口。"""

    provider: str
    display_name: str
    capabilities: LlmAdapterCapabilities

    def build_chat_model(self, config: LlmBuildConfig) -> BaseChatModel:
        """根据统一配置构建 LangChain Chat Model。

        Args:
            config: 已解密并规范化的模型构建配置。

        Returns:
            可交给 LangGraph 使用的 LangChain Chat Model。
        """
        ...
