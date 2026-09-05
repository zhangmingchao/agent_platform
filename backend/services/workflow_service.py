"""多 Agent 工作流持久化与运行时服务。"""
import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import HTTPException
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from ..core.agent_factory import create_agent_instance, get_model_name
from ..core.agent_state import build_agent_state, update_agent_checkpoint_state
from ..core.agent_output import append_schema_instruction, parse_and_validate_structured_output, render_prompt_template
from ..runtime.models import RuntimeContext
from ..core.event_publisher import RedisStreamEventPublisher
from ..core.trace_handler import TraceContext
from ..core.workflow_checkpointer import get_workflow_checkpointer
from ..core.workflow_state import (
    WorkflowRuntimeState,
    build_workflow_lifecycle_graph,
    workflow_graph_config,
)
from ..models.agent import Agent
from ..database import execute, fetch_all, fetch_one
from .agent_service import get_agent
from .mcp_config_service import get_agent_mcps
from .model_service import get_model
from .skill_service import get_agent_skills

MAX_WORKFLOW_STEPS = 12
MAX_STEP_INPUT_CHARS = 12000
MAX_GRAPH_STEPS = 40


class WorkflowApprovalRequired(Exception):
    """人工确认节点暂停执行时使用的内部控制流异常。"""

    def __init__(self, result: Dict):
        super().__init__("工作流等待人工确认")
        self.result = result


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _parse_config(config) -> Dict:
    # 对 工作流 中 的配置 节点与连线，json 校验
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="config_json 不是合法 JSON") from exc
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="config 必须是 JSON 对象")
    return config


# ── 顺序配置辅助函数 ──────────────────────────────────────────

def _normalize_steps(config: Dict) -> List[Dict]:
    if _is_graph_config(config):
        return _graph_agent_steps(config)
    steps = config.get("steps", [])
    if not isinstance(steps, list) or not steps:
        raise HTTPException(status_code=400, detail="工作流至少需要一个步骤")
    if len(steps) > MAX_WORKFLOW_STEPS:
        raise HTTPException(status_code=400, detail=f"工作流最多支持 {MAX_WORKFLOW_STEPS} 个步骤")

    normalized = []
    for idx, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise HTTPException(status_code=400, detail=f"第 {idx} 个步骤必须是 JSON 对象")
        agent_id = step.get("agent_id")
        if not isinstance(agent_id, int):
            raise HTTPException(status_code=400, detail=f"第 {idx} 个步骤缺少有效 agent_id")
        normalized.append({
            "agent_id": agent_id,
            "role": str(step.get("role") or f"step_{idx}")[:100],
            "instruction": str(step.get("instruction") or "").strip(),
        })
    return normalized


# ── 图（DAG）配置辅助函数 ─────────────────────────────────────────

def _is_graph_config(config: Dict) -> bool:
    return isinstance(config.get("nodes"), list) and isinstance(config.get("edges"), list)


def _graph_agent_steps(config: Dict) -> List[Dict]:
    steps = []
    for node in config.get("nodes", []):
        if node.get("type") != "agent":
            continue
        data = node.get("data") or {}
        agent_id = data.get("agent_id") or node.get("agent_id")
        if not isinstance(agent_id, int):
            raise HTTPException(status_code=400, detail=f"Agent 节点缺少有效 agent_id: {node.get('id')}")
        steps.append({
            "agent_id": agent_id,
            "role": str(data.get("role") or data.get("label") or node.get("id"))[:100],
            "instruction": str(data.get("instruction") or "").strip(),
            "node_id": node.get("id"),
        })
    if not steps:
        raise HTTPException(status_code=400, detail="图式工作流至少需要一个 Agent 节点")
    if len(steps) > MAX_GRAPH_STEPS:
        raise HTTPException(status_code=400, detail=f"图式工作流最多支持 {MAX_GRAPH_STEPS} 个 Agent 节点")
    return steps


def _graph_nodes(config: Dict) -> Dict[str, Dict]:
    """将节点列表转为 {node_id: node} 的字典，方便 O(1) 查找。"""
    return {node.get("id"): node for node in config.get("nodes", []) if node.get("id")}


def _outgoing_edges(config: Dict, node_id: str) -> List[Dict]:
    """获取指定节点的所有出边（从该节点出发的连线）。"""
    return [edge for edge in config.get("edges", []) if edge.get("source") == node_id]


