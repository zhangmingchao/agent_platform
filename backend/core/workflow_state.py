"""工作流级 LangGraph 调用配置。"""

from typing import Any, Dict


def workflow_thread_id(run_id: int) -> str:
    """生成原生动态工作流使用的稳定 v2 LangGraph thread_id。

    参数：
    - ``run_id``：MySQL 工作流运行记录 ID。

    v2 命名空间用于隔离旧版外层生命周期图的 Checkpoint，避免不同图拓扑误读状态。
    """
    return f"workflow_run_v2_{run_id}"


def workflow_graph_config(run_id: int) -> Dict[str, Any]:
    """构造调用工作流 StateGraph 时使用的统一配置。"""
    return {
        "configurable": {"thread_id": workflow_thread_id(run_id)},
        "recursion_limit": 100,
    }
