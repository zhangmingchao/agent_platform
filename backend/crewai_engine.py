"""CrewAI-backed conversation runtime with Skill, MCP and Trace integration."""
import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, create_model

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, MAX_TOOL_ROUNDS
from .mcp_client import McpClient
from .services.skill_service import read_skill_entrypoint, read_skill_file
from .services.trace_service import create_span

log = logging.getLogger("agent-platform")


def _sse_event(event_type: str, content: str = "", **metadata: Any) -> str:
    payload = json.dumps(
        {"type": event_type, "content": content, **metadata},
        ensure_ascii=False,
        default=str,
    )
    return f"data:{payload}\n\n"


async def _emit_runtime_event(
    event_queue: Optional[asyncio.Queue],
    event_type: str,
    content: str = "",
    **metadata: Any,
) -> None:
    if event_queue is not None:
        await event_queue.put({"type": event_type, "content": content, **metadata})


async def _trace_span(trace_id: Optional[int], **kwargs: Any) -> None:
    if not trace_id:
        return
    try:
        await create_span(trace_id=trace_id, **kwargs)
    except Exception:
        log.exception("[Trace#%s] 写入 CrewAI Span 失败", trace_id)


def _schema_type(schema: Dict[str, Any]) -> Any:
    schema_type = schema.get("type")
    if schema_type == "string":
        return str
    if schema_type == "integer":
        return int
    if schema_type == "number":
        return float
    if schema_type == "boolean":
        return bool
    if schema_type == "array":
        return List[Any]
    if schema_type == "object":
        return Dict[str, Any]
    return Any


def _args_model(tool_name: str, input_schema: Optional[Dict[str, Any]]) -> type[BaseModel]:
    """Convert the common subset of MCP JSON Schema into a Pydantic model."""
    schema = input_schema or {"type": "object", "properties": {}}
    required = set(schema.get("required", []))
    fields: Dict[str, Any] = {}
    for name, field_schema in schema.get("properties", {}).items():
        annotation = _schema_type(field_schema)
        default = ... if name in required else field_schema.get("default", None)
        fields[name] = (
            annotation,
            Field(default, description=field_schema.get("description", "")),
        )
    model_name = re.sub(r"[^0-9A-Za-z_]", "_", tool_name) or "Tool"
    return create_model(f"{model_name}Arguments", **fields)


class PlatformTool(BaseTool):
    """CrewAI tool adapter around the platform's existing synchronous executors."""

    executor: Callable[..., Any] = Field(exclude=True)
    agent_name: str = Field(exclude=True)
    recorder: Any = Field(exclude=True)
    source_type: str = Field(default="tool", exclude=True)
    source_id: int = Field(default=0, exclude=True)

    def _run(self, **kwargs: Any) -> Any:
        started = time.time()
        started_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
        status = "success"
        error_text = ""
        result: Any = None
        try:
            result = self.executor(**kwargs)
            return result
        except Exception as exc:
            status = "error"
            error_text = str(exc)
            raise
        finally:
            self.recorder.events.append(
                {
                    "agent_name": self.agent_name,
                    "tool_name": self.name,
                    "status": status,
                    "input": kwargs,
                    "output": result,
                    "error": error_text,
                    "started_at": started_at,
                    "duration_ms": int((time.time() - started) * 1000),
                }
            )


class SkillCommand(BaseModel):
    command: str = Field(description="要执行的 Skill 名称")


class SkillFileCommand(BaseModel):
    skill_name: str = Field(description="Skill 名称")
    path: str = Field(description="Skill 包内的相对文件路径")


class ToolEventRecorder:
    """Mutable holder kept by reference when Pydantic validates tool models."""

    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []


