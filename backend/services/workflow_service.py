"""Multi-agent workflow persistence and runtime service."""
import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import HTTPException
from langchain_core.messages import HumanMessage

from ..core.agent_factory import create_agent_instance, get_model_name
from ..core.trace_handler import TraceContext
from ..database import execute, fetch_all, fetch_one
from .agent_service import get_agent
from .mcp_config_service import get_agent_mcps
from .model_service import get_model
from .skill_service import get_agent_skills

MAX_WORKFLOW_STEPS = 12
MAX_STEP_INPUT_CHARS = 12000
MAX_GRAPH_STEPS = 40


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _parse_config(config) -> Dict:
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="config_json 不是合法 JSON") from exc
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="config 必须是 JSON 对象")
    return config


# ── Sequential config helpers ──────────────────────────────────────────

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


# ── Graph (DAG) config helpers ─────────────────────────────────────────

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
    return {node.get("id"): node for node in config.get("nodes", []) if node.get("id")}


def _outgoing_edges(config: Dict, node_id: str) -> List[Dict]:
    return [edge for edge in config.get("edges", []) if edge.get("source") == node_id]


def _next_node(config: Dict, node_id: str) -> Optional[str]:
    edges = _outgoing_edges(config, node_id)
    return edges[0].get("target") if edges else None


def _all_targets(config: Dict, node_id: str) -> List[str]:
    return [e.get("target") for e in _outgoing_edges(config, node_id) if e.get("target")]


def _start_node_id(config: Dict) -> str:
    for node in config.get("nodes", []):
        if node.get("type") in ("input", "start"):
            return node.get("id")
    return config.get("nodes", [{}])[0].get("id")


def _evaluate_condition_branch(node: Dict, current_input: str) -> int:
    data = node.get("data") or {}
    conditions = data.get("conditions") or []
    text = current_input or ""

    for i, cond in enumerate(conditions):
        cond_type = cond.get("type", "else")
        if cond_type == "else":
            continue
        value = str(cond.get("value") or "")
        if not value:
            continue
        if cond_type == "contains" and value in text:
            return i
        if cond_type == "regex":
            try:
                if re.search(value, text):
                    return i
            except re.error:
                continue

    for i, cond in enumerate(conditions):
        if cond.get("type") == "else":
            return i
    return 0


def _condition_branch_target(config: Dict, node_id: str, branch_idx: int) -> Optional[str]:
    edges = _outgoing_edges(config, node_id)
    handle_id = f"cond-{branch_idx}"
    for edge in edges:
        sh = edge.get("source_handle") or edge.get("sourceHandle")
        if sh == handle_id:
            return edge.get("target")
    if branch_idx < len(edges):
        return edges[branch_idx].get("target")
    return None


def _find_reachable(config: Dict, start_id: str) -> Set[str]:
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
    if not branch_starts:
        return None
    if len(branch_starts) == 1:
        return _next_node(config, branch_starts[0])

    reachable_sets = [_find_reachable(config, start) for start in branch_starts]
    common = reachable_sets[0]
    for rs in reachable_sets[1:]:
        common = common & rs

    if not common:
        return None

    for start in branch_starts:
        queue = list(_all_targets(config, start))
        visited: Set[str] = set()
        while queue:
            nid = queue.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            if nid in common:
                return nid
            for target in _all_targets(config, nid):
                if target not in visited:
                    queue.append(target)

    return next(iter(common)) if common else None


# ── Model / agent loading helpers ──────────────────────────────────────

async def _load_model_config(agent: Dict, user_id: int) -> Optional[Dict]:
    model_config_id = agent.get("model_config_id")
    if not model_config_id:
        return None
    return await get_model(model_config_id, user_id)


async def _validate_workflow_agents(user_id: int, config: Dict) -> None:
    for step in _normalize_steps(config):
        if not await get_agent(step["agent_id"], user_id):
            raise HTTPException(status_code=400, detail=f"Agent 不存在或无权限: {step['agent_id']}")


# ── CRUD ───────────────────────────────────────────────────────────────

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


# ── Agent step execution ───────────────────────────────────────────────

