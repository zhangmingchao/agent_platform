"""将前端工作流配置动态编译为原生 LangGraph。"""

from operator import or_
from functools import lru_cache
import json
from typing import Annotated, Any, Awaitable, Callable, Dict, List, Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt
from typing_extensions import NotRequired, TypedDict

from .event_publisher import RedisStreamEventPublisher
from .workflow_graph import (
    all_targets,
    condition_branch_target,
    evaluate_condition_branch,
    find_merge_point,
    graph_nodes,
    is_graph_config,
    outgoing_edges,
    start_node_id,
)
from ..models.workflow import WorkflowResumeContext


class NativeWorkflowState(TypedDict):
    """动态 LangGraph 中所有业务节点共享的可持久化 State。

    字段：
    - ``run_id`` / ``workflow_id`` / ``user_id``：运行身份；
    - ``workflow_config``：运行创建时冻结的配置快照；
    - ``initial_input``：工作流初始输入；
    - ``node_outputs``：按节点 ID 保存的输出，使用字典合并 reducer 支持并行写入；
    - ``status`` / ``output``：生命周期状态与最终输出；
    - ``approval_*``：人工审批暂停和恢复所需字段。
    """

    run_id: int
    workflow_id: int
    user_id: int
    workflow_config: Dict[str, Any]
    initial_input: str
    state_version: NotRequired[int]
    node_outputs: Annotated[Dict[str, str], or_]
    status: str
    output: NotRequired[str]
    approval_status: NotRequired[str]
    approval_payload: NotRequired[Dict[str, Any]]
    approval_input: NotRequired[str]


AgentNodeRunner = Callable[
    [Dict[str, Any], NativeWorkflowState, str, int],
    Awaitable[str],
]
ApprovalNodePreparer = Callable[
    [Dict[str, Any], NativeWorkflowState, str, int],
    Awaitable[WorkflowResumeContext],
]


@lru_cache(maxsize=128)
def _cached_graph_config(config_json: str) -> Dict[str, Any]:
    """缓存配置标准化结果；返回值只读使用，避免重复解析同一拓扑。"""
    return _as_graph_config(json.loads(config_json))


def _as_graph_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """将传统顺序 steps 配置转换为等价图配置。

    参数：
    - ``config``：运行记录中的工作流配置快照。
    """
    if is_graph_config(config):
        return config
    nodes: List[Dict[str, Any]] = [{"id": "__input__", "type": "input"}]
    edges: List[Dict[str, Any]] = []
    previous_id = "__input__"
    for index, step in enumerate(config.get("steps") or [], start=1):
        node_id = f"__agent_{index}__"
        nodes.append({
            "id": node_id,
            "type": "agent",
            "data": {
                "agent_id": step.get("agent_id"),
                "role": step.get("role"),
                "instruction": step.get("instruction"),
            },
        })
        edges.append({"source": previous_id, "target": node_id})
        previous_id = node_id
    nodes.append({"id": "__output__", "type": "output"})
    edges.append({"source": previous_id, "target": "__output__"})
    return {"mode": "graph", "nodes": nodes, "edges": edges}


