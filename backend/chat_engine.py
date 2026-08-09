"""
Chat Engine - Core streaming conversation with Agent + Skill + MCP.
Handles multi-round tool call loops.
"""
import json
import time
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, List

from openai import OpenAI

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MAX_TOOL_ROUNDS
from .mcp_client import McpClient, mcp_tools_to_openai_format
from .services.skill_service import read_skill_entrypoint, read_skill_file

log = logging.getLogger("agent-platform")

SEP = "━" * 60


def _sse_event(event_type: str, content: str = "") -> str:
    """Encode one SSE event as single-line JSON so newlines are preserved."""
    payload = json.dumps(
        {"type": event_type, "content": content},
        ensure_ascii=False,
    )
    return f"data:{payload}\n\n"


def _log_tool_list(tools: List[Dict]):
    log.info(f"已注册工具 (共{len(tools)}个):")
    for tool in tools:
        fn = tool["function"]
        log.info(f"  [{fn['name']}]")


def _log_round_header(round_num: int, msg_count: int):
    log.info(SEP)
    log.info(f"[LLM交互] 第{round_num}轮 | 消息数={msg_count}")


def _log_messages(messages: list):
    for i, msg in enumerate(messages):
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if isinstance(content, str):
            preview = content[:100].replace("\n", "\\n")
        else:
            preview = str(content)[:100]
        log.info(f"  消息[{i}] | role={role} | 摘要={preview}")


def _log_tool_call(idx: int, func_name: str, func_args: dict):
    log.info(f"  name={func_name}||请求参数: {json.dumps(func_args, ensure_ascii=False)}")


def _log_tool_result(func_name: str, result: str, elapsed_ms: int):
    log.info(f"  ToolResult | name={func_name} | 返回: {result}")



def _log_final_response(text: str):
    log.info(f"[LLM交互] 最终响应: {text}")


def build_skill_tool(skills: List[Dict]) -> Dict:
    """Build a unified Skill tool from multiple skill definitions."""
    available = []
    for s in skills:
        available.append(
            f'<skill>\n  <name>{s["name"]}</name>\n  <description>{s["description"]}</description>\n</skill>'
        )

    skills_xml = "\n".join(available) if available else "<skills></skills>"

    description = f"""Execute a skill within the main conversation.
<available_skills>
{skills_xml}
</available_skills>

Invoke a skill by its name to get full instructions and context for the task."""

    return {
        "type": "function",
        "function": {
            "name": "Skill",
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The skill name to execute"
                    }
                },
                "required": ["command"],
            }
        }
    }


def build_skill_file_tool(skills: List[Dict]) -> Dict:
    """Allow the model to read referenced text files from an activated Skill package."""
    skill_names = [skill["name"] for skill in skills]
    return {
        "type": "function",
        "function": {
            "name": "SkillFile",
            "description": (
                "Read a UTF-8 text file referenced by a Skill, such as "
                "references/guide.md. Call Skill first, then read only files it references."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "enum": skill_names,
                        "description": "The owning Skill name",
                    },
                    "path": {
                        "type": "string",
                        "description": "Relative path inside the Skill package",
                    },
                },
                "required": ["skill_name", "path"],
            },
        },
    }


def execute_skill(skills_map: Dict[str, Dict], command: str) -> str:
    skill = skills_map.get(command)
    if not skill:
        return f"Unknown skill: {command}"
    # Skill 的可执行内容以 data/skills/<id>/SKILL.md 为准；content 仅兼容旧数据。
    content = read_skill_entrypoint(skill["id"], skill.get("content", ""))
    log.info(f"[Skill执行] name={command} | 内容长度={len(content)}")
    return content


def execute_skill_file(skills_map: Dict[str, Dict], skill_name: str, path: str) -> str:
    skill = skills_map.get(skill_name)
    if not skill:
        return f"Unknown skill: {skill_name}"
    try:
        content = read_skill_file(skill["id"], path)
        log.info(f"[Skill文件] name={skill_name} | path={path} | 内容长度={len(content)}")
        return content
    except ValueError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


