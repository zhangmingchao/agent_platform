"""多 Agent 工作流持久化与运行时服务。"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from ..core.agent_factory import create_agent_instance, get_model_name
from ..core.agent_state import build_agent_state, update_agent_checkpoint_state
from ..core.agent_output import append_schema_instruction, parse_and_validate_structured_output, render_prompt_template
from ..runtime.models import RuntimeContext
from ..core.event_publisher import RedisStreamEventPublisher
from ..core.trace_handler import TraceContext
from ..core.workflow_checkpointer import get_workflow_checkpointer
from ..core.workflow_native_engine import (
    NativeWorkflowEngine,
    NativeWorkflowState,
)
from ..core.workflow_graph import (
    normalize_workflow_steps as _normalize_steps,
    parse_workflow_config as _parse_config,
)
from ..core.workflow_state import workflow_graph_config
from ..models.agent import Agent
from ..models.workflow import WorkflowResumeContext, WorkflowRun
from ..database import execute, fetch_all
from ..repositories.workflow_repository import find_workflow_run_entity
from .agent_service import get_agent
from .mcp_config_service import get_agent_mcps
from .model_service import get_model
from .skill_service import get_agent_skills
from .workflow_definition_service import (
    create_workflow,
    delete_workflow,
    get_workflow,
    list_workflows,
    update_workflow,
)

MAX_STEP_INPUT_CHARS = 12000


class WorkflowApprovalRequired(Exception):
    """人工确认节点暂停执行时使用的内部控制流异常。"""

    def __init__(self, result: Dict) -> None:
        super().__init__("工作流等待人工确认")
        self.result = result


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


# ── 模型 / Agent 加载辅助函数 ──────────────────────────────────────

async def _load_model_config(agent: Agent, user_id: int) -> Optional[Dict]:
    """加载 Agent 实体关联的模型配置。"""
    if not agent.model_config_id:
        return None
    return await get_model(agent.model_config_id, user_id)


# ── Agent 节点执行 ─────────────────────────────────────────────────────

async def _invoke_agent_step(
    *,
    agent: Agent,
    user_id: int,
    workflow_id: int,
    run_id: int,
    workflow_step_id: int,
    step_order: int,
    role: str,
    instruction: str,
    input_text: str,
    node_id: str,
    publisher: RedisStreamEventPublisher,
) -> tuple[str, int, Optional[Dict]]:
    """执行一个 Agent 节点，并将模型及工具事件统一交给 EventPublisher。

    返回节点最终文本、Trace Run ID 和可选结构化结果。这里不直接处理 SSE，确保同一套执行逻辑可以
    服务于后台任务、事件订阅以及未来的独立 Worker。
    """
    # 每次执行时根据 Agent 配置装配 Skill、MCP 工具和模型。
    skills_data = await get_agent_skills(agent.id)
    mcps_data = await get_agent_mcps(agent.id)
    model_config = await _load_model_config(agent, user_id)
    rendered_prompt = render_prompt_template(
        agent.system_prompt,
        agent.prompt_variables,
        {
            "user_input": input_text,
            "workflow_input": input_text,
            "workflow_id": workflow_id,
            "run_id": run_id,
            "step_order": step_order,
            "role": role,
            "instruction": instruction,
            "user_id": user_id,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
        },
    )
    runtime_agent = agent.with_system_prompt(
        append_schema_instruction(rendered_prompt, agent.output_schema),
    )
    agent_executor = await create_agent_instance(
        runtime_agent,
        skills_data,
        mcps_data,
        model_config,
        runtime_context=RuntimeContext(
            user_id=user_id,
            workspace_id=f"workflow-{workflow_id}",
            workflow_run_id=run_id,
            workflow_step_id=workflow_step_id,
            node_id=node_id,
        ),
    )

    prompt_parts = [
        f"你是多 Agent 工作流中的第 {step_order} 个执行者，角色是：{role}。",
        "请只完成当前步骤，不要假装已经执行后续步骤。",
    ]
    if instruction:
        prompt_parts.append(f"当前步骤指令：\n{instruction}")
    prompt_parts.append(f"工作流当前输入：\n{input_text[:MAX_STEP_INPUT_CHARS]}")
    prompt = "\n\n".join(prompt_parts)

    trace_ctx = TraceContext(
        session_id=None,
        user_id=user_id,
        agent_id=agent.id,
        model_name=get_model_name(runtime_agent, model_config),
        workflow_run_id=run_id,
        workflow_step_id=workflow_step_id,
    )
    trace_run_id = await trace_ctx.start(prompt)
    await execute(
        "UPDATE multi_agent_run_steps SET trace_run_id=%s WHERE id=%s",
        (trace_run_id, workflow_step_id),
    )

    config = {
        "configurable": {"thread_id": f"workflow_{workflow_id}_run_{run_id}_step_{step_order}"},
        "recursion_limit": max(8, min(agent.iteration_count * 2 + 5, 80)),
    }

    # token 既实时发布到 Stream，也在服务端拼接成节点最终输出用于持久化。
    full_response = []
    current_llm_chunks = []
    last_final_response = ""
    try:
        # 工作流 Agent 节点沿用原消息输入，同时将节点上下文写入自定义 State。
        initial_state = build_agent_state(
            [HumanMessage(content=prompt)],
            available_skills=[item["name"] for item in skills_data],
            current_input=input_text,
            current_node_id=node_id,
        )
        async for event in agent_executor.astream_events(
            initial_state,
            config=config,
            version="v2",
        ):
            kind = event["event"]
            event_run_id = event.get("run_id", "")

            if kind == "on_chat_model_start":
                current_llm_chunks = []
                model_name = event.get("name", "LLM")
                input_data = str(event.get("data", {}).get("input", ""))
                await trace_ctx.on_llm_start(event_run_id, model_name, input_data)

            elif kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and chunk.content:
                    full_response.append(chunk.content)
                    current_llm_chunks.append(chunk.content)
                    await publisher.publish(
                        "token",
                        {"node_id": node_id, "content": chunk.content},
                        node_id=node_id,
                    )

            elif kind == "on_chat_model_end":
                raw_output = event.get("data", {}).get("output")
                output = str(raw_output or "")
                await trace_ctx.on_llm_end(event_run_id, output)
                if not (getattr(raw_output, "tool_calls", None) or []):
                    last_final_response = "".join(current_llm_chunks).strip()

            elif kind == "on_tool_start":
                tool_name = event.get("name", "")
                input_data = str(event.get("data", {}).get("input", ""))
                await trace_ctx.on_tool_start(event_run_id, tool_name, input_data)
                await publisher.publish(
                    "tool_start",
                    {"node_id": node_id, "tool": tool_name},
                    node_id=node_id,
                )

            elif kind == "on_tool_end":
                output = event.get("data", {}).get("output", "")
                if hasattr(output, "content"):
                    output_str = str(output.content)
                else:
                    output_str = str(output)
                await trace_ctx.on_tool_end(event_run_id, output_str)
                await publisher.publish(
                    "tool_end",
                    {
                        "node_id": node_id,
                        "tool": event.get("name", ""),
                        "output": output_str[:200],
                    },
                    node_id=node_id,
                )

        output_text = last_final_response or "".join(full_response).strip()
        if not output_text:
            output_text = "工作流步骤未产生文本输出"
        await trace_ctx.finish(output_text)
        structured_output = parse_and_validate_structured_output(
            output_text, agent.output_schema,
        )
        if structured_output is not None:
            # 同步到当前线程 Checkpoint，不改变工作流原有 MySQL 结果持久化方式。
            await update_agent_checkpoint_state(
                agent_executor,
                config["configurable"]["thread_id"],
                {"structured_result": structured_output},
            )
            await publisher.publish(
                "structured_result",
                {"node_id": node_id, "data": structured_output},
                node_id=node_id,
            )
        return output_text, trace_run_id, structured_output
    except Exception as exc:
        await trace_ctx.error(str(exc))
        raise


async def _execute_native_agent_node(
    node: Dict[str, Any],
    state: NativeWorkflowState,
    input_text: str,
    step_order: int,
) -> str:
    """执行动态 LangGraph 中的一个 Agent 节点。

    参数：
    - ``node``：前端工作流中的 Agent 节点配置；
    - ``state``：当前原生 LangGraph State；
    - ``input_text``：根据前驱节点输出计算出的输入；
    - ``step_order``：编译阶段分配的稳定节点序号。

    返回值：Agent 节点的最终文本输出。
    """
    data = node.get("data") or {}
    node_id = str(node["id"])
    agent_id = data.get("agent_id") or node.get("agent_id")
    agent = await get_agent(agent_id, state["user_id"])
    if not agent:
        raise HTTPException(status_code=400, detail=f"Agent 不存在或无权限: {agent_id}")
    role = str(data.get("role") or data.get("label") or node_id)[:100]
    instruction = str(data.get("instruction") or "").strip()
    publisher = RedisStreamEventPublisher(state["run_id"])
    await execute(
        "UPDATE multi_agent_runs SET current_node_id=%s WHERE id=%s",
        (node_id, state["run_id"]),
    )
    await publisher.publish(
        "node_start",
        {
            "node_id": node_id,
            "node_type": "agent",
            "label": role,
            "step_order": step_order,
        },
        node_id=node_id,
    )
    step_id = await execute(
        "INSERT INTO multi_agent_run_steps "
        "(run_id, step_order, agent_id, node_id, node_type, role_name, "
        "instruction, input_text, status, started_at, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            state["run_id"],
            step_order,
            agent.id,
            node_id,
            "agent",
            role,
            instruction,
            input_text,
            "running",
            _now(),
            _now(),
        ),
    )
    try:
        output_text, trace_run_id, structured_output = await _invoke_agent_step(
            agent=agent,
            user_id=state["user_id"],
            workflow_id=state["workflow_id"],
            run_id=state["run_id"],
            workflow_step_id=step_id,
            step_order=step_order,
            role=role,
            instruction=instruction,
            input_text=input_text,
            node_id=node_id,
            publisher=publisher,
        )
    except Exception as exc:
        await execute(
            "UPDATE multi_agent_run_steps SET status=%s, error_text=%s, "
            "finished_at=%s WHERE id=%s",
            ("error", str(exc), _now(), step_id),
        )
        raise
    await execute(
        "UPDATE multi_agent_run_steps SET output_text=%s, output_json=%s, "
        "trace_run_id=%s, status=%s, finished_at=%s WHERE id=%s",
        (
            output_text,
            json.dumps(structured_output, ensure_ascii=False)
            if structured_output is not None
            else None,
            trace_run_id,
            "success",
            _now(),
            step_id,
        ),
    )
    await publisher.publish(
        "node_done",
        {"node_id": node_id, "output": output_text},
        node_id=node_id,
    )
    return output_text


async def _prepare_native_approval_node(
    node: Dict[str, Any],
    state: NativeWorkflowState,
    input_text: str,
    step_order: int,
) -> WorkflowResumeContext:
    """持久化原生 LangGraph 审批节点的暂停现场。

    参数：
    - ``node``：前端审批节点配置；
    - ``state``：当前原生 LangGraph State；
    - ``input_text``：审批页面展示的上游输出；
    - ``step_order``：编译阶段分配的稳定节点序号。
    """
    node_id = str(node["id"])
    data = node.get("data") or {}
    label = str(data.get("label") or "人工确认")[:100]
    prompt = str(data.get("prompt") or "请确认是否继续执行此工作流").strip()
    next_targets = _all_targets(state["workflow_config"], node_id)
    resume_node_id = next_targets[0] if next_targets else None
    step_id = await execute(
        "INSERT INTO multi_agent_run_steps "
        "(run_id, step_order, agent_id, node_id, node_type, role_name, instruction, "
        "input_text, status, started_at, created_at) "
        "VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            state["run_id"],
            step_order,
            node_id,
            "approval",
            label,
            prompt,
            input_text,
            "waiting_approval",
            _now(),
            _now(),
        ),
    )
    context = WorkflowResumeContext(
        approval_step_id=step_id,
        approval_node_id=node_id,
        approval_label=label,
        approval_prompt=prompt,
        resume_node_id=resume_node_id,
        current_input=input_text,
        step_counter=step_order,
    )
    await execute(
        "UPDATE multi_agent_runs SET status=%s, current_node_id=%s, context_json=%s WHERE id=%s",
        (
            "waiting_approval",
            node_id,
            json.dumps(context.to_dict(), ensure_ascii=False),
            state["run_id"],
        ),
    )
    publisher = RedisStreamEventPublisher(state["run_id"])
    await publisher.publish(
        "approval_required",
        {
            "run_id": state["run_id"],
            "step_id": step_id,
            "node_id": node_id,
            "label": label,
            "prompt": prompt,
            "input": input_text,
        },
        node_id=node_id,
    )
    return context


# ── 工作流运行管理 ────────────────────────────────────────────────────

async def run_workflow(workflow_id: int, user_id: int, input_text: str) -> Dict:
    workflow = await get_workflow(workflow_id, user_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    if not workflow.get("is_active", 1):
        raise HTTPException(status_code=400, detail="工作流已停用")

    run_id = await create_workflow_run(workflow_id, user_id, input_text)
    return await execute_workflow_run(run_id, user_id)


async def create_workflow_run(workflow_id: int, user_id: int, input_text: str) -> int:
    """校验工作流并创建一条运行记录，返回新生成的 run_id。"""
    workflow = await get_workflow(workflow_id, user_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    if not workflow.get("is_active", 1):
        raise HTTPException(status_code=400, detail="工作流已停用")
    _normalize_steps(workflow["config"])

    now = _now()
    return await execute(
        "INSERT INTO multi_agent_runs "
        "(workflow_id, user_id, status, workflow_config_json, input_text, started_at, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            workflow_id,
            user_id,
            "running",
            json.dumps(workflow["config"], ensure_ascii=False),
            input_text,
            now,
            now,
        ),
    )


async def execute_workflow_run(run_id: int, user_id: int) -> Dict:
    """使用稳定 thread_id 启动工作流级 StateGraph。"""
    return await resume_workflow_graph(run_id, user_id)


async def resume_workflow_graph(
    run_id: int,
    user_id: int,
    resume_decision: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """首次运行或通过 ``Command(resume=...)`` 恢复同一工作流线程。

    参数：
    - ``run_id``：需要启动或恢复的工作流运行记录 ID；
    - ``user_id``：当前用户 ID，用于校验运行记录归属；
    - ``resume_decision``：人工审批恢复参数，首次执行时为 ``None``。

    返回值：工作流当前状态、输入、输出等运行结果。
    """
    run: Optional[WorkflowRun] = await find_workflow_run_entity(run_id, user_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    if run.status != "running":
        return {
            "run_id": run.id,
            "workflow_id": run.workflow_id,
            "status": run.status,
            "input": run.input_text,
            "output": run.output_text,
            "error_text": run.error_text,
            "steps": run.steps,
        }

    workflow_id: int = run.workflow_id
    publisher: RedisStreamEventPublisher = RedisStreamEventPublisher(run_id)

    try:
        try:
            workflow_config_value: Dict[str, Any] = run.require_workflow_config()
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        workflow_config: Dict[str, Any] = _parse_config(workflow_config_value)
        checkpointer: BaseCheckpointSaver[str] = get_workflow_checkpointer()
        engine = NativeWorkflowEngine(
            workflow_config,
            publisher,
            _execute_native_agent_node,
            _prepare_native_approval_node,
        )
        graph: CompiledStateGraph = engine.compile(checkpointer)
        graph_config: Dict[str, Any] = workflow_graph_config(run_id)
        if resume_decision is None:
            # start 只在首次执行时发布，审批恢复不会生成第二条开始事件。
            await publisher.publish(
                "start",
                {"run_id": run_id, "workflow_id": workflow_id, "input": run.input_text},
            )
            graph_input: NativeWorkflowState | Command[Any] = {
                "run_id": run_id,
                "workflow_id": workflow_id,
                "user_id": user_id,
                "workflow_config": workflow_config,
                "initial_input": run.input_text,
                "state_version": 1,
                "node_outputs": {},
                "status": "running",
            }
        else:
            graph_input = Command(resume=resume_decision)

        result: Dict[str, Any] = await graph.ainvoke(
            graph_input,
            config=graph_config,
        )
        if result.get("__interrupt__") or result.get("status") == "waiting_approval":
            return {
                "run_id": run_id,
                "workflow_id": workflow_id,
                "status": "waiting_approval",
                "input": result.get("approval_input", run.input_text),
                "output": result.get("output", result.get("approval_input", "")),
            }

        if result.get("status") == "rejected":
            output: str = str(result.get("output") or "已拒绝")
            await execute(
                "UPDATE multi_agent_runs SET status=%s, output_text=%s, finished_at=%s, "
                "current_node_id=%s, context_json=NULL WHERE id=%s",
                ("rejected", output, _now(), None, run_id),
            )
            await publisher.publish(
                "rejected", {"run_id": run_id, "status": "rejected", "output": output},
            )
            return {"run_id": run_id, "status": "rejected", "output": output}

        await execute(
            "UPDATE multi_agent_runs SET status=%s, output_text=%s, finished_at=%s, "
            "current_node_id=%s, context_json=NULL WHERE id=%s",
            ("success", result["output"], _now(), None, run_id),
        )
        await publisher.publish(
            "done",
            {"run_id": run_id, "status": "success", "output": result["output"]},
        )
        return {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": "success",
            "input": run.input_text,
            "output": result["output"],
        }
    except Exception as exc:
        # 无论失败发生在 Agent、工具还是事件发布阶段，都要先落库终止 running 状态。
        error_text: str = str(exc)
        await execute(
            "UPDATE multi_agent_runs SET status=%s, error_text=%s, finished_at=%s WHERE id=%s",
            ("error", error_text, _now(), run_id),
        )
        try:
            await publisher.publish(
                "error",
                {"run_id": run_id, "detail": error_text},
            )
        except Exception:
            # 原始异常可能就是 Redis 故障。即使 error 事件无法写入，也必须保留数据库错误状态。
            pass
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {error_text}") from exc


async def start_workflow_run(workflow_id: int, user_id: int, input_text: str) -> Dict:
    """仅创建运行记录，不在当前 HTTP 请求中执行工作流。"""
    run_id = await create_workflow_run(workflow_id, user_id, input_text)
    return {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "status": "running",
        "input": input_text,
    }


async def decide_workflow_approval(
    run_id: int, user_id: int, approved: bool, comment: str = "",
) -> Dict:
    """处理当前待审批节点；批准后恢复运行，拒绝后结束本次运行。"""
    run: Optional[WorkflowRun] = await find_workflow_run_entity(run_id, user_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    if run.status != "waiting_approval":
        raise HTTPException(status_code=409, detail="当前运行不处于待人工确认状态")

    context: WorkflowResumeContext = run.resume_context
    step_id = context.approval_step_id
    if not step_id:
        raise HTTPException(status_code=409, detail="待审批运行缺少恢复信息")

    decision_text = ("已批准" if approved else "已拒绝") + (f"：{comment.strip()}" if comment.strip() else "")
    await execute(
        "UPDATE multi_agent_run_steps SET status=%s, output_text=%s, finished_at=%s "
        "WHERE id=%s AND run_id=%s AND status=%s",
        ("approved" if approved else "rejected", decision_text, _now(), step_id, run_id, "waiting_approval"),
    )
    publisher = RedisStreamEventPublisher(run_id)
    await publisher.publish(
        "approval_decided",
        {
            "run_id": run_id,
            "step_id": step_id,
            "node_id": context.approval_node_id,
            "approved": approved,
            "comment": comment.strip(),
        },
        node_id=context.approval_node_id,
    )
    # 审批结果由 Command(resume=...) 交回同一个 LangGraph thread。这里先把运行状态
    # 原子地切回 running，使后台恢复任务成为唯一负责写入最终状态的执行者。
    await execute(
        "UPDATE multi_agent_runs SET status=%s, current_node_id=%s, context_json=%s, error_text=NULL WHERE id=%s",
        ("running", context.resume_node_id, json.dumps(context.to_dict(), ensure_ascii=False), run_id),
    )
    return {
        "run_id": run_id,
        "status": "running",
        "resume": True,
        "resume_decision": {"approved": approved, "comment": comment.strip()},
    }


async def list_workflow_runs(workflow_id: int, user_id: int) -> List[Dict]:
    workflow = await get_workflow(workflow_id, user_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return await fetch_all(
        "SELECT id, workflow_id, status, input_text, output_text, error_text, "
        "started_at, finished_at, created_at "
        "FROM multi_agent_runs WHERE workflow_id=%s AND user_id=%s ORDER BY created_at DESC",
        (workflow_id, user_id),
    )


async def get_workflow_run(run_id: int, user_id: int) -> Optional[Dict]:
    """查询运行实体，并在 HTTP 服务边界转换为兼容响应。"""
    run = await find_workflow_run_entity(run_id, user_id)
    return run.to_dict() if run else None