def _next_node(config: Dict, node_id: str) -> Optional[str]:
    """获取节点的下一个节点（第一条出边的目标）。
    注意：普通 Agent 节点有多条出边时只走第一条，条件/并行节点不走这个函数。"""
    edges = _outgoing_edges(config, node_id)
    return edges[0].get("target") if edges else None


def _all_targets(config: Dict, node_id: str) -> List[str]:
    """获取节点所有下游目标节点 ID（用于并行节点的扇出）。"""
    return [e.get("target") for e in _outgoing_edges(config, node_id) if e.get("target")]


def _start_node_id(config: Dict) -> str:
    """找到 DAG 的入口节点：优先找 type 为 input/start 的节点，没有就取第一个节点。
    注意：多个 input/start 节点时只取第一个，其他会被忽略。"""
    for node in config.get("nodes", []):
        if node.get("type") in ("input", "start"):
            return node.get("id")
    return config.get("nodes", [{}])[0].get("id")


def _evaluate_condition_branch(node: Dict, current_input: str) -> int:
    """根据当前输入文本，按顺序匹配条件分支，返回命中的分支索引。

    匹配规则：
    1. 按条件数组顺序逐一检查，先匹配先命中（短路逻辑）
    2. contains 类型：关键词是否在文本中出现
    3. regex 类型：正则表达式是否匹配
    4. else 类型在第一轮跳过，第二轮兜底
    5. 没有任何 else 且全部未命中时，默认返回第 0 个分支
    """
    data = node.get("data") or {}
    conditions = data.get("conditions") or []
    text = current_input or ""

    # 第一轮：匹配非 else 的条件（contains / regex）
    for i, cond in enumerate(conditions):
        cond_type = cond.get("type", "else")
        if cond_type == "else":
            continue  # else 分支留到第二轮兜底
        value = str(cond.get("value") or "")
        if not value:
            continue
        # 包含关键词匹配
        if cond_type == "contains" and value in text:
            return i
        # 正则匹配
        if cond_type == "regex":
            try:
                if re.search(value, text):
                    return i
            except re.error:
                continue  # 正则写错了就跳过该条件

    # 第二轮：找 else 分支作为默认兜底
    for i, cond in enumerate(conditions):
        if cond.get("type") == "else":
            return i
    # 没有 else 分支时，默认走第 0 条边
    return 0


def _condition_branch_target(config: Dict, node_id: str, branch_idx: int) -> Optional[str]:
    """根据分支索引找到条件节点对应分支的下游目标节点。

    优先按 source_handle（即 cond-0 / cond-1 / ...）精确匹配，
    匹配不到时降级为按边的数组下标取目标（兼容旧数据或单 Handle 场景）。
    """
    edges = _outgoing_edges(config, node_id)
    handle_id = f"cond-{branch_idx}"  # 与前端 ConditionNode 的 Handle id 规则一致
    for edge in edges:
        sh = edge.get("source_handle") or edge.get("sourceHandle")
        if sh == handle_id:
            return edge.get("target")
    # 降级：按边的顺序取（兼容未设置 source_handle 的情况）
    if branch_idx < len(edges):
        return edges[branch_idx].get("target")
    return None


def _find_reachable(config: Dict, start_id: str) -> Set[str]:
    """BFS 广度优先搜索：找出从 start_id 出发能到达的所有节点。
    用于计算并行分支的公共汇合点。"""
    reachable: Set[str] = set()
    queue = [start_id]
    while queue:
        nid = queue.pop(0)
        if nid in reachable:
            continue
        reachable.add(nid)
        for target in _all_targets(config, nid):
            if target not in reachable:
                queue.append(target)
    return reachable


