"""工作流定义与运行记录 Repository。"""

from typing import Any, Dict, List, Optional

from ..database import fetch_all, fetch_one
from ..models.workflow import WorkflowDefinition, WorkflowRun


async def list_workflow_entities(user_id: int) -> List[WorkflowDefinition]:
    """查询用户的工作流定义实体。

    参数：
    - ``user_id``：工作流所属用户 ID。
    """
    rows: List[Dict[str, Any]] = await fetch_all(
        "SELECT id, name, description, mode, config_json, is_active, created_at, updated_at "
        "FROM multi_agent_workflows WHERE user_id=%s ORDER BY updated_at DESC",
        (user_id,),
    )
    return [WorkflowDefinition.from_mapping(row) for row in rows]


async def find_workflow_entity(
    workflow_id: int,
    user_id: int,
) -> Optional[WorkflowDefinition]:
    """按主键和用户查询工作流实体。

    参数：
    - ``workflow_id``：工作流 ID；
    - ``user_id``：所属用户 ID。
    """
    row: Optional[Dict[str, Any]] = await fetch_one(
        "SELECT id, name, description, mode, config_json, is_active, created_at, updated_at "
        "FROM multi_agent_workflows WHERE id=%s AND user_id=%s",
        (workflow_id, user_id),
    )
    return WorkflowDefinition.from_mapping(row) if row else None


async def find_workflow_run_entity(
    run_id: int,
    user_id: int,
) -> Optional[WorkflowRun]:
    """查询包含步骤和配置快照的工作流运行实体。

    参数：
    - ``run_id``：运行记录 ID；
    - ``user_id``：所属用户 ID。
    """
    row: Optional[Dict[str, Any]] = await fetch_one(
        "SELECT id, workflow_id, status, input_text, output_text, error_text, "
        "started_at, finished_at, created_at, current_node_id, context_json, workflow_config_json "
        "FROM multi_agent_runs WHERE id=%s AND user_id=%s",
        (run_id, user_id),
    )
    if not row:
        return None
    steps: List[Dict[str, Any]] = await fetch_all(
        "SELECT id, step_order, agent_id, node_id, node_type, trace_run_id, "
        "role_name, instruction, input_text, output_text, output_json, status, error_text, "
        "started_at, finished_at, created_at "
        "FROM multi_agent_run_steps WHERE run_id=%s ORDER BY step_order ASC",
        (run_id,),
    )
    return WorkflowRun.from_mapping(row, steps)
