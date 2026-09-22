"""显式任务计划及步骤的持久化服务。"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database import execute, execute_many, fetch_all, fetch_one
from ..models.task_planning import (
    TaskPlan,
    TaskPlanStatus,
    TaskPlanStep,
    TaskPlanStepStatus,
)


def _now() -> str:
    """返回数据库使用的 UTC 时间文本。"""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def create_task_plan(
    trace_run_id: int,
    user_id: int,
    agent_id: int,
    plan: TaskPlan,
) -> TaskPlan:
    """创建一次任务计划和全部待执行步骤。

    Args:
        trace_run_id: 本次聊天对应的 Trace 运行主键。
        user_id: 计划所属用户 ID。
        agent_id: 执行计划的 Agent ID。
        plan: 规划模型生成并转换后的领域实体。

    Returns:
        包含数据库主键的任务计划实体。
    """
    now = _now()
    plan_id = await execute(
        "INSERT INTO agent_task_plans "
        "(trace_run_id, user_id, agent_id, goal, status, current_step_order, "
        "created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (
            trace_run_id,
            user_id,
            agent_id,
            plan.goal,
            TaskPlanStatus.RUNNING.value,
            0,
            now,
            now,
        ),
    )
    try:
        await execute_many(
            "INSERT INTO agent_task_plan_steps "
            "(plan_id, step_key, step_order, title, instruction, status, "
            "created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [
                (
                    plan_id,
                    step.step_key,
                    step.order,
                    step.title,
                    step.instruction,
                    TaskPlanStepStatus.PENDING.value,
                    now,
                    now,
                )
                for step in plan.steps
            ],
        )
    except Exception:
        # 两个通用数据库方法分别提交事务；步骤创建失败时主动清理孤立计划。
        await execute("DELETE FROM agent_task_plans WHERE id=%s", (plan_id,))
        raise

    persisted = await get_task_plan(plan_id)
    if persisted is None:
        raise RuntimeError("任务计划创建成功后无法重新加载")
    return persisted


async def get_task_plan(plan_id: int) -> Optional[TaskPlan]:
    """按照计划主键读取完整计划实体。

    Args:
        plan_id: 需要查询的任务计划主键。

    Returns:
        找到时返回计划实体，否则返回 ``None``。
    """
    plan_row: Optional[Dict[str, Any]] = await fetch_one(
        "SELECT id, trace_run_id, goal, status, current_step_order "
        "FROM agent_task_plans WHERE id=%s",
        (plan_id,),
    )
    if plan_row is None:
        return None
    step_rows: List[Dict[str, Any]] = await fetch_all(
        "SELECT id, step_key, step_order, title, instruction, status, "
        "result_summary, error_text FROM agent_task_plan_steps "
        "WHERE plan_id=%s ORDER BY step_order ASC",
        (plan_id,),
    )
    return TaskPlan.from_mapping(
        plan_row,
        steps=[TaskPlanStep.from_mapping(item) for item in step_rows],
    )


async def get_task_plan_by_trace(trace_run_id: int) -> Optional[TaskPlan]:
    """读取指定 Trace 对应的任务计划。

    Args:
        trace_run_id: Trace 运行主键。

    Returns:
        Trace 启用了显式规划时返回计划实体，否则返回 ``None``。
    """
    row: Optional[Dict[str, Any]] = await fetch_one(
        "SELECT id FROM agent_task_plans WHERE trace_run_id=%s",
        (trace_run_id,),
    )
    return await get_task_plan(int(row["id"])) if row else None


async def start_task_plan_step(plan_id: int, step: TaskPlanStep) -> None:
    """将指定计划步骤标记为执行中。

    Args:
        plan_id: 所属任务计划主键。
        step: 即将执行的步骤实体。
    """
    now = _now()
    await execute(
        "UPDATE agent_task_plan_steps SET status=%s, started_at=%s, updated_at=%s "
        "WHERE plan_id=%s AND step_key=%s",
        (TaskPlanStepStatus.RUNNING.value, now, now, plan_id, step.step_key),
    )
    await execute(
        "UPDATE agent_task_plans SET status=%s, current_step_order=%s, updated_at=%s "
        "WHERE id=%s",
        (TaskPlanStatus.RUNNING.value, step.order, now, plan_id),
    )


async def finish_task_plan_step(
    plan_id: int,
    step: TaskPlanStep,
) -> None:
    """持久化一个已完成或失败步骤的结果。

    Args:
        plan_id: 所属任务计划主键。
        step: 带有最终状态、结果或错误信息的步骤实体。
    """
    now = _now()
    await execute(
        "UPDATE agent_task_plan_steps SET status=%s, result_summary=%s, "
        "error_text=%s, finished_at=%s, updated_at=%s "
        "WHERE plan_id=%s AND step_key=%s",
        (
            step.status.value,
            step.result_summary or None,
            step.error_text or None,
            now,
            now,
            plan_id,
            step.step_key,
        ),
    )


async def finish_task_plan(plan_id: int, status: TaskPlanStatus) -> None:
    """把整体计划标记为完成或失败。

    Args:
        plan_id: 需要结束的任务计划主键。
        status: 最终计划状态，只允许 completed 或 failed。
    """
    if status not in {TaskPlanStatus.COMPLETED, TaskPlanStatus.FAILED}:
        raise ValueError("任务计划最终状态必须是 completed 或 failed")
    now = _now()
    await execute(
        "UPDATE agent_task_plans SET status=%s, updated_at=%s, finished_at=%s "
        "WHERE id=%s",
        (status.value, now, now, plan_id),
    )


async def fail_active_task_plan_by_trace(
    trace_run_id: int,
    error_text: str,
) -> Optional[TaskPlan]:
    """按 Trace 回收尚未正常结束的任务计划。

    Args:
        trace_run_id: 发生断连或异常的 Trace 运行主键。
        error_text: 导致计划中止的错误说明，只写入当时正在运行的步骤。

    Returns:
        存在计划时返回更新后的任务计划实体；尚未生成计划时返回 ``None``。
    """
    plan = await get_task_plan_by_trace(trace_run_id)
    if plan is None:
        return None
    if plan.status in {TaskPlanStatus.COMPLETED, TaskPlanStatus.FAILED}:
        return plan
    if plan.id is None:
        raise RuntimeError("任务计划缺少数据库主键")

    now = _now()
    # 执行中的步骤记录真实错误；尚未开始的步骤只标记为跳过。
    # error_text 必须先更新，避免 MySQL 按从左到右赋值后丢失原 running 状态。
    await execute(
        "UPDATE agent_task_plan_steps SET "
        "error_text=CASE WHEN status=%s THEN %s ELSE error_text END, "
        "status=CASE WHEN status=%s THEN %s ELSE %s END, "
        "finished_at=%s, updated_at=%s "
        "WHERE plan_id=%s AND status IN (%s, %s)",
        (
            TaskPlanStepStatus.RUNNING.value,
            error_text[:5000],
            TaskPlanStepStatus.RUNNING.value,
            TaskPlanStepStatus.FAILED.value,
            TaskPlanStepStatus.SKIPPED.value,
            now,
            now,
            plan.id,
            TaskPlanStepStatus.RUNNING.value,
            TaskPlanStepStatus.PENDING.value,
        ),
    )
    await finish_task_plan(plan.id, TaskPlanStatus.FAILED)
    return await get_task_plan(plan.id)