def _find_merge_point(config: Dict, branch_starts: List[str]) -> Optional[str]:
    """寻找并行分支的汇合点：所有分支都能到达的第一个公共节点。

    算法：
    1. 分别计算每个分支起点的可达节点集合
    2. 取所有集合的交集（所有分支都能到达的节点）
    3. 从第一个分支的下游开始 BFS，第一个落在交集中的节点就是汇合点
    4. 这样可以保证是"最早"的汇合点，而不是任意公共节点

    注意：复杂 DAG 中可能不是语义上最合理的汇合点，但对简单菱形结构有效。
    """
    if not branch_starts:
        return None
    # 只有一个分支时直接找下一个节点就行
    if len(branch_starts) == 1:
        return _next_node(config, branch_starts[0])

    # 计算每个分支的可达集合，取交集得到所有分支的公共节点
    reachable_sets = [_find_reachable(config, start) for start in branch_starts]
    common = reachable_sets[0]
    for rs in reachable_sets[1:]:
        common = common & rs  # 集合交集

    if not common:
        return None

    # 从第一个分支的下游开始 BFS，找到第一个公共节点（即最早的汇合点）
    for start in branch_starts:
        queue = list(_all_targets(config, start))
        visited: Set[str] = set()
        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            if nid in common:
                return nid  # 第一个遇到的公共节点就是汇合点
            for target in _all_targets(config, nid):
                if target not in visited:
                    queue.append(target)

    # 兜底：直接取交集中的任意一个
    return next(iter(common)) if common else None


# ── 模型 / Agent 加载辅助函数 ──────────────────────────────────────

async def _load_model_config(agent: Agent, user_id: int) -> Optional[Dict]:
    """加载 Agent 实体关联的模型配置。"""
    if not agent.model_config_id:
        return None
    return await get_model(agent.model_config_id, user_id)


async def _validate_workflow_agents(user_id: int, config: Dict) -> None:
    for step in _normalize_steps(config):
        if not await get_agent(step["agent_id"], user_id):
            raise HTTPException(status_code=400, detail=f"Agent 不存在或无权限: {step['agent_id']}")


# ── 增删改查 ───────────────────────────────────────────────────────────────

async def list_workflows(user_id: int) -> List[Dict]:
    workflows = await fetch_all(
        "SELECT id, name, description, mode, config_json, is_active, created_at, updated_at "
        "FROM multi_agent_workflows WHERE user_id=%s ORDER BY updated_at DESC",
        (user_id,),
    )
    for workflow in workflows:
        workflow["config"] = _parse_config(workflow.pop("config_json"))
    return workflows


async def get_workflow(workflow_id: int, user_id: int) -> Optional[Dict]:
    workflow = await fetch_one(
        "SELECT id, name, description, mode, config_json, is_active, created_at, updated_at "
        "FROM multi_agent_workflows WHERE id=%s AND user_id=%s",
        (workflow_id, user_id),
    )
    if not workflow:
        return None
    workflow["config"] = _parse_config(workflow.pop("config_json"))
    return workflow


async def create_workflow(user_id: int, data: Dict) -> Dict:
    name = str(data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="工作流名称不能为空")

    config = _parse_config(data.get("config") or data.get("config_json") or {})
    _normalize_steps(config)
    await _validate_workflow_agents(user_id, config)

    now = _now()
    workflow_id = await execute(
        "INSERT INTO multi_agent_workflows "
        "(user_id, name, description, mode, config_json, is_active, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (
            user_id,
            name,
            str(data.get("description") or ""),
            str(data.get("mode") or config.get("mode") or "sequential"),
            json.dumps(config, ensure_ascii=False),
            1,
            now,
            now,
        ),
    )
    return await get_workflow(workflow_id, user_id)


async def update_workflow(workflow_id: int, user_id: int, data: Dict) -> Optional[Dict]:
    existing = await get_workflow(workflow_id, user_id)
    if not existing:
        return None

    config = _parse_config(data.get("config") or data.get("config_json") or existing["config"])
    _normalize_steps(config)
    await _validate_workflow_agents(user_id, config)

    name = str(data.get("name", existing["name"])).strip()
    if not name:
        raise HTTPException(status_code=400, detail="工作流名称不能为空")

    await execute(
        "UPDATE multi_agent_workflows SET name=%s, description=%s, mode=%s, "
        "config_json=%s, is_active=%s, updated_at=%s WHERE id=%s AND user_id=%s",
        (
            name,
            str(data.get("description", existing.get("description") or "")),
            str(data.get("mode", existing.get("mode") or config.get("mode") or "sequential")),
            json.dumps(config, ensure_ascii=False),
            int(data.get("is_active", existing.get("is_active", 1))),
            _now(),
            workflow_id,
            user_id,
        ),
    )
    return await get_workflow(workflow_id, user_id)