def _build_tools(
    agent: Dict[str, Any],
    recorder: ToolEventRecorder,
) -> List[BaseTool]:
    tools: List[BaseTool] = []
    agent_name = agent.get("name") or "Agent"
    skills = agent.get("skills") or []

    if skills:
        skills_map = {skill["name"]: skill for skill in skills}
        skill_catalog = "\n".join(
            f"- {skill['name']}: {skill.get('description', '')}" for skill in skills
        )

        def execute_skill(command: str) -> str:
            skill = skills_map.get(command)
            if not skill:
                return f"Unknown skill: {command}"
            return read_skill_entrypoint(skill["id"], skill.get("content", ""))

        def execute_skill_file(skill_name: str, path: str) -> str:
            skill = skills_map.get(skill_name)
            if not skill:
                return f"Unknown skill: {skill_name}"
            try:
                return read_skill_file(skill["id"], path)
            except ValueError as exc:
                return json.dumps({"error": str(exc)}, ensure_ascii=False)

        tools.extend(
            [
                PlatformTool(
                    name="Skill",
                    description=(
                        "读取并执行一个 Skill 的完整指令。可用 Skill：\n" + skill_catalog
                    ),
                    args_schema=SkillCommand,
                    executor=execute_skill,
                    agent_name=agent_name,
                    recorder=recorder,
                    source_type="skill",
                ),
                PlatformTool(
                    name="SkillFile",
                    description="读取已启用 Skill 包中的 references 等文本文件。",
                    args_schema=SkillFileCommand,
                    executor=execute_skill_file,
                    agent_name=agent_name,
                    recorder=recorder,
                    source_type="skill",
                ),
            ]
        )

    for mcp_config in agent.get("mcps") or []:
        try:
            client = McpClient(mcp_config["base_url"], mcp_config.get("endpoint") or "/mcp")
            for definition in client.list_tools():
                tool_name = definition["name"]

                def make_executor(mcp_client: McpClient, name: str) -> Callable[..., str]:
                    def execute(**kwargs: Any) -> str:
                        return mcp_client.call_tool(name, kwargs)

                    return execute

                tools.append(
                    PlatformTool(
                        name=tool_name,
                        description=definition.get("description") or f"MCP tool {tool_name}",
                        args_schema=_args_model(tool_name, definition.get("inputSchema")),
                        executor=make_executor(client, tool_name),
                        agent_name=agent_name,
                        recorder=recorder,
                        source_type="mcp",
                        source_id=mcp_config["id"],
                    )
                )
            log.info("[CrewAI][MCP] %s 工具发现完成", mcp_config["name"])
        except Exception as exc:
            log.warning("[CrewAI][MCP] %s 连接失败: %s", mcp_config.get("name"), exc)

    return tools


def _build_llm(agent: Dict[str, Any]) -> LLM:
    temperature = agent.get("temperature")
    return LLM(
        model=agent.get("model") or DEEPSEEK_MODEL,
        provider="openai",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=float(0.7 if temperature is None else temperature),
        api="completions",
        custom_openai=True,
    )


def _build_agent(
    definition: Dict[str, Any],
    recorder: ToolEventRecorder,
    allow_delegation: bool,
) -> Agent:
    name = definition.get("name") or "Agent"
    role = definition.get("role") or name
    description = definition.get("goal") or definition.get("description") or f"完成分配给 {name} 的任务"
    backstory = definition.get("backstory") or definition.get("description") or description
    if definition.get("system_prompt"):
        backstory = f"{backstory}\n\n额外行为规则：\n{definition['system_prompt']}"
    max_iter = max(1, min(int(definition.get("iteration_count") or MAX_TOOL_ROUNDS), 100))
    return Agent(
        role=role,
        goal=description,
        backstory=backstory,
        llm=_build_llm(definition),
        tools=_build_tools(definition, recorder),
        allow_delegation=allow_delegation or bool(definition.get("allow_delegation")),
        max_iter=max_iter,
        verbose=False,
        cache=False,
        inject_date=True,
        respect_context_window=True,
        reasoning=bool(definition.get("reasoning", False)),
        planning=bool(definition.get("planning", False)),
        memory=bool(definition.get("memory", False)),
    )


def _task_description(user_message: str, history_messages: List[Dict[str, str]]) -> str:
    history = "\n".join(
        f"{('用户' if item.get('role') == 'user' else '助手')}: {item.get('content', '')}"
        for item in history_messages
    )
    if not history:
        history = "（无历史对话）"
    return (
        f"当前日期：{datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"历史对话：\n{history}\n\n"
        f"用户本轮请求：\n{user_message}\n\n"
        "请结合历史上下文完成本轮请求。需要时调用工具或委派给合适的协作 Agent，"
        "最终只输出直接面向用户的完整答案。"
    )


async def _flush_tool_events(trace_id: Optional[int], events: List[Dict[str, Any]]) -> None:
    for index, event in enumerate(events, start=1):
        await _trace_span(
            trace_id,
            span_type="tool",
            name=f"{event['agent_name']} · {event['tool_name']}",
            round_no=index,
            status=event["status"],
            input_data=event["input"],
            output_data=event["output"],
            error_text=event["error"],
            started_at=event["started_at"],
            duration_ms=event["duration_ms"],
        )


