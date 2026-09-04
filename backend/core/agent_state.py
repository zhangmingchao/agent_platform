"""Agent Platform 的 LangGraph 自定义状态定义与辅助方法。"""

import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence, cast

from langchain_core.messages import BaseMessage
from langgraph.prebuilt.chat_agent_executor import AgentState
from typing_extensions import NotRequired

log = logging.getLogger(__name__)


class AgentPlatformState(AgentState):
    """统一保存 Agent 的模型交互上下文和平台业务上下文。

    从 ``AgentState`` 继承的字段：
    - ``messages``：保存用户问题、模型回复、工具请求和工具执行结果；
    - ``remaining_steps``：由 LangGraph 管理剩余执行步数，防止工具调用无限循环。

    继承内置状态可以保持 ``create_react_agent`` 原有的模型与工具循环不变。
    平台扩展字段均为可选字段，聊天和工作流可以按需写入，也兼容只传
    ``messages`` 的旧调用方式。
    """

    # 本次运行允许工具访问的文件 ID；只存标识，不保存文件内容或宿主机路径。
    runtime_file_ids: NotRequired[List[str]]
    # 当前 Agent 被授权使用的 Skill 名称，不表示相应 Skill 已经被读取。
    available_skills: NotRequired[List[str]]
    # 本次执行已经读取或加载的 Skill 名称，用于区分“可用”和“已加载”。
    loaded_skills: NotRequired[List[str]]
    # 当前轮用户问题或工作流节点输入；messages 仍负责保存完整交互历史。
    current_input: NotRequired[str]
    # 当前执行的工作流节点 ID；普通聊天没有节点时可以不设置。
    current_node_id: NotRequired[Optional[str]]
    # 模型原始输出经过业务 Schema 解析和校验后得到的结构化结果。
    structured_result: NotRequired[Dict[str, Any]]
    # 人工审批状态，例如 pending、approved 或 rejected。
    approval_status: NotRequired[str]
    # Agent 或工作流执行过程中的错误信息；没有错误时不写入。
    error: NotRequired[str]


def _unique_strings(values: Optional[Iterable[Any]]) -> List[str]:
    """清洗字符串列表并保持原有顺序，避免 State 中出现重复 ID 或名称。"""
    result: List[str] = []
    seen = set()
    for value in values or []:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def build_agent_state(
    messages: Sequence[BaseMessage],
    *,
    runtime_file_ids: Optional[Iterable[str]] = None,
    available_skills: Optional[Iterable[str]] = None,
    loaded_skills: Optional[Iterable[str]] = None,
    current_input: str = "",
    current_node_id: Optional[str] = None,
    approval_status: str = "",
) -> AgentPlatformState:
    """构造兼容原 Agent 的初始 State。

    这里只保存轻量业务标识，不把文件内容、API Key、数据库连接或宿主机路径
    放入 Checkpoint，避免状态膨胀和敏感信息泄露。
    """
    state: Dict[str, Any] = {
        "messages": list(messages),
        "runtime_file_ids": _unique_strings(runtime_file_ids),
        "available_skills": _unique_strings(available_skills),
        "loaded_skills": _unique_strings(loaded_skills),
        "current_input": str(current_input or ""),
    }
    if current_node_id is not None:
        state["current_node_id"] = str(current_node_id)
    if approval_status:
        state["approval_status"] = str(approval_status)
    return cast(AgentPlatformState, state)


async def update_agent_checkpoint_state(
    agent_executor,
    thread_id: str,
    updates: Dict[str, Any],
) -> bool:
    """在 Agent 执行完成后安全追加业务状态。

    Checkpoint 更新失败不能影响现有聊天或工作流结果，因此这里记录警告并返回
    ``False``。MySQL 仍然是结构化结果和业务状态的长期事实来源。
    """
    if not updates:
        return False
    try:
        await agent_executor.aupdate_state(
            {"configurable": {"thread_id": thread_id}},
            updates,
        )
        return True
    except Exception as exc:
        log.warning("[AgentState] checkpoint update failed | thread_id=%s | error=%s", thread_id, exc)
        return False
