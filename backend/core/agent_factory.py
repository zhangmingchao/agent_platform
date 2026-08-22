"""智能体工厂 —— 创建集成工具、记忆、流式输出和模型配置的 LangGraph ReAct 智能体。"""
import logging
from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from ..config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .tools import build_skill_tools
from .mcp_tools import build_mcp_langchain_tools

log = logging.getLogger("agent-platform")

_checkpointer = InMemorySaver()


def build_llm(
    model_name: str,
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> ChatOpenAI:
    """创建 ChatOpenAI 实例。优先使用传入的 model_config，否则回退到 DeepSeek。"""
    return ChatOpenAI(
        model=model_name,
        base_url=base_url or DEEPSEEK_BASE_URL,
        api_key=api_key or DEEPSEEK_API_KEY,
        temperature=temperature,
    )


async def build_all_tools(skills: List[Dict], mcp_configs: List[Dict]) -> list:
    """从技能和 MCP 配置构建所有 LangChain 工具。"""
    tools = []
    tools.extend(build_skill_tools(skills))
    tools.extend(await build_mcp_langchain_tools(mcp_configs))
    log.info(f"[Tools] loaded {len(tools)} tools total")
    return tools


async def create_agent_instance(
    agent: Dict,
    skills: List[Dict],
    mcp_configs: List[Dict],
    model_config: Optional[Dict] = None,
):
    """
    创建一个集成工具、记忆和系统提示词的 LangGraph ReAct 智能体。

    如果提供了 model_config（来自用户的模型设置），则使用其 api_key/base_url/model_id。
    否则回退到环境变量中的 DeepSeek 配置。
    """
    if model_config:
        model_name = model_config.get("model_id", DEEPSEEK_MODEL)
        api_key = model_config.get("api_key", DEEPSEEK_API_KEY)
        base_url = model_config.get("base_url", DEEPSEEK_BASE_URL)
        temperature = agent.get("temperature", model_config.get("temperature", 0.7))
        log.info(f"[Agent] using user model config: {model_config.get('name', 'unknown')}")
    else:
        model_name = agent.get("model", DEEPSEEK_MODEL)
        api_key = DEEPSEEK_API_KEY
        base_url = DEEPSEEK_BASE_URL
        temperature = agent.get("temperature", 0.7)

    system_prompt = agent.get("system_prompt", "")

    llm = build_llm(model_name, temperature, api_key, base_url)
    tools = await build_all_tools(skills, mcp_configs)

    try:
        agent_executor = create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_prompt,
            checkpointer=_checkpointer,
        )
    except TypeError:
        agent_executor = create_react_agent(
            model=llm,
            tools=tools,
            state_modifier=system_prompt,
            checkpointer=_checkpointer,
        )

    log.info(
        f"[Agent] created | model={model_name} | tools={len(tools)} | prompt_len={len(system_prompt)}"
    )
    return agent_executor


def get_model_name(agent: Dict, model_config: Optional[Dict] = None) -> str:
    """获取用于链路追踪日志的模型显示名称。"""
    if model_config:
        return model_config.get("model_id", agent.get("model", DEEPSEEK_MODEL))
    return agent.get("model", DEEPSEEK_MODEL)
