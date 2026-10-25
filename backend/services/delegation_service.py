"""执行独立子 Agent，复用用户 Runtime、模型额度和流式 Trace 机制。"""
import asyncio
from dataclasses import replace
from datetime import datetime
import json

from ..core.agent_output import append_schema_instruction, parse_and_validate_structured_output, render_prompt_template
from ..models.api_access import InvocationSource
from ..models.delegation import DelegationResult
from ..models.permission import PermissionPreset
from ..runtime.models import RuntimeContext


def restrictive_permission(parent: PermissionPreset, child: PermissionPreset) -> PermissionPreset:
    """parent 为父权限、child 为目标权限；取交集的保守预设，避免子任务扩大执行边界。"""
    if parent == child:
        return parent
    if PermissionPreset.SAFE in (parent, child):
        return PermissionPreset.SAFE
    if PermissionPreset.AUTO in (parent, child):
        return PermissionPreset.AUTO
    return PermissionPreset.STANDARD


async def execute_delegation(
    parent: RuntimeContext, agent_id: int, task: str, context: str, delegation_id: str,
) -> DelegationResult:
    """parent 为可信父上下文，agent_id 为目标，task/context 为必要输入，delegation_id 为唯一关联标识。"""
    from ..core.agent_factory import create_agent_instance
    from ..core.streaming import stream_agent_response
    from ..core.trace_handler import TraceContext
    from .agent_service import get_agent
    from .mcp_config_service import get_agent_mcps
    from .model_service import get_model
    from .skill_service import get_agent_skills

    trace: TraceContext | None = None
    name = ''
    try:
        target = await get_agent(agent_id, parent.user_id)
        if target is None or target.id == parent.agent_id or parent.delegation_depth > 0:
            return DelegationResult(delegation_id=delegation_id, agent_id=agent_id, status='rejected', error='目标不可用或不允许嵌套委托')
        name = target.name
        if not target.model_config_id:
            raise ValueError('目标 Agent 未配置自定义模型')
        model = await get_model(target.model_config_id, parent.user_id)
        if not model or not model.get('is_active'):
            raise ValueError('目标 Agent 模型不存在或未启用')
        input_text = f'子任务：\n{task}\n\n必要背景：\n{context}'
        # 单层子执行使用独立线程，父任务上下文不复制进消息历史。
        trace = TraceContext(
            session_id=parent.session_id, user_id=parent.user_id, agent_id=target.id,
            model_name=model['model_id'], workflow_run_id=parent.workflow_run_id,
            workflow_step_id=parent.workflow_step_id,
            invocation_source=InvocationSource(parent.invocation_source),
            parent_trace_run_id=parent.trace_ctx.run_id if parent.trace_ctx else None,
        )
        await trace.start(input_text)
        child_context = replace(
            parent, workspace_id=f'delegation-{delegation_id}', agent_id=target.id,
            permission_preset=restrictive_permission(parent.permission_preset, target.permission_preset),
            trace_ctx=trace, delegation_depth=1,
        )
        # 目标整体超时覆盖装配、模型请求、工具和最终结果解析；取消向下传播。
        async with asyncio.timeout(target.execution_timeout_seconds):
            skills = await get_agent_skills(target.id)
            mcps = await get_agent_mcps(target.id)
            rendered = render_prompt_template(target.system_prompt, target.prompt_variables, {
                'user_input': input_text, 'user_id': parent.user_id,
                'session_id': parent.session_id or '', 'current_date': datetime.now().strftime('%Y-%m-%d'),
            })
            graph = await create_agent_instance(
                target.with_system_prompt(append_schema_instruction(rendered, target.output_schema)),
                skills, [item.to_factory_dict() for item in mcps], model,
                runtime_context=child_context, trace_ctx=trace, planning_execution_prompt=rendered,
            )
            rounds: dict[str, str] = {}
            answers: list[str] = []
            error = ''
            timed_out = False
            async for chunk in stream_agent_response(
                graph, input_text, f'delegation-{delegation_id}',
                max_tool_rounds=target.iteration_count,
                execution_timeout_seconds=target.execution_timeout_seconds,
                trace_ctx=trace, execution_scope='delegation_child',
                state_context={'planning_mode': target.planning_mode.value, 'current_input': input_text},
            ):
                event = json.loads(chunk.removeprefix('data:').strip())
                if event['type'] == 'pending_text_delta':
                    key = event['round_id']
                    rounds[key] = rounds.get(key, '') + event['content']
                elif event['type'] == 'llm_round_classified':
                    text = rounds.pop(event['round_id'], '')
                    if event['classification'] == 'answer':
                        answers.append(text)
                elif event['type'] == 'error':
                    error = event['content']
                    timed_out = event.get('code') == 'agent_timeout'
            if timed_out:
                raise TimeoutError
            if error:
                raise ValueError(error)
            output = ''.join(answers)
            if not output.strip():
                raise ValueError('子 Agent 没有返回最终答案')
            parse_and_validate_structured_output(output, target.output_schema)
            await trace.finish(output)
            return DelegationResult(delegation_id=delegation_id, agent_id=agent_id, agent_name=name, status='completed', result=output[:20000], trace_run_id=trace.run_id)
    except asyncio.CancelledError:
        if trace:
            await trace.cancelled('父任务取消或整体超时，子任务同步取消')
        raise
    except TimeoutError:
        if trace:
            await trace.timeout('子 Agent 整体执行超时')
        return DelegationResult(delegation_id=delegation_id, agent_id=agent_id, agent_name=name, status='timed_out', error='子 Agent 整体执行超时', trace_run_id=trace.run_id if trace else None)
    except Exception:
        # 上游 SDK 异常可能带请求信息；完整凭据和异常原文不进入工具结果或 Trace。
        error = '子任务执行失败，请查看目标模型、工具权限和配置；可调整任务后重试'
        if trace:
            await trace.error(error)
        return DelegationResult(delegation_id=delegation_id, agent_id=agent_id, agent_name=name, status='failed', error=error, trace_run_id=trace.run_id if trace else None)