async def _invoke_agent_step(
    *,
    agent: Dict,
    user_id: int,
    workflow_id: int,
    run_id: int,
    workflow_step_id: int,
    step_order: int,
    role: str,
    instruction: str,
    input_text: str,
) -> tuple[str, int]:
    skills_data = await get_agent_skills(agent["id"])
    mcps_data = await get_agent_mcps(agent["id"])
    model_config = await _load_model_config(agent, user_id)
    agent_executor = await create_agent_instance(agent, skills_data, mcps_data, model_config)

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
        agent_id=agent["id"],
        model_name=get_model_name(agent, model_config),
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
        "recursion_limit": max(8, min(int(agent.get("iteration_count") or 6) * 2 + 5, 80)),
    }

    full_response = []
    try:
        async for event in agent_executor.astream_events(
            {"messages": [HumanMessage(content=prompt)]},
            config=config,
            version="v2",
        ):
            kind = event["event"]
            event_run_id = event.get("run_id", "")

            if kind == "on_chat_model_start":
                model_name = event.get("name", "LLM")
                input_data = str(event.get("data", {}).get("input", ""))
                await trace_ctx.on_llm_start(event_run_id, model_name, input_data)

            elif kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and chunk.content:
                    full_response.append(chunk.content)

            elif kind == "on_chat_model_end":
                output = str(event.get("data", {}).get("output", ""))
                await trace_ctx.on_llm_end(event_run_id, output)

            elif kind == "on_tool_start":
                tool_name = event.get("name", "")
                input_data = str(event.get("data", {}).get("input", ""))
                await trace_ctx.on_tool_start(event_run_id, tool_name, input_data)

            elif kind == "on_tool_end":
                output = event.get("data", {}).get("output", "")
                if hasattr(output, "content"):
                    output_str = str(output.content)
                else:
                    output_str = str(output)
                await trace_ctx.on_tool_end(event_run_id, output_str)

        output_text = "".join(full_response).strip()
        if not output_text:
            output_text = "工作流步骤未产生文本输出"
        await trace_ctx.finish(output_text)
        return output_text, trace_run_id
    except Exception as exc:
        await trace_ctx.error(str(exc))
        raise


# ── Workflow run management ───────────────────────────────────────────

