"""工作流级 LangGraph State 与生命周期图。"""

from typing import Any, Awaitable, Callable, Dict, Optional

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from typing_extensions import NotRequired, TypedDict


class WorkflowRuntimeState(TypedDict):
    """一次工作流运行在暂停、恢复期间需要持久化的轻量状态。"""

    # 稳定身份字段：整个工作流运行期间保持不变。
    run_id: int
    workflow_id: int
    user_id: int
    # 创建运行时保存的工作流配置快照，恢复时不读取可能已经修改的新配置。
    workflow_config: Dict[str, Any]
    initial_input: str

    # 每段执行完成后更新的游标与输入。
    current_input: str
    current_node_id: NotRequired[Optional[str]]
    step_counter: NotRequired[int]
    resume_context: NotRequired[Dict[str, Any]]

    # 工作流生命周期状态与最终结果。
    status: str
    output: NotRequired[str]
    error: NotRequired[str]
    approval_status: NotRequired[str]
    approval_comment: NotRequired[str]
    approval_payload: NotRequired[Dict[str, Any]]


WorkflowSegmentRunner = Callable[[WorkflowRuntimeState], Awaitable[Dict[str, Any]]]


def workflow_thread_id(run_id: int) -> str:
    """生成贯穿整个工作流运行生命周期的稳定 LangGraph thread_id。"""
    return f"workflow_run_{run_id}"


def workflow_graph_config(run_id: int) -> Dict[str, Any]:
    """构造调用工作流 StateGraph 时使用的统一配置。"""
    return {
        "configurable": {"thread_id": workflow_thread_id(run_id)},
        "recursion_limit": 100,
    }


def build_workflow_lifecycle_graph(checkpointer, run_segment: WorkflowSegmentRunner):
    """构建可持久化暂停和恢复的工作流生命周期图。

    ``run_segment`` 继续复用当前成熟的 DAG/顺序执行器。执行器遇到人工审批时返回
    ``waiting_approval``，图随后进入 ``interrupt``；审批 API 使用相同 thread_id 和
    ``Command(resume=...)`` 恢复，不再依赖重新提交一份初始 State。
    """

    async def execute_node(state: WorkflowRuntimeState) -> Dict[str, Any]:
        """执行到结束或下一个人工审批点，并把游标写回 State。"""
        return await run_segment(state)

    def route_after_execute(state: WorkflowRuntimeState) -> str:
        """等待审批时进入审批节点，其他终态直接结束。"""
        return "approval" if state.get("status") == "waiting_approval" else "end"

    def approval_node(state: WorkflowRuntimeState) -> Dict[str, Any]:
        """通过 LangGraph interrupt 保存现场，并接收审批接口的恢复参数。"""
        decision = interrupt(state.get("approval_payload") or {})
        approved = bool(decision.get("approved"))
        comment = str(decision.get("comment") or "").strip()
        if not approved:
            decision_text = "已拒绝" + (f"：{comment}" if comment else "")
            return {
                "status": "rejected",
                "output": decision_text,
                "approval_status": "rejected",
                "approval_comment": comment,
            }

        # 审批通过后只移除当前审批标识，保留恢复节点、输入和步骤序号。
        resume_context = dict(state.get("resume_context") or {})
        resume_context.pop("approval_step_id", None)
        resume_context.pop("approval_node_id", None)
        return {
            "status": "running",
            "approval_status": "approved",
            "approval_comment": comment,
            "resume_context": resume_context,
            "current_node_id": resume_context.get("resume_node_id"),
        }

    def route_after_approval(state: WorkflowRuntimeState) -> str:
        """审批通过继续执行，审批拒绝直接结束。"""
        return "execute" if state.get("approval_status") == "approved" else "end"

    builder = StateGraph(WorkflowRuntimeState)
    builder.add_node("execute", execute_node)
    builder.add_node("approval", approval_node)
    builder.add_edge(START, "execute")
    builder.add_conditional_edges(
        "execute",
        route_after_execute,
        {"approval": "approval", "end": END},
    )
    builder.add_conditional_edges(
        "approval",
        route_after_approval,
        {"execute": "execute", "end": END},
    )
    return builder.compile(checkpointer=checkpointer)
