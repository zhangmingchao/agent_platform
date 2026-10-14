"""智能体工厂 —— 创建集成工具、记忆、流式输出和模型配置的 LangGraph ReAct 智能体。"""
import logging
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.utils.function_calling import convert_to_openai_tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from ..config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from ..llm_adapters.registry import get_llm_adapter
from ..models.llm_adapter import LlmBuildConfig
from ..models.task_planning import PlanningMode
from ..runtime.models import RuntimeContext
from ..runtime.tools import build_runtime_tools
from .agent_state import AgentPlatformState
from .bi_cli_tool import build_bi_cli_tools
from .tools import build_skill_tools
from .mcp_tools import build_mcp_langchain_tools
from .task_planning import create_task_planning_graph
from .token_quota_callback import ModelTokenQuotaCallback
from .tool_execution_pipeline import wrap_tools_with_execution_pipeline
from .trace_handler import TraceContext

log = logging.getLogger(__name__)

_checkpointer = InMemorySaver()


def build_llm(
    model_name: str,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    max_tokens: int = 4096,
    callbacks: Optional[Sequence[BaseCallbackHandler]] = None,
    provider: str = "openai",
    timeout_seconds: Optional[int] = None,
    max_retries: Optional[int] = None,
) -> BaseChatModel:
    """通过 LLM Adapter 创建 Chat Model。

    Args:
        model_name: 供应商使用的模型标识。
        temperature: 模型采样温度。
        api_key: 调用模型使用的 API Key。
        base_url: OpenAI 兼容接口基础地址。
        max_tokens: 单次调用允许生成的最大 Token 数。
        callbacks: 模型生命周期 Callback，额度控制会通过这里注入。
        provider: 模型供应商标识，用于选择 LLM Adapter。
        timeout_seconds: 单次模型请求超时时间。
        max_retries: 模型请求最大重试次数。
    """
    adapter = get_llm_adapter(provider)
    return adapter.build_chat_model(
        LlmBuildConfig(
            provider=provider,
            model_name=model_name,
            api_key=api_key or "",
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=list(callbacks or []),
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
    )


async def build_all_tools(
    skills: List[Dict],
    mcp_configs: List[Dict],
    runtime_context: Optional[RuntimeContext] = None,
) -> list:
    """从技能和 MCP 配置构建所有 LangChain 工具。"""
    tools = []
    tools.extend(build_skill_tools(skills))
    tools.extend(build_runtime_tools(runtime_context))
    tools.extend(build_bi_cli_tools(runtime_context))
    tools.extend(await build_mcp_langchain_tools(mcp_configs))
    tools = wrap_tools_with_execution_pipeline(tools, runtime_context)
    log.info(f"[Tools] loaded {len(tools)} tools total")
    return tools


async def create_agent_instance(
    agent: Dict,
    skills: List[Dict],
    mcp_configs: List[Dict],
    model_config: Optional[Dict] = None,
    runtime_context: Optional[RuntimeContext] = None,
    trace_ctx: Optional[TraceContext] = None,
    planning_execution_prompt: Optional[str] = None,
) -> CompiledStateGraph:
    """
    创建一个集成工具、记忆和系统提示词的 LangGraph ReAct 智能体。

    如果提供了 model_config（来自用户的模型设置），则使用其 api_key/base_url/model_id。
    否则回退到环境变量中的 DeepSeek 配置。
    """
    # 自定义模型配置优先；未配置时回退到环境变量，避免空指针。
    if model_config:
        provider = str(model_config.get("provider") or "openai")
        model_name = model_config.get("model_id", DEEPSEEK_MODEL)
        api_key = model_config.get("api_key", DEEPSEEK_API_KEY)
        base_url = model_config.get("base_url", DEEPSEEK_BASE_URL)
        temperature = agent.get("temperature", model_config.get("temperature", 0.7))
        max_tokens = int(model_config.get("max_tokens") or 4096)
        log.info(f"[Agent] using user model config: {model_config.get('name', 'unknown')}")
    else:
        provider = "deepseek"
        model_name = agent.get("model", DEEPSEEK_MODEL)
        api_key = DEEPSEEK_API_KEY
        base_url = DEEPSEEK_BASE_URL
        temperature = agent.get("temperature", 0.7)
        max_tokens = 4096

    system_prompt = agent.get("system_prompt", "")

    tools = await build_all_tools(skills, mcp_configs, runtime_context)
    callbacks: List[BaseCallbackHandler] = []
    if model_config and runtime_context:
        tool_schemas: List[Dict[str, Any]] = [convert_to_openai_tool(tool) for tool in tools]
        callbacks.append(
            ModelTokenQuotaCallback(model_config, runtime_context.user_id, tool_schemas)
        )
    llm = build_llm(
        model_name,
        temperature,
        api_key,
        base_url,
        max_tokens=max_tokens,
        callbacks=callbacks,
        provider=provider,
    )

    planning_mode = PlanningMode(str(agent.get("planning_mode") or "disabled"))
    react_checkpointer = None if planning_mode is PlanningMode.EXPLICIT and trace_ctx else _checkpointer
    react_prompt = (
        planning_execution_prompt
        if planning_mode is PlanningMode.EXPLICIT and planning_execution_prompt is not None
        else system_prompt
    )

    try:
        react_graph = create_react_agent(
            model=llm,
            tools=tools,
            prompt=react_prompt,
            # 使用扩展 State，同时保留内置 messages/remaining_steps 行为。
            state_schema=AgentPlatformState,
            checkpointer=react_checkpointer,
        )
    except TypeError:
        react_graph = create_react_agent(
            model=llm,
            tools=tools,
            state_modifier=react_prompt,
            # 兼容旧版 prompt 参数名称时仍使用同一套自定义 State。
            state_schema=AgentPlatformState,
            checkpointer=react_checkpointer,
        )

    if planning_mode is PlanningMode.EXPLICIT and trace_ctx and runtime_context:
        agent_executor = create_task_planning_graph(
            llm=llm,
            react_graph=react_graph,
            tools=tools,
            final_system_prompt=system_prompt,
            checkpointer=_checkpointer,
            trace_ctx=trace_ctx,
            user_id=runtime_context.user_id,
            agent_id=int(agent["id"]),
            max_tool_rounds=max(1, min(int(agent.get("iteration_count") or 6), 100)),
        )
    else:
        # 工作流已经有明确节点计划，不在工作流 Agent 内再次嵌套任务规划。
        agent_executor = react_graph

    log.info(
        f"[Agent] created | model={model_name} | tools={len(tools)} | prompt_len={len(system_prompt)}"
    )
    return agent_executor


def get_model_name(agent: Dict, model_config: Optional[Dict] = None) -> str:
    """获取用于链路追踪日志的模型显示名称。"""
    if model_config:
        return model_config.get("model_id", agent.get("model", DEEPSEEK_MODEL))
    return agent.get("model", DEEPSEEK_MODEL)
