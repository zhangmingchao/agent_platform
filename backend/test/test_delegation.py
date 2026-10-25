"""委托白名单、预算、串行、取消和父子事件隔离测试。"""
import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from langchain_core.messages import AIMessage

from backend.core.delegation_tools import DelegationBudget, build_delegation_tools, delegation_budget
from backend.core.streaming import stream_agent_response
from backend.models.agent import Agent
from backend.models.delegation import DelegationResult
from backend.models.permission import PermissionPreset
from backend.runtime.models import RuntimeContext
from backend.services.agent_service import _validate_delegation_targets
from backend.services.delegation_service import execute_delegation, restrictive_permission


class DelegationTests(unittest.IsolatedAsyncioTestCase):
    """用模拟 Agent 执行器检查运行边界，不调用真实模型或修改业务数据。"""

    def agent(self, agent_id: int = 2) -> Agent:
        """agent_id 为测试目标 ID；返回具备模型配置的 Agent 实体。"""
        return Agent.from_mapping({'id': agent_id, 'user_id': 1, 'name': '分析员', 'model_config_id': 4})

    async def test_configuration_targets(self) -> None:
        """自身、跨用户/不存在及空白名单禁止保存；有效目标允许保存。"""
        with patch('backend.services.agent_service.get_agent', AsyncMock(return_value=None)):
            for targets in ([], [1], [2], [2, 2]):
                with self.assertRaises(HTTPException):
                    await _validate_delegation_targets(1, {'allow_delegation': True, 'delegation_agent_ids': targets}, 1)
        with patch('backend.services.agent_service.get_agent', AsyncMock(return_value=self.agent())):
            await _validate_delegation_targets(1, {'allow_delegation': True, 'delegation_agent_ids': [2]}, 1)

    async def test_budget_serial_and_single_level(self) -> None:
        """同轮多个工具调用串行、次数受限；新轮重置预算，子任务不提供委托工具。"""
        config = {'id': 1, 'allow_delegation': True, 'delegation_agent_ids': [2], 'delegation_max_calls': 2}
        context = RuntimeContext(user_id=1, agent_id=1)
        active = 0
        peak = 0
        async def execute(parent: RuntimeContext, agent_id: int, task: str, context: str, delegation_id: str) -> DelegationResult:
            """模拟执行；各参数与生产委托服务一致，统计并发峰值。"""
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.01)
            active -= 1
            return DelegationResult(delegation_id=delegation_id, agent_id=agent_id, status='completed', result='分析结果')
        with patch('backend.services.agent_service.get_agent', AsyncMock(return_value=self.agent())), patch('backend.services.delegation_service.execute_delegation', execute), patch('backend.core.delegation_tools.adispatch_custom_event', AsyncMock()):
            tool = (await build_delegation_tools(config, context))[0]
            self.assertEqual(await build_delegation_tools(config, RuntimeContext(user_id=1, delegation_depth=1)), [])
            self.assertEqual(await build_delegation_tools({**config, 'allow_delegation': False}, context), [])
            token = delegation_budget.set(DelegationBudget())
            try:
                results = await asyncio.gather(*[tool.ainvoke({'agent_id': 2, 'task': '分析'}) for _ in range(3)])
                self.assertEqual([json.loads(r)['status'] for r in results], ['completed', 'completed', 'rejected'])
                self.assertEqual(peak, 1)
                bad = json.loads(await tool.ainvoke({'agent_id': 9, 'task': '分析'}))
                self.assertEqual(bad['status'], 'rejected')
            finally:
                delegation_budget.reset(token)
            token = delegation_budget.set(DelegationBudget())
            try:
                self.assertEqual(json.loads(await tool.ainvoke({'agent_id': 2, 'task': '新轮'}))['status'], 'completed')
            finally:
                delegation_budget.reset(token)

    async def test_permission_intersection(self) -> None:
        """父子任一安全模式均禁止写入；自动模式不通过委托扩大权限。"""
        self.assertEqual(restrictive_permission(PermissionPreset.SAFE, PermissionPreset.DEVELOPER), PermissionPreset.SAFE)
        self.assertEqual(restrictive_permission(PermissionPreset.STANDARD, PermissionPreset.AUTO), PermissionPreset.AUTO)
        self.assertEqual(restrictive_permission(PermissionPreset.DEVELOPER, PermissionPreset.STANDARD), PermissionPreset.STANDARD)

    async def test_child_result_and_cancellation(self) -> None:
        """子执行独立工作目录/状态，使用自己模型；取消向下传播并记录 Trace。"""
        child_trace = AsyncMock()
        child_trace.run_id = 20
        child_trace.start.return_value = 20
        parent_trace = AsyncMock()
        parent_trace.run_id = 10
        parent = RuntimeContext(user_id=1, agent_id=1, trace_ctx=parent_trace)
        entered = asyncio.Event()
        async def stream(*args: object, **kwargs: object):
            """模拟子流；收集隔离标签，阻塞场景允许测试取消。"""
            entered.set()
            if blocking:
                await asyncio.Event().wait()
            yield 'data:' + json.dumps({'type': 'pending_text_delta', 'round_id': 'child', 'content': '子任务结果'}) + '\n\n'
            yield 'data:' + json.dumps({'type': 'llm_round_classified', 'round_id': 'child', 'classification': 'answer'}) + '\n\n'
        blocking = False
        factory = AsyncMock(return_value=object())
        with patch('backend.services.agent_service.get_agent', AsyncMock(return_value=self.agent())), patch('backend.services.model_service.get_model', AsyncMock(return_value={'id': 4, 'is_active': True, 'model_id': 'child-model'})), patch('backend.services.skill_service.get_agent_skills', AsyncMock(return_value=[])), patch('backend.services.mcp_config_service.get_agent_mcps', AsyncMock(return_value=[])), patch('backend.core.trace_handler.TraceContext', return_value=child_trace) as trace_constructor, patch('backend.core.agent_factory.create_agent_instance', factory), patch('backend.core.streaming.stream_agent_response', stream):
            result = await execute_delegation(parent, 2, '任务', '背景', 'test-id')
            self.assertEqual(result.result, '子任务结果')
            self.assertEqual(result.trace_run_id, 20)
            self.assertEqual(trace_constructor.call_args.kwargs['parent_trace_run_id'], 10)
            context = factory.call_args.kwargs['runtime_context']
            self.assertEqual(context.workspace_id, 'delegation-test-id')
            self.assertEqual(context.delegation_depth, 1)
            self.assertEqual(context.agent_id, 2)
            blocking = True
            entered.clear()
            running = asyncio.create_task(execute_delegation(parent, 2, '任务', '', 'cancel-id'))
            await entered.wait()
            running.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await running
            child_trace.cancelled.assert_awaited_once()

    async def test_chat_history_restores_delegation_summary(self) -> None:
        """刷新聊天时恢复委托摘要，查询仍按当前用户检查会话归属。"""
        from backend.routers.sessions import api_get_messages
        summary = [{'delegation_id': 'd1', 'agent_name': '分析员', 'status': 'completed', 'result': '结果'}]
        with patch('backend.routers.sessions.fetch_one', AsyncMock(return_value={'id': 1})), patch('backend.routers.sessions.fetch_all', AsyncMock(return_value=[{'role': 'assistant', 'content': '汇总', 'delegation_results': json.dumps(summary)}])):
            messages = await api_get_messages(1, {'user_id': 1})
            self.assertEqual(messages[0]['delegations'], summary)
            self.assertNotIn('delegation_results', messages[0])

    async def test_child_deadline(self) -> None:
        """子 Agent 总时限触发时返回 timed_out，并结束子 Trace。"""
        target = self.agent()
        from dataclasses import replace
        target = replace(target, execution_timeout_seconds=0.01)
        trace = AsyncMock()
        trace.run_id = 20
        async def blocked(*args: object, **kwargs: object) -> list:
            """模拟工具装配阻塞，验证总时限也覆盖执行准备。"""
            await asyncio.Event().wait()
        with patch('backend.services.agent_service.get_agent', AsyncMock(return_value=target)), patch('backend.services.model_service.get_model', AsyncMock(return_value={'id': 4, 'is_active': True, 'model_id': 'child'})), patch('backend.core.trace_handler.TraceContext', return_value=trace), patch('backend.services.skill_service.get_agent_skills', blocked):
            result = await execute_delegation(RuntimeContext(user_id=1, agent_id=1), 2, '任务', '', 'timeout')
            self.assertEqual(result.status, 'timed_out')
            trace.timeout.assert_awaited_once()

    async def test_parent_suppresses_child_events(self) -> None:
        """子模型事件不进入父 SSE 答案，仅委托公开状态允许转发。"""
        class Graph:
            """仅提供事件流的模拟执行器，覆盖父子事件混合场景。"""
            async def astream_events(self, *args: object, **kwargs: object):
                """args 为初始状态，kwargs 为 LangGraph 执行配置。"""
                for tags, name in [(['delegation_child'], '子答案'), ([], '父答案')]:
                    yield {'event': 'on_chat_model_start', 'run_id': name, 'tags': tags, 'name': '模型'}
                    yield {'event': 'on_chat_model_end', 'run_id': name, 'tags': tags, 'data': {'output': AIMessage(content=name)}}
                yield {'event': 'on_custom_event', 'name': 'delegation_completed', 'tags': [], 'data': {'status': 'completed'}}
        events = [json.loads(chunk[5:]) async for chunk in stream_agent_response(Graph(), '问题', 'parent')]
        text = ''.join(event['content'] for event in events if event['type'] == 'pending_text_delta')
        self.assertEqual(text, '父答案')
        self.assertTrue(any(event['type'] == 'delegation_completed' for event in events))
        self.assertIsNone(delegation_budget.get())


if __name__ == '__main__':
    unittest.main()