async def delete_workflow(workflow_id: int, user_id: int) -> bool:
    existing = await get_workflow(workflow_id, user_id)
    if not existing:
        return False
    await execute(
        "DELETE FROM multi_agent_workflows WHERE id=%s AND user_id=%s",
        (workflow_id, user_id),
    )
    return True


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


async def _run_workflow_segment(state: WorkflowRuntimeState) -> Dict:
    """执行工作流直到完成或遇到下一个审批节点。

    当前 DAG 节点执行逻辑继续复用，LangGraph 负责保存运行级 State、暂停点和恢复命令。
    MySQL 仍然保存业务步骤及最终结果，避免把 Checkpoint 当成业务数据库。
    """
    run_id = state["run_id"]
    user_id = state["user_id"]
    workflow_id = state["workflow_id"]
    config = _parse_config(state["workflow_config"])
    publisher = RedisStreamEventPublisher(run_id)

    try:
        if _is_graph_config(config):
            result = await _execute_dag(
                run_id,
                user_id,
                workflow_id,
                config,
                state["initial_input"],
                publisher,
                state.get("resume_context"),
            )
        else:
            result = await _execute_sequential(
                run_id,
                user_id,
                workflow_id,
                config,
                state["initial_input"],
                publisher,
            )
        return {
            "status": "success",
            "output": result["output"],
            "current_input": result["output"],
            "current_node_id": None,
        }
    except WorkflowApprovalRequired as pending:
        # 审批节点已经把恢复游标写入 MySQL；这里将同一份数据写入持久化 State，
        # 随后的 approval 图节点会调用 interrupt() 原生暂停。
        paused_run = await get_workflow_run(run_id, user_id)
        raw_context = (paused_run or {}).get("context_json") or {}
        if isinstance(raw_context, str):
            raw_context = json.loads(raw_context)
        context = dict(raw_context)
        return {
            "status": "waiting_approval",
            "output": pending.result.get("output", state.get("current_input", "")),
            "current_input": context.get("current_input", state.get("current_input", "")),
            "current_node_id": context.get("approval_node_id"),
            "step_counter": int(context.get("step_counter") or state.get("step_counter") or 0),
            "resume_context": context,
            "approval_status": "pending",
            "approval_payload": {
                "run_id": run_id,
                "step_id": context.get("approval_step_id"),
                "node_id": context.get("approval_node_id"),
                "label": context.get("approval_label", "人工确认"),
                "prompt": context.get("approval_prompt", "请确认是否继续执行此工作流"),
                "input": context.get("current_input", state.get("current_input", "")),
            },
        }


async def resume_workflow_graph(
    run_id: int,
    user_id: int,
    resume_decision: Optional[Dict] = None,
) -> Dict:
    """首次运行或通过 ``Command(resume=...)`` 恢复同一工作流线程。"""
    run = await get_workflow_run(run_id, user_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    if run["status"] != "running":
        return {
            "run_id": run["id"],
            "workflow_id": run["workflow_id"],
            "status": run["status"],
            "input": run["input_text"],
            "output": run.get("output_text"),
            "error_text": run.get("error_text"),
            "steps": run.get("steps", []),
        }

    workflow_id = run["workflow_id"]
    publisher = RedisStreamEventPublisher(run_id)

    try:
        graph = build_workflow_lifecycle_graph(
            get_workflow_checkpointer(),
            _run_workflow_segment,
        )
        graph_config = workflow_graph_config(run_id)
        if resume_decision is None:
            # start 只在首次执行时发布，审批恢复不会生成第二条开始事件。
            await publisher.publish(
                "start",
                {"run_id": run_id, "workflow_id": workflow_id, "input": run["input_text"]},
            )
            workflow_config = run.get("workflow_config_json")
            if not workflow_config:
                # 兼容迁移前创建但尚未运行的记录；新记录始终具有配置快照。
                workflow = await get_workflow(workflow_id, user_id)
                if not workflow:
                    raise HTTPException(status_code=404, detail="工作流不存在")
                workflow_config = workflow["config"]
            if isinstance(workflow_config, str):
                workflow_config = json.loads(workflow_config)
            graph_input = {
                "run_id": run_id,
                "workflow_id": workflow_id,
                "user_id": user_id,
                "workflow_config": workflow_config,
                "initial_input": run["input_text"],
                "current_input": run["input_text"],
                "current_node_id": run.get("current_node_id"),
                "step_counter": 0,
                "resume_context": {},
                "status": "running",
            }
        else:
            graph_input = Command(resume=resume_decision)

        result = await graph.ainvoke(graph_input, config=graph_config)
        if result.get("__interrupt__") or result.get("status") == "waiting_approval":
            return {
                "run_id": run_id,
                "workflow_id": workflow_id,
                "status": "waiting_approval",
                "input": result.get("current_input", run["input_text"]),
                "output": result.get("output", result.get("current_input", "")),
            }

        if result.get("status") == "rejected":
            output = result.get("output") or "已拒绝"
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
            "input": run["input_text"],
            "output": result["output"],
        }
    except Exception as exc:
        # 无论失败发生在 Agent、工具还是事件发布阶段，都要先落库终止 running 状态。
        error_text = str(exc)
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


