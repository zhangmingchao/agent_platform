"""模型 Token 估算和供应商 usage 提取工具。"""

import json
import math
from typing import Any, Sequence

from langchain_core.messages import BaseMessage, message_to_dict

from ..models.token_quota import ModelTokenUsage, TokenEstimate


def _json_text(value: Any) -> str:
    """将消息或工具结构稳定序列化为估算文本。"""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def estimate_model_tokens(
    messages: Sequence[BaseMessage],
    tool_schemas: Sequence[dict],
    max_output_tokens: int,
    safety_factor: float = 1.2,
) -> TokenEstimate:
    """保守估算完整模型请求的最大 Token 消耗。

    Args:
        messages: 本轮实际发送给模型的全部 LangChain 消息。
        tool_schemas: 本轮绑定到模型的工具 JSON Schema。
        max_output_tokens: 模型配置允许的单轮最大输出 Token。
        safety_factor: 对未知供应商分词差异应用的安全系数。

    Returns:
        包含消息、工具、协议开销和最终预占量的强类型估算结果。
    """
    message_text = _json_text([message_to_dict(message) for message in messages])
    tool_text = _json_text(list(tool_schemas)) if tool_schemas else ""
    # 不同 OpenAI 兼容模型没有统一 Tokenizer。中文和 JSON 按每 2 个字符约 1 Token
    # 保守估算，并额外计算每条消息的协议开销；最终账目仍以供应商 usage 为准。
    message_tokens = max(1, math.ceil(len(message_text) / 2))
    tool_schema_tokens = math.ceil(len(tool_text) / 2) if tool_text else 0
    protocol_overhead_tokens = 12 + len(messages) * 6
    raw_input_tokens = message_tokens + tool_schema_tokens + protocol_overhead_tokens
    estimated_input_tokens = max(1, math.ceil(raw_input_tokens * safety_factor))
    bounded_output_tokens = max(1, int(max_output_tokens))
    return TokenEstimate(
        message_tokens=message_tokens,
        tool_schema_tokens=tool_schema_tokens,
        protocol_overhead_tokens=protocol_overhead_tokens,
        estimated_input_tokens=estimated_input_tokens,
        max_output_tokens=bounded_output_tokens,
        reserved_total_tokens=estimated_input_tokens + bounded_output_tokens,
        estimator_name="conservative-char-v1",
        safety_factor=safety_factor,
    )


def extract_token_usage(value: Any) -> ModelTokenUsage:
    """从 AIMessage、ChatGeneration 或 LLMResult 中提取标准 Token 用量。

    Args:
        value: LangChain 模型结束事件或 Callback 返回的响应对象。

    Returns:
        标准化后的 Token 用量；供应商没有返回 usage 时各字段为 ``0``。
    """
    candidates = [value]
    generations = getattr(value, "generations", None)
    if generations:
        for generation_group in generations:
            candidates.extend(generation_group if isinstance(generation_group, list) else [generation_group])
    for candidate in list(candidates):
        message = getattr(candidate, "message", None)
        if message is not None:
            candidates.append(message)

    for candidate in candidates:
        usage = getattr(candidate, "usage_metadata", None)
        if isinstance(usage, dict):
            input_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
            output_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
            total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
            if total_tokens > 0:
                return ModelTokenUsage(input_tokens, output_tokens, total_tokens)

        metadata = getattr(candidate, "response_metadata", None)
        if isinstance(metadata, dict):
            nested = metadata.get("token_usage") or metadata.get("usage") or metadata
            if isinstance(nested, dict):
                input_tokens = int(nested.get("input_tokens") or nested.get("prompt_tokens") or 0)
                output_tokens = int(nested.get("output_tokens") or nested.get("completion_tokens") or 0)
                total_tokens = int(nested.get("total_tokens") or input_tokens + output_tokens)
                if total_tokens > 0:
                    return ModelTokenUsage(input_tokens, output_tokens, total_tokens)

    llm_output = getattr(value, "llm_output", None)
    if isinstance(llm_output, dict):
        usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
        if isinstance(usage, dict):
            input_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
            output_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
            total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
            if total_tokens > 0:
                return ModelTokenUsage(input_tokens, output_tokens, total_tokens)
    return ModelTokenUsage()