def _render_task_text(template: str, user_message: str, history_messages: List[Dict[str, str]]) -> str:
    history = "\n".join(
        f"{item.get('role', 'user')}: {item.get('content', '')}" for item in history_messages
    ) or "（无历史对话）"
    rendered = (template or "处理用户请求：{{ user_input }}").replace("{{ user_input }}", user_message)
    rendered = rendered.replace("{{ history }}", history)
    if "{{ user_input }}" not in (template or ""):
        rendered += f"\n\n本轮用户输入：\n{user_message}"
    return rendered


def _restricted_task_tools(
    task_definition: Dict[str, Any],
    agent_definition: Optional[Dict[str, Any]],
    recorder: ToolEventRecorder,
) -> Optional[List[BaseTool]]:
    skill_ids = set(task_definition.get("skill_ids") or [])
    mcp_ids = set(task_definition.get("mcp_ids") or [])
    if not skill_ids and not mcp_ids:
        return None
    if not agent_definition:
        return []
    filtered = dict(agent_definition)
    filtered["skills"] = (
        [item for item in agent_definition.get("skills", []) if item["id"] in skill_ids]
        if skill_ids else agent_definition.get("skills", [])
    )
    filtered["mcps"] = (
        [item for item in agent_definition.get("mcps", []) if item["id"] in mcp_ids]
        if mcp_ids else agent_definition.get("mcps", [])
    )
    return _build_tools(filtered, recorder)


