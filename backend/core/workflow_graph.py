"""工作流配置校验与 DAG 图结构查询。"""

import json
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException

from .workflow_conditions import evaluate_workflow_conditions
from ..models.workflow_condition import WorkflowConditionResult

MAX_WORKFLOW_STEPS = 12
MAX_GRAPH_STEPS = 40


def parse_workflow_config(config: Any) -> Dict[str, Any]:
    """解析并校验工作流配置。

    参数：
    - ``config``：JSON 字符串或已经解析的工作流配置对象。
    """
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="config_json 不是合法 JSON") from exc
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="config 必须是 JSON 对象")
    return config


def is_graph_config(config: Dict[str, Any]) -> bool:
    """判断配置是否为包含 nodes 和 edges 的图式工作流。"""
    return isinstance(config.get("nodes"), list) and isinstance(config.get("edges"), list)


def graph_agent_steps(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """提取并校验图式工作流中的 Agent 步骤。"""
    steps: List[Dict[str, Any]] = []
    for node in config.get("nodes", []):
        if node.get("type") != "agent":
            continue
        data = node.get("data") or {}
        agent_id = data.get("agent_id") or node.get("agent_id")
        if not isinstance(agent_id, int):
            raise HTTPException(
                status_code=400,
                detail=f"Agent 节点缺少有效 agent_id: {node.get('id')}",
            )
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


def normalize_workflow_steps(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """规范化顺序或图式工作流的 Agent 步骤。"""
    if is_graph_config(config):
        return graph_agent_steps(config)
    steps = config.get("steps", [])
    if not isinstance(steps, list) or not steps:
        raise HTTPException(status_code=400, detail="工作流至少需要一个步骤")
    if len(steps) > MAX_WORKFLOW_STEPS:
        raise HTTPException(status_code=400, detail=f"工作流最多支持 {MAX_WORKFLOW_STEPS} 个步骤")
    normalized: List[Dict[str, Any]] = []
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise HTTPException(status_code=400, detail=f"第 {index} 个步骤必须是 JSON 对象")
        agent_id = step.get("agent_id")
        if not isinstance(agent_id, int):
            raise HTTPException(status_code=400, detail=f"第 {index} 个步骤缺少有效 agent_id")
        normalized.append({
            "agent_id": agent_id,
            "role": str(step.get("role") or f"step_{index}")[:100],
            "instruction": str(step.get("instruction") or "").strip(),
        })
    return normalized


def graph_nodes(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """将节点列表转换为按节点 ID 索引的字典。"""
    return {node["id"]: node for node in config.get("nodes", []) if node.get("id")}


def outgoing_edges(config: Dict[str, Any], node_id: str) -> List[Dict[str, Any]]:
    """返回从指定节点出发的全部连线。"""
    return [edge for edge in config.get("edges", []) if edge.get("source") == node_id]


def next_node(config: Dict[str, Any], node_id: str) -> Optional[str]:
    """返回普通节点第一条出边的目标节点。"""
    edges = outgoing_edges(config, node_id)
    return edges[0].get("target") if edges else None


def all_targets(config: Dict[str, Any], node_id: str) -> List[str]:
    """返回节点全部有效下游目标 ID。"""
    return [edge["target"] for edge in outgoing_edges(config, node_id) if edge.get("target")]


def start_node_id(config: Dict[str, Any]) -> Optional[str]:
    """查找图式工作流入口节点。"""
    for node in config.get("nodes", []):
        if node.get("type") in ("input", "start"):
            return node.get("id")
    nodes = config.get("nodes") or []
    return nodes[0].get("id") if nodes else None


def evaluate_condition_branch(
    node: Dict[str, Any],
    current_input: str,
) -> WorkflowConditionResult:
    """根据当前输入判断条件节点命中的分支。"""
    conditions = (node.get("data") or {}).get("conditions") or []
    return evaluate_workflow_conditions(conditions, current_input)


def condition_branch_target(
    config: Dict[str, Any],
    node_id: str,
    branch_index: int,
) -> Optional[str]:
    """根据条件分支索引查找对应目标节点。"""
    edges = outgoing_edges(config, node_id)
    handle_id = f"cond-{branch_index}"
    for edge in edges:
        source_handle = edge.get("source_handle") or edge.get("sourceHandle")
        if source_handle == handle_id:
            return edge.get("target")
    return edges[branch_index].get("target") if branch_index < len(edges) else None


def reachable_nodes(config: Dict[str, Any], start_id: str) -> Set[str]:
    """通过广度优先搜索计算起点可到达的节点集合。"""
    reachable: Set[str] = set()
    queue = [start_id]
    while queue:
        current_id = queue.pop(0)
        if current_id in reachable:
            continue
        reachable.add(current_id)
        queue.extend(
            target
            for target in all_targets(config, current_id)
            if target not in reachable
        )
    return reachable


def find_merge_point(
    config: Dict[str, Any],
    branch_starts: List[str],
) -> Optional[str]:
    """寻找并行分支最早的公共汇合节点。"""
    if not branch_starts:
        return None
    if len(branch_starts) == 1:
        return next_node(config, branch_starts[0])
    reachable_sets = [reachable_nodes(config, start) for start in branch_starts]
    common_nodes = set.intersection(*reachable_sets)
    if not common_nodes:
        return None
    for start in branch_starts:
        queue = list(all_targets(config, start))
        visited: Set[str] = set()
        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)
            if current_id in common_nodes:
                return current_id
            queue.extend(
                target
                for target in all_targets(config, current_id)
                if target not in visited
            )
    return next(iter(common_nodes))