async def run_workflow(workflow_id: int, user_id: int, input_text: str) -> Dict:
    workflow = await get_workflow(workflow_id, user_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    if not workflow.get("is_active", 1):
        raise HTTPException(status_code=400, detail="工作流已停用")

    run_id = await create_workflow_run(workflow_id, user_id, input_text)
    return await execute_workflow_run(run_id, user_id)


async def create_workflow_run(workflow_id: int, user_id: int, input_text: str) -> int:
    workflow = await get_workflow(workflow_id, user_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    if not workflow.get("is_active", 1):
        raise HTTPException(status_code=400, detail="工作流已停用")
    _normalize_steps(workflow["config"])

    now = _now()
    return await execute(
        "INSERT INTO multi_agent_runs "
        "(workflow_id, user_id, status, input_text, started_at, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (workflow_id, user_id, "running", input_text, now, now),
    )


async def execute_workflow_run(run_id: int, user_id: int) -> Dict:
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

    workflow = await get_workflow(run["workflow_id"], user_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")

    workflow_id = run["workflow_id"]
    config = workflow["config"]

    if _is_graph_config(config):
        return await _execute_dag(run_id, user_id, workflow_id, config, run["input_text"])
    return await _execute_sequential(run_id, user_id, workflow_id, config, run["input_text"])


async def _execute_sequential(
    run_id: int, user_id: int, workflow_id: int, config: Dict, initial_input: str,
) -> Dict:
    steps = _normalize_steps(config)
    current_input = initial_input
    step_results = []

    try:
        for idx, step in enumerate(steps, start=1):
            agent = await get_agent(step["agent_id"], user_id)
            if not agent:
                raise HTTPException(status_code=400, detail=f"Agent 不存在或无权限: {step['agent_id']}")

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
                output_text, trace_run_id = await _invoke_agent_step(
                    agent=agent,
                    user_id=user_id,
                    workflow_id=workflow_id,
                    run_id=run_id,
                    workflow_step_id=step_id,
                    step_order=idx,
                    role=step["role"],
                    instruction=step["instruction"],
                    input_text=current_input,
                )
            except Exception as exc:
                await execute(
                    "UPDATE multi_agent_run_steps SET status=%s, error_text=%s, finished_at=%s WHERE id=%s",
                    ("error", str(exc), _now(), step_id),
                )
                raise

            await execute(
                "UPDATE multi_agent_run_steps SET output_text=%s, status=%s, finished_at=%s WHERE id=%s",
                (output_text, "success", _now(), step_id),
            )
            step_results.append({
                "step_order": idx,
                "agent_id": step["agent_id"],
                "agent_name": agent.get("name"),
                "role": step["role"],
                "trace_run_id": trace_run_id,
                "output": output_text,
            })
            current_input = output_text

        await execute(
            "UPDATE multi_agent_runs SET status=%s, output_text=%s, finished_at=%s WHERE id=%s",
            ("success", current_input, _now(), run_id),
        )
        return {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": "success",
            "input": initial_input,
            "output": current_input,
            "steps": step_results,
        }
    except Exception as exc:
        error_text = str(exc)
        await execute(
            "UPDATE multi_agent_runs SET status=%s, error_text=%s, finished_at=%s WHERE id=%s",
            ("error", error_text, _now(), run_id),
        )
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {error_text}") from exc


# ── DAG execution (parallel + conditional branches) ────────────────────

async def _execute_dag(
    run_id: int, user_id: int, workflow_id: int, config: Dict, initial_input: str,
) -> Dict:
    nodes_map = _graph_nodes(config)
    start_id = _start_node_id(config)
    step_counter = [0]

    try:
        final_output = await _walk_graph(
            config, nodes_map, start_id, initial_input,
            run_id, user_id, workflow_id, step_counter,
        )
        await execute(
            "UPDATE multi_agent_runs SET status=%s, output_text=%s, finished_at=%s, "
            "current_node_id=%s WHERE id=%s",
            ("success", final_output, _now(), None, run_id),
        )
        return {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": "success",
            "input": initial_input,
            "output": final_output,
        }
    except Exception as exc:
        error_text = str(exc)
        await execute(
            "UPDATE multi_agent_runs SET status=%s, error_text=%s, finished_at=%s WHERE id=%s",
            ("error", error_text, _now(), run_id),
        )
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {error_text}") from exc


async def _walk_graph(
    config: Dict,
    nodes_map: Dict[str, Dict],
    node_id: Optional[str],
    current_input: str,
    run_id: int,
    user_id: int,
    workflow_id: int,
    step_counter: list,
    stop_node_id: Optional[str] = None,
) -> str:
    """Walk the DAG from *node_id*.  When *stop_node_id* is set the walk halts
    just before reaching that node — used to confine each parallel branch to
    the sub-graph that precedes the merge point."""
    visited: Set[str] = set()

    while node_id and node_id != stop_node_id:
        if node_id in visited:
            break
        visited.add(node_id)

        node = nodes_map.get(node_id)
        if not node:
            break

        node_type = node.get("type", "agent")

        await execute(
            "UPDATE multi_agent_runs SET current_node_id=%s WHERE id=%s",
            (node_id, run_id),
        )

        # ── pass-through nodes ──────────────────────────────────────
        if node_type in ("input", "start"):
            node_id = _next_node(config, node_id)
            continue

        if node_type == "output":
            break

        # ── agent node: execute LLM ──────────────────────────────────
        if node_type == "agent":
            step_counter[0] += 1
            order = step_counter[0]
            data = node.get("data") or {}
            agent_id = data.get("agent_id")

            agent = await get_agent(agent_id, user_id)
            if not agent:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent 不存在或无权限: {agent_id}",
                )

            role = str(data.get("role") or data.get("label") or node_id)[:100]
            instruction = str(data.get("instruction") or "").strip()

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
                output_text, trace_run_id = await _invoke_agent_step(
                    agent=agent,
                    user_id=user_id,
                    workflow_id=workflow_id,
                    run_id=run_id,
                    workflow_step_id=step_id,
                    step_order=order,
                    role=role,
                    instruction=instruction,
                    input_text=current_input,
                )
            except Exception as exc:
                await execute(
                    "UPDATE multi_agent_run_steps SET status=%s, error_text=%s, "
                    "finished_at=%s WHERE id=%s",
                    ("error", str(exc), _now(), step_id),
                )
                raise

            await execute(
                "UPDATE multi_agent_run_steps SET output_text=%s, status=%s, "
                "finished_at=%s WHERE id=%s",
                (output_text, "success", _now(), step_id),
            )

            current_input = output_text
            node_id = _next_node(config, node_id)
            continue

        # ── condition node: pick a branch ────────────────────────────
        if node_type == "condition":
            branch_idx = _evaluate_condition_branch(node, current_input)
            node_id = _condition_branch_target(config, node_id, branch_idx)
            continue

        # ── parallel node: fan-out + merge ──────────────────────────
        if node_type == "parallel":
            targets = _all_targets(config, node_id)
            if not targets:
                break
            if len(targets) == 1:
                node_id = targets[0]
                continue

            merge_point = _find_merge_point(config, targets)

            branch_tasks = [
                _walk_graph(
                    config, nodes_map, t, current_input,
                    run_id, user_id, workflow_id, step_counter,
                    stop_node_id=merge_point,
                )
                for t in targets
            ]
            results = await asyncio.gather(*branch_tasks, return_exceptions=True)

            merged_parts = []
            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    raise HTTPException(
                        status_code=500,
                        detail=f"并行分支 {i + 1} 执行失败: {r}",
                    )
                merged_parts.append(r if isinstance(r, str) else str(r))

            current_input = "\n\n---\n\n".join(merged_parts)
            node_id = merge_point
            continue

        # unknown type — skip
        node_id = _next_node(config, node_id)

    return current_input


async def start_workflow_run(workflow_id: int, user_id: int, input_text: str) -> Dict:
    run_id = await create_workflow_run(workflow_id, user_id, input_text)
    return {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "status": "running",
        "input": input_text,
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
        "started_at, finished_at, created_at, current_node_id, context_json "
        "FROM multi_agent_runs WHERE id=%s AND user_id=%s",
        (run_id, user_id),
    )
    if not run:
        return None
    run["steps"] = await fetch_all(
        "SELECT id, step_order, agent_id, node_id, node_type, trace_run_id, "
        "role_name, instruction, input_text, output_text, status, error_text, "
        "started_at, finished_at, created_at "
        "FROM multi_agent_run_steps WHERE run_id=%s ORDER BY step_order ASC",
        (run_id,),
    )
    return run