async def run_crew(
    crew_definition: Dict[str, Any],
    user_message: str,
    history_messages: List[Dict[str, str]],
    trace_id: Optional[int] = None,
    event_queue: Optional[asyncio.Queue] = None,
) -> str:
    """Build and run a persisted Crew definition."""
    process_name = crew_definition.get("process", "sequential")
    recorder = ToolEventRecorder()
    agent_definitions = {item["id"]: item for item in crew_definition.get("agents", [])}
    crew_agents = {
        agent_id: _build_agent(definition, recorder, allow_delegation=False)
        for agent_id, definition in agent_definitions.items()
    }
    if not crew_agents:
        raise ValueError("Crew 没有可执行的 Agent")

    task_definitions = sorted(
        crew_definition.get("tasks") or [], key=lambda item: (item.get("order_no", 1), item.get("id", 0))
    )
    if not task_definitions:
        first_agent_id = next(iter(crew_agents))
        task_definitions = [{
            "id": 0,
            "name": "处理用户请求",
            "description": "结合历史对话处理用户请求：{{ user_input }}\n\n历史：\n{{ history }}",
            "expected_output": "直接面向用户的完整最终回答",
            "agent_id": first_agent_id if process_name == "sequential" else None,
            "dependency_ids": [],
            "skill_ids": [],
            "mcp_ids": [],
            "markdown": True,
            "max_retries": 2,
        }]

    crew_tasks: Dict[int, Task] = {}
    ordered_tasks: List[Task] = []
    for definition in task_definitions:
        agent_id = definition.get("agent_id")
        agent_object = crew_agents.get(agent_id)
        task_kwargs: Dict[str, Any] = {
            "name": definition.get("name"),
            "description": _render_task_text(
                definition.get("description", ""), user_message, history_messages
            ),
            "expected_output": _render_task_text(
                definition.get("expected_output", "完整结果"), user_message, history_messages
            ),
            "agent": agent_object,
            "async_execution": bool(definition.get("async_execution", False)),
            "markdown": bool(definition.get("markdown", True)),
            "max_retries": int(definition.get("max_retries", 2)),
        }
        restricted_tools = _restricted_task_tools(
            definition, agent_definitions.get(agent_id), recorder
        )
        if restricted_tools is not None:
            task_kwargs["tools"] = restricted_tools
        if definition.get("output_file"):
            task_kwargs["output_file"] = definition["output_file"]
        task_object = Task(**task_kwargs)
        crew_tasks[int(definition.get("id", 0))] = task_object
        ordered_tasks.append(task_object)

    for definition, task_object in zip(task_definitions, ordered_tasks):
        task_object.context = [
            crew_tasks[item_id]
            for item_id in definition.get("dependency_ids", [])
            if item_id in crew_tasks
        ] or None

    manager_agent = None
    runtime_agents = list(crew_agents.values())
    if process_name == "hierarchical":
        manager_id = crew_definition.get("manager_agent_id")
        manager_definition = agent_definitions.get(manager_id)
        if not manager_definition:
            raise ValueError("层级 Crew 缺少 Manager Agent")
        manager_agent = _build_agent(manager_definition, recorder, allow_delegation=True)
        runtime_agents = [agent for agent_id, agent in crew_agents.items() if agent_id != manager_id]
        if not runtime_agents:
            raise ValueError("层级 Crew 缺少协作 Agent")

    await _trace_span(
        trace_id,
        span_type="crew_setup",
        name=f"Crew · {crew_definition.get('name')}",
        status="success",
        input_data={"process": process_name, "message": user_message},
        output_data={
            "agents": [item.get("name") for item in agent_definitions.values()],
            "tasks": [item.get("name") for item in task_definitions],
        },
    )
    await _emit_runtime_event(
        event_queue,
        "status",
        f"正在准备 Crew：{crew_definition.get('name') or 'Crew'}",
        stage="crew_setup",
    )
    crew_kwargs: Dict[str, Any] = {
        "name": crew_definition.get("name") or "Crew",
        "agents": runtime_agents,
        "tasks": ordered_tasks,
        "process": Process.hierarchical if process_name == "hierarchical" else Process.sequential,
        "manager_agent": manager_agent,
        "planning": bool(crew_definition.get("planning", False)),
        "memory": bool(crew_definition.get("memory", False)),
        "cache": bool(crew_definition.get("cache_enabled", False)),
        "verbose": bool(crew_definition.get("verbose", False)),
        "max_rpm": crew_definition.get("max_rpm"),
        "share_crew": False,
        "tracing": False,
        "stream": event_queue is not None,
    }
    crew = Crew(**crew_kwargs)
    started = time.time()
    try:
        execution = await crew.kickoff_async()
        if event_queue is not None:
            current_stream_phase: Optional[tuple] = None
            async for stream_chunk in execution:
                chunk_type = getattr(getattr(stream_chunk, "chunk_type", None), "value", "text")
                task_index = int(getattr(stream_chunk, "task_index", 0) or 0)
                task_name = getattr(stream_chunk, "task_name", "") or (
                    task_definitions[task_index].get("name", "")
                    if task_index < len(task_definitions) else ""
                )
                agent_role = getattr(stream_chunk, "agent_role", "") or ""
                stream_phase = (task_index, agent_role)
                if stream_phase != current_stream_phase:
                    current_stream_phase = stream_phase
                    phase_label = f"正在执行 Task：{task_name or task_index + 1}"
                    if agent_role:
                        phase_label += f"（{agent_role}）"
                    await _emit_runtime_event(
                        event_queue,
                        "phase_start",
                        phase_label,
                        stage="task",
                        task_index=task_index,
                        task_name=task_name,
                        agent_role=agent_role,
                    )
                if chunk_type == "tool_call":
                    tool_call = getattr(stream_chunk, "tool_call", None)
                    tool_name = getattr(tool_call, "tool_name", "") or getattr(tool_call, "name", "")
                    await _emit_runtime_event(
                        event_queue,
                        "status",
                        f"正在调用工具{f'：{tool_name}' if tool_name else ''}",
                        stage="tool",
                        task_name=task_name,
                        agent_role=agent_role,
                    )
                    continue
                content = getattr(stream_chunk, "content", "")
                if content:
                    await _emit_runtime_event(
                        event_queue,
                        "chunk",
                        content,
                        stage="task",
                        task_index=task_index,
                        task_name=task_name,
                        agent_role=agent_role,
                    )
            output = execution.result
        else:
            output = execution
    except Exception as exc:
        await _flush_tool_events(trace_id, recorder.events)
        await _trace_span(
            trace_id,
            span_type="crew",
            name=f"Crew · {crew_definition.get('name')}",
            status="error",
            input_data={"message": user_message},
            error_text=str(exc),
            duration_ms=int((time.time() - started) * 1000),
        )
        raise

    await _flush_tool_events(trace_id, recorder.events)
    for definition, task_output in zip(task_definitions, getattr(output, "tasks_output", [])):
        await _trace_span(
            trace_id,
            task_id=definition.get("id") or None,
            agent_id=definition.get("agent_id"),
            span_type="task",
            name=f"Task · {definition.get('name')}",
            status="success",
            input_data={"description": definition.get("description")},
            output_data={"content": getattr(task_output, "raw", str(task_output))},
        )
    final_text = output.raw if hasattr(output, "raw") else str(output)
    await _trace_span(
        trace_id,
        span_type="crew",
        name=f"Crew · {crew_definition.get('name')}",
        status="success",
        input_data={"message": user_message},
        output_data={"content": final_text},
        duration_ms=int((time.time() - started) * 1000),
    )
    return final_text


def _edge_matches(edge: Dict[str, Any], value: str) -> bool:
    condition_type = edge.get("condition_type", "always")
    expected = edge.get("condition_value") or ""
    if condition_type == "always":
        return True
    if condition_type == "equals":
        return value.strip() == expected.strip()
    if condition_type == "contains":
        return expected in value
    if condition_type == "not_contains":
        return expected not in value
    return False


