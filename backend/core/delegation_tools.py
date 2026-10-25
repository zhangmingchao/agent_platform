"""单层 Agent 委托工具，按当前执行作用域限制次数并串行调度。"""
from contextvars import ContextVar
from dataclasses import dataclass, field
import asyncio
import json
from uuid import uuid4

from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.tools import StructuredTool

from ..models.agent import Agent
from ..models.delegation import DelegateTaskInput, DelegationResult
from ..runtime.models import RuntimeContext


@dataclass
class DelegationBudget:
    """一次父任务的委托预算；used 为已消耗次数，lock 保证所有调用顺序执行。"""

    used: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


# 每次顶层执行初始化；LangGraph 子任务继承同一预算，不依赖长驻工具闭包计数。
delegation_budget: ContextVar[DelegationBudget | None] = ContextVar('delegation_budget', default=None)


async def record_delegation_event(context: RuntimeContext, phase: str, payload: dict[str, object]) -> None:
    """context 为父运行归属，phase 为委托阶段，payload 为公开摘要；审计结果最多保存 500 字符。"""
    from ..models.session_event import SessionEventRecord, SessionEventSource, SessionEventType
    from ..services.session_event_service import append_session_event
    if context.trace_ctx is None or context.trace_ctx.run_id is None:
        return
    summary = dict(payload)
    if 'result' in summary:
        summary['result'] = str(summary['result'])[:500]
    await append_session_event(SessionEventRecord(
        user_id=context.user_id, session_id=context.session_id,
        trace_run_id=context.trace_ctx.run_id, agent_id=context.agent_id,
        workflow_run_id=context.workflow_run_id, workflow_step_id=context.workflow_step_id,
        event_source=SessionEventSource.SYSTEM, event_type=SessionEventType.TOOL_STAGE,
        phase=phase, name=str(payload.get('agent_name') or 'DelegateTask'),
        status=str(payload.get('status') or ''), payload=summary,
    ))


async def build_delegation_tools(agent: dict[str, object], context: RuntimeContext | None) -> list[StructuredTool]:
    """agent 为当前工厂配置，context 为归属及权限；子执行或关闭委托时不提供工具。"""
    if context is None or not agent.get('allow_delegation') or context.delegation_depth > 0:
        return []
    from ..services.agent_service import get_agent
    allowed: dict[int, Agent] = {}
    for target_id in agent.get('delegation_agent_ids') or []:
        if int(target_id) == int(agent['id']):
            continue
        target = await get_agent(int(target_id), context.user_id)
        if target is not None:
            allowed[target.id] = target
    if not allowed:
        return []
    maximum = max(1, min(int(agent.get('delegation_max_calls') or 3), 10))

    async def delegate_task(agent_id: int, task: str, context: str = '') -> str:
        """agent_id 为白名单目标，task 为子任务，context 为必要背景；工具边界返回实体 JSON。"""
        from ..services.delegation_service import execute_delegation
        delegation_id = str(uuid4())
        budget = delegation_budget.get()
        if budget is None or agent_id not in allowed:
            return DelegationResult(delegation_id=delegation_id, agent_id=agent_id, status='rejected', error='委托作用域缺失或目标不在白名单').model_dump_json()
        async with budget.lock:
            if budget.used >= maximum:
                return DelegationResult(delegation_id=delegation_id, agent_id=agent_id, status='rejected', error=f'本轮最多允许 {maximum} 次委托').model_dump_json()
            budget.used += 1
            target = allowed[agent_id]
            started = {
                'delegation_id': delegation_id, 'agent_id': agent_id,
                'agent_name': target.name, 'task': task[:500], 'status': 'running',
            }
            await record_delegation_event(runtime_context, 'delegation_started', started)
            await adispatch_custom_event('delegation_started', started)
            # 工具形参 context 是模型提供的文本；runtime_context 是闭包中的可信归属。
            result = await execute_delegation(runtime_context, agent_id, task, context, delegation_id)
            await record_delegation_event(runtime_context, 'delegation_completed', result.model_dump())
            await adispatch_custom_event('delegation_completed', result.model_dump())
            return result.model_dump_json()

    runtime_context = context
    summary = json.dumps([{'agent_id': item.id, 'name': item.name, 'description': item.description[:1000]} for item in allowed.values()], ensure_ascii=False)
    return [StructuredTool.from_function(
        name='DelegateTask', coroutine=delegate_task, args_schema=DelegateTaskInput,
        description=f'把独立子任务交给授权 Agent，等待完成后获取结果，再由你汇总回答。每轮最多 {maximum} 次；禁止要求目标继续委托。只传必要背景，不传凭据。目标列表：{summary}',
    )]
