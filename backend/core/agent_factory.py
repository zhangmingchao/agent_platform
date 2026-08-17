"""Agent factory — creates LangGraph ReAct agents with tools, memory, streaming, and model config."""
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
    """Create a ChatOpenAI instance. Uses model_config if provided, falls back to DeepSeek."""
    return ChatOpenAI(
        model=model_name,
        base_url=base_url or DEEPSEEK_BASE_URL,
        api_key=api_key or DEEPSEEK_API_KEY,
        temperature=temperature,
    )


async def build_all_tools(skills: List[Dict], mcp_configs: List[Dict]) -> list:
    """Build all LangChain tools from skills and MCP configs."""
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
    Create a LangGraph ReAct agent with tools, memory, and system prompt.

    If model_config is provided (from user's model settings), use its api_key/base_url/model_id.
    Otherwise fall back to DeepSeek config from environment variables.
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
    """Get the model display name for trace logging."""
    if model_config:
        return model_config.get("model_id", agent.get("model", DEEPSEEK_MODEL))
    return agent.get("model", DEEPSEEK_MODEL)