def build_all_tools(agent, skills: List[Dict], mcp_configs: List[Dict]) -> tuple:
    """
    Build all tools for an agent.
    Returns: (tools_list, executors_dict)
    """
    tools = []
    executors = {}

    if skills:
        skills_map = {s["name"]: s for s in skills}
        skill_tool = build_skill_tool(skills)
        tools.append(skill_tool)
        tools.append(build_skill_file_tool(skills))
        executors["Skill"] = lambda command: execute_skill(skills_map, command)
        executors["SkillFile"] = lambda skill_name, path: execute_skill_file(
            skills_map, skill_name, path
        )

    for mcp_cfg in mcp_configs:
        try:
            client = McpClient(mcp_cfg["base_url"], mcp_cfg["endpoint"])
            mcp_tools = client.list_tools()
            openai_tools = mcp_tools_to_openai_format(mcp_tools)
            tools.extend(openai_tools)
            for mt in mcp_tools:
                def make_executor(c, n):
                    def executor(**kwargs):
                        return c.call_tool(n, kwargs)
                    return executor
                executors[mt["name"]] = make_executor(client, mt["name"])
            log.info(f"[MCP] {mcp_cfg['name']} 加载了 {len(mcp_tools)} 个工具")
        except Exception as e:
            log.warning(f"[MCP] {mcp_cfg['name']} 连接失败: {e}")

    return tools, executors


async def chat_stream(
    agent: Dict,
    skills: List[Dict],
    mcp_configs: List[Dict],
    user_message: str,
    history_messages: List[Dict],
    session_id: int,
) -> AsyncGenerator[str, None]:
    """
    Core streaming chat with multi-round tool call loop.
    """
    model_name = agent.get("model", DEEPSEEK_MODEL)
    temperature = agent.get("temperature", 0.7)
    system_prompt = agent.get("system_prompt", "")
    log.info(f"model_name={model_name},system_prompt={system_prompt}")

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )

    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"[当前日期：{today}] {user_message}"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    for msg in history_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    tools, executors = build_all_tools(agent, skills, mcp_configs)

    log.info(f"\n{SEP}")
    log.info(f"[会话#{session_id}] Agent={agent['name']} | 用户消息: {user_message[:80]}")
    log.info(f"[会话#{session_id}] 历史消息={len(history_messages)} | 工具={json.dumps(tools)}")

    if not DEEPSEEK_API_KEY:
        yield _sse_event("chunk", "API Key 未配置")
        yield _sse_event("done")
        return

    max_tool_rounds = max(1, min(int(agent.get("iteration_count") or MAX_TOOL_ROUNDS), 100))

    for round_num in range(1, max_tool_rounds + 1):
        _log_round_header(round_num, len(messages))
        _log_messages(messages)
        _log_tool_list(tools)

        t0 = time.time()
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
            stream=False
        )
        llm_elapsed = int((time.time() - t0) * 1000)
        assistant_msg = response.choices[0].message

        if not assistant_msg.tool_calls:
            log.info(f"[LLM] 第{round_num}轮 → 最终响应 | 耗时={llm_elapsed}ms")
            final_text = assistant_msg.content or ""
            _log_final_response(final_text)

            # 这次非流式调用已经生成了完整答案，不再重复请求一次模型。
            # 以一个 SSE chunk 返回，避免答案不一致、双倍费用和连接取消问题。
            if final_text:
                yield _sse_event("chunk", final_text)
            yield _sse_event("done")
            return

        tool_calls = assistant_msg.tool_calls
        log.info(f"[LLM] 第{round_num}轮 → ToolCall ({len(tool_calls)}个) | 耗时={llm_elapsed}ms")

        messages.append(assistant_msg.model_dump(exclude_none=True))

        for idx, tool_call in enumerate(tool_calls):
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments or "{}")
            _log_tool_call(idx, func_name, func_args)

            executor = executors.get(func_name)
            if executor:
                tool_start = time.time()
                try:
                    result = executor(**func_args)
                    elapsed = int((time.time() - tool_start) * 1000)
                    result_str = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
                    _log_tool_result(func_name, result_str, elapsed)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)}, ensure_ascii=False)
                    log.error(f"  工具执行异常: {e}")
            else:
                result_str = json.dumps({"error": f"未知工具: {func_name}"}, ensure_ascii=False)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str
            })

    log.warning(f"[LLM] 超过最大轮次 {max_tool_rounds}")
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        stream=False,
    )
    final_text = response.choices[0].message.content or ""
    if final_text:
        yield _sse_event("chunk", final_text)
    yield _sse_event("done")