async def _execute_sequential(
    run_id: int, user_id: int, workflow_id: int, config: Dict, initial_input: str,
    publisher: RedisStreamEventPublisher,
) -> Dict:
    """依次执行传统 steps 配置，前一步输出作为后一步输入。"""
    steps = _normalize_steps(config)
    current_input = initial_input
    step_results = []

    for idx, step in enumerate(steps, start=1):
        agent = await get_agent(step["agent_id"], user_id)
        if not agent:
            raise HTTPException(status_code=400, detail=f"Agent 不存在或无权限: {step['agent_id']}")

        node_id = f"step-{idx}"
        # 先发布 node_start，再执行 Agent，使前端能够及时切换节点状态。
        await publisher.publish(
            "node_start",
            {
                "node_id": node_id,
                "node_type": "agent",
                "label": step["role"],
                "step_order": idx,
            },
            node_id=node_id,
        )

        step_id = await execute(
            "INSERT INTO multi_agent_run_steps "
            "(run_id, step_order, agent_id, role_name, instruction, input_text, status, started_at, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                run_id, idx, step["agent_id"], step["role"], step["instruction"],
                current_input, "running", _now(), _now(),
            ),
        )

        try:
            output_text, trace_run_id, structured_output = await _invoke_agent_step(
                agent=agent,
                user_id=user_id,
                workflow_id=workflow_id,
                run_id=run_id,
                workflow_step_id=step_id,
                step_order=idx,
                role=step["role"],
                instruction=step["instruction"],
                input_text=current_input,
                node_id=node_id,
                publisher=publisher,
            )
        except Exception as exc:
            await execute(
                "UPDATE multi_agent_run_steps SET status=%s, error_text=%s, finished_at=%s WHERE id=%s",
                ("error", str(exc), _now(), step_id),
            )
            raise

        await execute(
            "UPDATE multi_agent_run_steps SET output_text=%s, output_json=%s, status=%s, finished_at=%s WHERE id=%s",
            (output_text, json.dumps(structured_output, ensure_ascii=False) if structured_output is not None else None, "success", _now(), step_id),
        )
        step_results.append({
            "step_order": idx,
            "agent_id": step["agent_id"],
            "agent_name": agent.name,
            "role": step["role"],
            "trace_run_id": trace_run_id,
            "output": output_text,
        })
        await publisher.publish(
            "node_done",
            {"node_id": node_id, "output": output_text},
            node_id=node_id,
        )
        current_input = output_text

    return {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "status": "success",
        "input": initial_input,
        "output": current_input,
        "steps": step_results,
    }


# ── DAG 执行（条件分支与并行分支）─────────────────────────────────────