class NativeWorkflowEngine:
    """把工作流节点动态注册成原生 LangGraph 节点。

    字段：
    - ``config``：标准化后的图配置；
    - ``publisher``：运行级 Redis Stream 事件发布器；
    - ``agent_runner``：执行一个 Agent 节点的业务回调；
    - ``approval_preparer``：持久化审批暂停现场的业务回调。

    方法：
    - ``compile``：注册节点、普通边、条件边、并行 barrier 并编译图。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        publisher: RedisStreamEventPublisher,
        agent_runner: AgentNodeRunner,
        approval_preparer: ApprovalNodePreparer,
    ) -> None:
        """保存动态编译依赖。

        参数：
        - ``config``：工作流配置快照；
        - ``publisher``：事件发布器；
        - ``agent_runner``：Agent 节点执行回调；
        - ``approval_preparer``：审批准备回调。
        """
        # 通过稳定 JSON 作为缓存键，仅缓存拓扑标准化，不缓存绑定运行上下文的 CompiledStateGraph。
        config_json = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.config = _cached_graph_config(config_json)
        self.publisher = publisher
        self.agent_runner = agent_runner
        self.approval_preparer = approval_preparer
        self.nodes = graph_nodes(self.config)
        executable_ids = [
            node_id
            for node_id, node in self.nodes.items()
            if node.get("type") in {"agent", "approval"}
        ]
        self.node_order = {
            node_id: index
            for index, node_id in enumerate(executable_ids, start=1)
        }
        self.parallel_merges: Dict[str, List[str]] = {}
        for parallel_id, node in self.nodes.items():
            if node.get("type") == "parallel":
                merge_id = find_merge_point(
                    self.config,
                    all_targets(self.config, parallel_id),
                )
                if merge_id:
                    self.parallel_merges.setdefault(merge_id, []).append(parallel_id)

    def _incoming_sources(self, node_id: str) -> List[str]:
        """按配置顺序返回节点的直接前驱 ID。"""
        return [
            edge["source"]
            for edge in self.config.get("edges", [])
            if edge.get("target") == node_id and edge.get("source")
        ]

    def _node_input(self, node_id: str, state: NativeWorkflowState) -> str:
        """根据已执行前驱节点输出组装当前节点输入。"""
        outputs = state.get("node_outputs") or {}
        values = [
            outputs[source]
            for source in self._incoming_sources(node_id)
            if source in outputs
        ]
        if not values:
            return state["initial_input"]
        return values[0] if len(values) == 1 else "\n\n---\n\n".join(values)

    def _mapped_target(self, target_id: str) -> str:
        """审批节点的入边先连接到其幂等准备节点。"""
        target = self.nodes.get(target_id) or {}
        return f"{target_id}__prepare" if target.get("type") == "approval" else target_id

    def _parallel_barriers(self) -> Dict[str, List[str]]:
        """计算并行节点公共汇合点及其 barrier 前驱。"""
        barriers: Dict[str, List[str]] = {}
        for node_id, node in self.nodes.items():
            if node.get("type") != "parallel":
                continue
            targets = all_targets(self.config, node_id)
            merge_id = find_merge_point(self.config, targets)
            if merge_id:
                sources = self._incoming_sources(merge_id)
                if len(sources) > 1:
                    barriers[merge_id] = sources
        return barriers

    async def _publish_parallel_completion(
        self,
        node_id: str,
        merged_input: str,
    ) -> None:
        """在公共汇合节点执行前发布并行完成事件。"""
        for parallel_id in self.parallel_merges.get(node_id, []):
            await self.publisher.publish(
                "parallel_done",
                {
                    "node_id": parallel_id,
                    "branch_count": len(all_targets(self.config, parallel_id)),
                    "merged_output": merged_input,
                },
                node_id=parallel_id,
            )

    def _register_business_node(
        self,
        builder: StateGraph,
        node_id: str,
        node: Dict[str, Any],
    ) -> None:
        """按照节点类型注册对应的异步执行函数。"""
        node_type = str(node.get("type") or "agent")
        order = self.node_order.get(node_id, 0)

        if node_type == "agent":
            async def agent_node(state: NativeWorkflowState) -> Dict[str, Any]:
                node_input = self._node_input(node_id, state)
                await self._publish_parallel_completion(node_id, node_input)
                output = await self.agent_runner(node, state, node_input, order)
                update: Dict[str, Any] = {"node_outputs": {node_id: output}}
                if not all_targets(self.config, node_id):
                    update.update({"status": "success", "output": output})
                return update

            builder.add_node(node_id, agent_node)
            return

        if node_type == "approval":
            prepare_id = f"{node_id}__prepare"

            async def prepare_node(state: NativeWorkflowState) -> Dict[str, Any]:
                node_input = self._node_input(node_id, state)
                await self._publish_parallel_completion(node_id, node_input)
                context = await self.approval_preparer(node, state, node_input, order)
                return {
                    "approval_status": "pending",
                    "approval_input": node_input,
                    "approval_payload": {
                        "run_id": state["run_id"],
                        "step_id": context.approval_step_id,
                        "node_id": node_id,
                        "label": context.approval_label,
                        "prompt": context.approval_prompt,
                        "input": node_input,
                    },
                }

            def approval_node(state: NativeWorkflowState) -> Dict[str, Any]:
                decision = interrupt(state.get("approval_payload") or {})
                approved = bool(decision.get("approved"))
                comment = str(decision.get("comment") or "").strip()
                if not approved:
                    decision_text = "已拒绝" + (f"：{comment}" if comment else "")
                    return {
                        "status": "rejected",
                        "output": decision_text,
                        "approval_status": "rejected",
                    }
                node_input = state.get("approval_input", "")
                return {
                    "status": "running" if all_targets(self.config, node_id) else "success",
                    "output": node_input if not all_targets(self.config, node_id) else state.get("output", ""),
                    "approval_status": "approved",
                    "node_outputs": {node_id: node_input},
                }

            builder.add_node(prepare_id, prepare_node)
            builder.add_node(node_id, approval_node)
            builder.add_edge(prepare_id, node_id)
            return

        async def passthrough_node(state: NativeWorkflowState) -> Dict[str, Any]:
            node_input = self._node_input(node_id, state)
            await self._publish_parallel_completion(node_id, node_input)
            update: Dict[str, Any] = {"node_outputs": {node_id: node_input}}
            if node_type == "output":
                update.update({"status": "success", "output": node_input})
            elif node_type == "parallel":
                await self.publisher.publish(
                    "parallel_start",
                    {"node_id": node_id, "branch_count": len(all_targets(self.config, node_id))},
                    node_id=node_id,
                )
            return update

        builder.add_node(node_id, passthrough_node)

    def compile(
        self,
        checkpointer: BaseCheckpointSaver[str],
    ) -> CompiledStateGraph:
        """动态注册全部业务节点和连线并编译 LangGraph。

        参数：
        - ``checkpointer``：必须可持久化的工作流 Checkpointer。
        """
        builder = StateGraph(NativeWorkflowState)
        for node_id, node in self.nodes.items():
            self._register_business_node(builder, node_id, node)

        start_id = start_node_id(self.config)
        if not start_id:
            raise ValueError("工作流缺少入口节点")
        builder.add_edge(START, self._mapped_target(start_id))
        barriers = self._parallel_barriers()
        barrier_edges = {
            (source, merge_id)
            for merge_id, sources in barriers.items()
            for source in sources
        }

        for node_id, node in self.nodes.items():
            node_type = str(node.get("type") or "agent")
            targets = all_targets(self.config, node_id)
            if node_type == "condition":
                conditions = (node.get("data") or {}).get("conditions") or []
                path_map: Dict[int, str] = {}
                for index in range(max(len(conditions), len(targets))):
                    target_id = condition_branch_target(self.config, node_id, index)
                    if target_id:
                        path_map[index] = self._mapped_target(target_id)

                async def route_condition(
                    state: NativeWorkflowState,
                    current_node_id: str = node_id,
                    current_node: Dict[str, Any] = node,
                ) -> int:
                    node_input = self._node_input(current_node_id, state)
                    result = evaluate_condition_branch(current_node, node_input)
                    target_id = condition_branch_target(
                        self.config,
                        current_node_id,
                        result.branch_index,
                    )
                    await self.publisher.publish(
                        "branch",
                        {
                            "node_id": current_node_id,
                            "branch_idx": result.branch_index,
                            "target_node_id": target_id,
                            "actual_value": result.actual_value,
                        },
                        node_id=current_node_id,
                    )
                    return result.branch_index

                builder.add_conditional_edges(node_id, route_condition, path_map)
                continue

            if node_type == "approval":
                if targets:
                    target = self._mapped_target(targets[0])

                    def route_approval(state: NativeWorkflowState) -> str:
                        return "continue" if state.get("approval_status") == "approved" else "end"

                    builder.add_conditional_edges(
                        node_id,
                        route_approval,
                        {"continue": target, "end": END},
                    )
                else:
                    builder.add_edge(node_id, END)
                continue

            if node_type == "output" or not targets:
                builder.add_edge(node_id, END)
                continue

            for target_id in targets:
                if (node_id, target_id) in barrier_edges:
                    continue
                builder.add_edge(node_id, self._mapped_target(target_id))

        for merge_id, sources in barriers.items():
            builder.add_edge(sources, self._mapped_target(merge_id))

        return builder.compile(checkpointer=checkpointer)