async def run_flow(
    flow_definition: Dict[str, Any],
    user_id: int,
    user_message: str,
    history_messages: List[Dict[str, str]],
    trace_id: Optional[int] = None,
    event_queue: Optional[asyncio.Queue] = None,
) -> str:
    """Execute a persisted Flow graph and pass state between Crew nodes."""
    from .services.crew_service import get_crew

    nodes = {item["node_key"]: item for item in flow_definition.get("nodes", [])}
    edges = flow_definition.get("edges", [])
    incoming = {key: 0 for key in nodes}
    for edge in edges:
        incoming[edge["target_key"]] = incoming.get(edge["target_key"], 0) + 1
    starts = [key for key, count in incoming.items() if count == 0]
    if not starts:
        raise ValueError("Flow 没有开始节点或存在闭环")
    current_key = starts[0]
    state_value = user_message
    visited = 0
    max_steps = max(1, len(nodes) * 3)
    while current_key and visited < max_steps:
        visited += 1
        node = nodes[current_key]
        started = time.time()
        await _emit_runtime_event(
            event_queue,
            "status",
            f"正在执行 Flow 节点：{node['name']}",
            stage="flow_node",
            node_key=current_key,
            node_type=node["node_type"],
        )
        if node["node_type"] == "crew":
            if not node.get("crew_id"):
                raise ValueError(f"Flow 节点“{node['name']}”未配置 Crew")
            crew = await get_crew(node["crew_id"], user_id, runtime=True)
            if not crew:
                raise ValueError(f"Flow 节点“{node['name']}”引用的 Crew 不存在")
            state_value = await run_crew(
                crew,
                state_value,
                history_messages,
                trace_id,
                event_queue,
            )
        elif node["node_type"] == "transform":
            config = node.get("config") or {}
            state_value = f"{config.get('prefix', '')}{state_value}{config.get('suffix', '')}"
        elif node["node_type"] == "approval":
            state_value = f"流程在“{node['name']}”等待人工审批。当前结果：\n{state_value}"
            await _trace_span(
                trace_id,
                span_type="approval",
                name=f"Flow · {node['name']}",
                status="paused",
                output_data={"content": state_value},
            )
            break
        elif node["node_type"] == "end":
            await _trace_span(
                trace_id,
                span_type="flow_node",
                name=f"Flow · {node['name']}",
                status="success",
                input_data={"node_type": "end"},
                output_data={"content": state_value},
                duration_ms=int((time.time() - started) * 1000),
            )
            break
        await _trace_span(
            trace_id,
            span_type="flow_node",
            name=f"Flow · {node['name']}",
            status="success",
            input_data={"node_type": node["node_type"]},
            output_data={"content": state_value},
            duration_ms=int((time.time() - started) * 1000),
        )
        outgoing = sorted(
            [edge for edge in edges if edge["source_key"] == current_key],
            key=lambda item: (item.get("priority", 0), item.get("id", 0)),
        )
        next_edge = next((edge for edge in outgoing if _edge_matches(edge, state_value)), None)
        current_key = next_edge["target_key"] if next_edge else None
    if visited >= max_steps and current_key:
        raise ValueError("Flow 超过最大节点执行次数，请检查循环配置")
    return state_value


async def chat_stream(
    target_type: str,
    target_definition: Dict[str, Any],
    user_id: int,
    user_message: str,
    history_messages: List[Dict[str, str]],
    session_id: int,
    trace_id: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    if not DEEPSEEK_API_KEY:
        yield _sse_event("chunk", "API Key 未配置")
        yield _sse_event("done")
        return
    event_queue: asyncio.Queue = asyncio.Queue()

    async def execute_target() -> str:
        if target_type == "crew":
            return await run_crew(
                target_definition,
                user_message,
                history_messages,
                trace_id,
                event_queue,
            )
        if target_type == "flow":
            return await run_flow(
                target_definition,
                user_id,
                user_message,
                history_messages,
                trace_id,
                event_queue,
            )
        raise ValueError(f"不支持的执行目标: {target_type}")

    execution_task = asyncio.create_task(execute_target())
    try:
        while not execution_task.done() or not event_queue.empty():
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=0.2)
            except asyncio.TimeoutError:
                continue
            yield _sse_event(
                event.pop("type"),
                event.pop("content", ""),
                **event,
            )
        final_text = await execution_task
    finally:
        if not execution_task.done():
            execution_task.cancel()
    log.info("[CrewAI][会话#%s] target=%s:%s", session_id, target_type, target_definition.get("name"))
    yield _sse_event("result", final_text or "")
    yield _sse_event("done")