async def _execute_dag(
    run_id: int, user_id: int, workflow_id: int, config: Dict, initial_input: str,
    publisher: RedisStreamEventPublisher,
    resume_context=None,
) -> Dict:
    """DAG 模式工作流的执行入口：找到入口节点，调用 _walk_graph 遍历整张图。

    step_counter 用 list 包装是为了在递归调用 _walk_graph 时能共享计数
    （Python 中 int 是不可变的，用 list 可以在子函数中修改并影响外层）。
    """
    nodes_map = _graph_nodes(config)       # 节点字典，O(1) 查找
    if isinstance(resume_context, str):
        try:
            resume_context = json.loads(resume_context)
        except json.JSONDecodeError:
            resume_context = None
    resume_context = resume_context if isinstance(resume_context, dict) else {}
    start_id = resume_context.get("resume_node_id") or _start_node_id(config)
    resume_input = resume_context.get("current_input", initial_input)
    step_counter = [int(resume_context.get("step_counter") or 0)]

    # 从入口节点开始遍历整个 DAG，得到最终输出
    final_output = await _walk_graph(
        config, nodes_map, start_id, resume_input,
        run_id, user_id, workflow_id, step_counter, publisher,
    )
    return {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "status": "success",
        "input": initial_input,
        "output": final_output,
    }


async def _walk_graph(
    config: Dict,
    nodes_map: Dict[str, Dict],
    node_id: Optional[str],
    current_input: str,
    run_id: int,
    user_id: int,
    workflow_id: int,
    step_counter: list,
    publisher: RedisStreamEventPublisher,
    stop_node_id: Optional[str] = None,
) -> str:
    """DAG 核心遍历函数：从 node_id 出发，沿出边一步步执行，直到遇到 stop_node_id 或终点。

    核心设计：
    - 单 while 循环线性推进，普通节点（input/agent/output）一个接一个走
    - 条件节点：计算分支，跳到对应下游节点继续走
    - 并行节点：递归调用自己，用 asyncio.gather 并发执行所有分支
    - stop_node_id：并行分支的停止标记，每个分支走到汇合点就停，等所有分支完成后
      由外层合并结果，再从汇合点继续往下走

    注意：这是深度优先的线性遍历，不是拓扑排序。简单链/树/菱形 DAG 没问题，
    但复杂 DAG（多个上游汇聚到同一个节点）可能存在执行顺序和结果丢失问题。
    """
    # 已访问节点集合，防止出现环时无限循环
    visited: Set[str] = set()

    # 主循环：逐个节点推进，直到没有下一个节点或到达停止点（并行汇合点）
    while node_id and node_id != stop_node_id:
        # 防环：已访问过的节点不再重复执行（注意：这也意味着汇聚节点的
        # 第二个上游路径到达时会直接 break，可能丢失该路径的输入）
        if node_id in visited:
            break
        visited.add(node_id)

        node = nodes_map.get(node_id)
        if not node:
            break  # 节点不存在就终止（边指向了不存在的节点）

        node_type = node.get("type", "agent")

        # 更新运行记录中的当前节点 ID（前端展示用）
        await execute(
            "UPDATE multi_agent_runs SET current_node_id=%s WHERE id=%s",
            (node_id, run_id),
        )

        # ── input / start 节点：纯路由节点，不执行任何逻辑，直接找下一个 ──
        if node_type in ("input", "start"):
            node_id = _next_node(config, node_id)
            continue

        # ── output 节点：终点，停止遍历 ──
        if node_type == "output":
            break

        # ── Agent 节点：核心执行节点，调用 LLM + Skill 工具 + MCP 工具 ──
        if node_type == "agent":
            step_counter[0] += 1    # 全局步骤序号 +1
            order = step_counter[0]
            data = node.get("data") or {}
            agent_id = data.get("agent_id")

            # 校验 Agent 存在且属于当前用户
            agent = await get_agent(agent_id, user_id)
            if not agent:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent 不存在或无权限: {agent_id}",
                )

            role = str(data.get("role") or data.get("label") or node_id)[:100]
            instruction = str(data.get("instruction") or "").strip()

            # 发布 node_start 事件（前端展示节点开始执行）
            await publisher.publish(
                "node_start",
                {
                    "node_id": node_id,
                    "node_type": "agent",
                    "label": role,
                    "step_order": order,
                },
                node_id=node_id,
            )

            # 写入步骤记录到数据库（running 状态）
            step_id = await execute(
                "INSERT INTO multi_agent_run_steps "
                "(run_id, step_order, agent_id, node_id, node_type, role_name, "
                "instruction, input_text, status, started_at, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    run_id, order, agent_id, node_id, "agent",
                    role, instruction, current_input,
                    "running", _now(), _now(),
                ),
            )

            try:
                # 调用 Agent 执行（内部会有 LLM 流式输出、工具调用等）
                output_text, trace_run_id, structured_output = await _invoke_agent_step(
                    agent=agent,
                    user_id=user_id,
                    workflow_id=workflow_id,
                    run_id=run_id,
                    workflow_step_id=step_id,
                    step_order=order,
                    role=role,
                    instruction=instruction,
                    input_text=current_input,
                    node_id=node_id,
                    publisher=publisher,
                )
            except Exception as exc:
                # 执行失败：更新步骤状态为 error，异常继续向上抛
                await execute(
                    "UPDATE multi_agent_run_steps SET status=%s, error_text=%s, "
                    "finished_at=%s WHERE id=%s",
                    ("error", str(exc), _now(), step_id),
                )
                raise

            # 执行成功：更新步骤状态为 success
            await execute(
                "UPDATE multi_agent_run_steps SET output_text=%s, output_json=%s, status=%s, "
                "finished_at=%s WHERE id=%s",
                (output_text, json.dumps(structured_output, ensure_ascii=False) if structured_output is not None else None, "success", _now(), step_id),
            )

            # 发布 node_done 事件（前端展示节点完成 + 输出）
            await publisher.publish(
                "node_done",
                {"node_id": node_id, "output": output_text},
                node_id=node_id,
            )

            # 当前节点的输出作为下一个节点的输入
            current_input = output_text
            # 继续沿第一条出边走到下一个节点
            node_id = _next_node(config, node_id)
            continue

        # ── 人工确认节点：持久化暂停点，等待用户批准或拒绝 ──
        if node_type == "approval":
            step_counter[0] += 1
            order = step_counter[0]
            data = node.get("data") or {}
            label = str(data.get("label") or "人工确认")[:100]
            prompt = str(data.get("prompt") or "请确认是否继续执行此工作流").strip()
            next_node_id = _next_node(config, node_id)
            step_id = await execute(
                "INSERT INTO multi_agent_run_steps "
                "(run_id, step_order, agent_id, node_id, node_type, role_name, instruction, "
                "input_text, status, started_at, created_at) "
                "VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    run_id, order, node_id, "approval", label, prompt,
                    current_input, "waiting_approval", _now(), _now(),
                ),
            )
            context = {
                "approval_step_id": step_id,
                "approval_node_id": node_id,
                "approval_label": label,
                "approval_prompt": prompt,
                "resume_node_id": next_node_id,
                "current_input": current_input,
                "step_counter": order,
            }
            await execute(
                "UPDATE multi_agent_runs SET status=%s, current_node_id=%s, context_json=%s WHERE id=%s",
                ("waiting_approval", node_id, json.dumps(context, ensure_ascii=False), run_id),
            )
            await publisher.publish(
                "approval_required",
                {
                    "run_id": run_id,
                    "step_id": step_id,
                    "node_id": node_id,
                    "label": label,
                    "prompt": prompt,
                    "input": current_input,
                },
                node_id=node_id,
            )
            raise WorkflowApprovalRequired({
                "run_id": run_id,
                "workflow_id": workflow_id,
                "status": "waiting_approval",
                "input": current_input,
                "output": current_input,
            })

        # ── 条件节点：根据当前输入文本匹配条件，选择一个分支继续执行 ──
        if node_type == "condition":
            # 计算命中哪个分支（返回分支索引）
            branch_idx = _evaluate_condition_branch(node, current_input)
            conditions = (node.get("data") or {}).get("conditions") or []
            # 获取分支的显示名称（前端展示用）
            branch_label = ""
            if branch_idx < len(conditions):
                branch_label = conditions[branch_idx].get("label", "")
            # 找到该分支连接的下游节点
            target_id = _condition_branch_target(config, node_id, branch_idx)
            # 发布 branch 事件（前端展示选中了哪个分支）
            await publisher.publish(
                "branch",
                {
                    "node_id": node_id,
                    "branch_idx": branch_idx,
                    "branch_label": branch_label,
                    "target_node_id": target_id,
                },
                node_id=node_id,
            )
            # 跳到命中分支的下游节点继续遍历
            node_id = target_id
            continue

        # ── 并行节点：所有下游分支并发执行，完成后合并结果继续往下 ──
        if node_type == "parallel":
            # 获取所有下游节点（并行分支的起点）
            targets = _all_targets(config, node_id)
            if not targets:
                break  # 没有下游节点，直接结束
            # 只有一个下游，退化成普通顺序执行，没必要搞并行
            if len(targets) == 1:
                node_id = targets[0]
                continue

            # 找到所有分支的公共汇合点（并行之后在哪里汇合）
            merge_point = _find_merge_point(config, targets)

            # 发布 parallel_start 事件（前端展示并行开始）
            await publisher.publish(
                "parallel_start",
                {"node_id": node_id, "branch_count": len(targets)},
                node_id=node_id,
            )

            # 为每个分支创建一个 _walk_graph 任务，并发执行
            # stop_node_id=merge_point 表示每个分支走到汇合点就停下
            # 等所有分支都到了再一起继续
            branch_tasks = [
                _walk_graph(
                    config, nodes_map, t, current_input,
                    run_id, user_id, workflow_id, step_counter, publisher,
                    stop_node_id=merge_point,
                )
                for t in targets
            ]
            # asyncio.gather 并发执行所有分支任务
            # return_exceptions=True 让异常也作为结果返回，不中断其他分支
            results = await asyncio.gather(*branch_tasks, return_exceptions=True)

            # 收集各分支结果，检查是否有失败
            merged_parts = []
            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    raise HTTPException(
                        status_code=500,
                        detail=f"并行分支 {i + 1} 执行失败: {r}",
                    )
                merged_parts.append(r if isinstance(r, str) else str(r))

            # 用分隔线合并所有分支的输出文本，作为汇合点之后节点的输入
            current_input = "\n\n---\n\n".join(merged_parts)
            # 发布 parallel_done 事件（前端展示并行完成 + 合并结果）
            await publisher.publish(
                "parallel_done",
                {
                    "node_id": node_id,
                    "branch_count": len(targets),
                    "merged_output": current_input,
                },
                node_id=node_id,
            )
            # 从汇合点继续往下执行
            node_id = merge_point
            continue

        # 兜底：未识别的节点类型（未知 type）当透传节点处理，继续沿第一条出边走
        node_id = _next_node(config, node_id)

    # 返回当前累计的输出文本（作为这一段 DAG 的最终输出）
    return current_input


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
    run = await get_workflow_run(run_id, user_id)
    if not run:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    if run["status"] != "waiting_approval":
        raise HTTPException(status_code=409, detail="当前运行不处于待人工确认状态")

    context = run.get("context_json") or {}
    if isinstance(context, str):
        try:
            context = json.loads(context)
        except json.JSONDecodeError:
            context = {}
    step_id = context.get("approval_step_id")
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
            "node_id": context.get("approval_node_id"),
            "approved": approved,
            "comment": comment.strip(),
        },
        node_id=context.get("approval_node_id"),
    )
    # 审批结果由 Command(resume=...) 交回同一个 LangGraph thread。这里先把运行状态
    # 原子地切回 running，使后台恢复任务成为唯一负责写入最终状态的执行者。
    await execute(
        "UPDATE multi_agent_runs SET status=%s, current_node_id=%s, context_json=%s, error_text=NULL WHERE id=%s",
        ("running", context.get("resume_node_id"), json.dumps(context, ensure_ascii=False), run_id),
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
    run = await fetch_one(
        "SELECT id, workflow_id, status, input_text, output_text, error_text, "
        "started_at, finished_at, created_at, current_node_id, context_json, workflow_config_json "
        "FROM multi_agent_runs WHERE id=%s AND user_id=%s",
        (run_id, user_id),
    )
    if not run:
        return None
    # aiomysql 对 JSON 字段通常返回字符串，这里统一转换后再交给恢复逻辑使用。
    for field in ("context_json", "workflow_config_json"):
        value = run.get(field)
        if isinstance(value, str):
            try:
                run[field] = json.loads(value)
            except json.JSONDecodeError:
                run[field] = None
    run["steps"] = await fetch_all(
        "SELECT id, step_order, agent_id, node_id, node_type, trace_run_id, "
        "role_name, instruction, input_text, output_text, output_json, status, error_text, "
        "started_at, finished_at, created_at "
        "FROM multi_agent_run_steps WHERE run_id=%s ORDER BY step_order ASC",
        (run_id,),
    )
    return run
