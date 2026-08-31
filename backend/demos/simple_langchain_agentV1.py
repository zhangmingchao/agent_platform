"""最小 LangChain Agent Demo：大模型 + 两个模拟 Tool（异步流式事件版）。

运行前设置环境变量：
    export LLM_API_KEY="你的 API Key"
    export LLM_BASE_URL="https://api.deepseek.com"   # 可选
    export LLM_MODEL="deepseek-chat"                 # 可选

运行：
    python backend/demos/simple_langchain_agent.py
"""

import os
import asyncio
from typing import Any, List

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def query_weather(city: str) -> str:
    """查询指定城市的天气。参数 city 是城市名称。"""
    mock_data = {
        "北京": "晴，26℃",
        "上海": "多云，28℃",
        "深圳": "小雨，30℃",
    }
    return mock_data.get(city, f"暂时没有 {city} 的天气数据")


@tool
def query_order(order_id: str) -> str:
    """查询订单状态。参数 order_id 是订单编号。"""
    mock_data = {
        "A1001": "已发货，预计明天送达",
        "A1002": "待付款",
        "A1003": "已完成",
    }
    return mock_data.get(order_id, "没有找到这个订单")


def build_agent():
    """创建支持 Tool Calling 的 LangChain Agent。"""
    api_key = os.getenv("LLM_API_KEY", "sk-0b9d5ce279744c90a423aaf955c843af")
    if not api_key:
        raise RuntimeError("请先设置环境变量 LLM_API_KEY")

    model = ChatOpenAI(
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        temperature=0,
        streaming=True,          # 启用流式，让 astream_events 能逐字输出
    )

    return create_agent(
        model=model,
        tools=[query_weather, query_order],
        system_prompt=(
            "你是一个简洁的中文助手。"
            "遇到天气或订单问题时必须调用对应工具，不要自己编造数据。"
        ),
    )



async def arun_agent_stream(
    agent,
    user_input: str,
    history: List[BaseMessage] | None = None,
) -> dict[str, Any]:
    """
    异步流式运行 Agent，捕获所有 astream_events 事件并打印每个事件名。
    """
    input_messages = [*(history or []), {"role": "user", "content": user_input}]
    print(f"\n👤 你：{user_input}")
    print("🤖 Agent：", end="", flush=True)

    final_answer = ""
    all_messages = input_messages.copy()
    stream_event_printed = False  # 用于防止同一个事件重复打印太多，但按需求我们保留

    async for event in agent.astream_events(
        {"messages": input_messages},
        version="v2",
    ):
        event_type = event.get("event")
        data = event.get("data", {})
        run_id = event.get("run_id")
        name = event.get("name", "unknown")

        # ----- 1. 链事件 -----
        if event_type == "on_chain_start":
            print(f"\n[{event_type}] 链开始: {name} (ID: {run_id})")
            # 可以打印输入数据（可选）
            # print(f"  输入: {data.get('input')}")

        elif event_type == "on_chain_stream":
            chunk = data.get("chunk")
            print(f"[{event_type}] 链流式输出: {chunk}")

        elif event_type == "on_chain_end":
            print(f"[{event_type}] 链结束: {name} (ID: {run_id})")
            # 可打印输出
            # print(f"  输出: {data.get('output')}")

        elif event_type == "on_chain_error":
            error = data.get("error")
            print(f"[{event_type}] 链错误: {name} -> {error}")

        # ----- 2. LLM / Chat Model 事件 -----
        elif event_type == "on_chat_model_start":
            print(f"\n[{event_type}] 大模型开始思考 (ID: {run_id})")

        elif event_type == "on_chat_model_stream":
            chunk = data.get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                # 每个 chunk 都是独立事件，打印事件名 + 文本内容（不换行）
                print(f"[{event_type}] {chunk.content}", end="", flush=True)
                final_answer += chunk.content

        elif event_type == "on_chat_model_end":
            output = data.get("output")
            print(f"\n[{event_type}] 大模型思考结束")
            if isinstance(output, AIMessage):
                if output.tool_calls:
                    print(f"  决定调用工具: {output.tool_calls}")
                if output.content and not output.tool_calls:
                    # 最终回答（已通过流式累加，但也要存入历史）
                    existing = any(
                        isinstance(m, AIMessage) and m.content == output.content
                        for m in all_messages
                    )
                    if not existing:
                        all_messages.append(output)

        elif event_type == "on_chat_model_error":
            error = data.get("error")
            print(f"[{event_type}] 大模型错误: {error}")

        # 如果是普通 LLM（非 chat），类似处理
        elif event_type == "on_llm_start":
            print(f"\n[{event_type}] LLM 开始 (ID: {run_id})")

        elif event_type == "on_llm_stream":
            chunk = data.get("chunk")
            if chunk and hasattr(chunk, "text") and chunk.text:
                print(f"[{event_type}] {chunk.text}", end="", flush=True)
                final_answer += chunk.text

        elif event_type == "on_llm_end":
            print(f"\n[{event_type}] LLM 结束")
            output = data.get("output")
            # 类似处理

        elif event_type == "on_llm_error":
            error = data.get("error")
            print(f"[{event_type}] LLM 错误: {error}")

        # ----- 3. 工具事件 -----
        elif event_type == "on_tool_start":
            tool_name = event.get("name", "未知工具")
            tool_input = data.get("input", {})
            print(f"\n[{event_type}] 工具开始: {tool_name}({tool_input}) (ID: {run_id})")

        elif event_type == "on_tool_end":
            tool_name = event.get("name", "未知工具")
            output = data.get("output", "")
            print(f"[{event_type}] 工具结束: {tool_name} -> {output}")

            # 构造 ToolMessage 存入历史
            tool_call_id = event.get("run_id")
            if tool_call_id:
                tool_msg = ToolMessage(
                    content=str(output),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
                all_messages.append(tool_msg)

        elif event_type == "on_tool_error":
            tool_name = event.get("name", "未知工具")
            error = data.get("error")
            print(f"[{event_type}] 工具错误: {tool_name} -> {error}")

        # ----- 4. 检索器事件 -----
        elif event_type == "on_retriever_start":
            print(f"\n[{event_type}] 检索开始: {name} (ID: {run_id})")

        elif event_type == "on_retriever_end":
            print(f"[{event_type}] 检索结束: {name}")

        elif event_type == "on_retriever_error":
            error = data.get("error")
            print(f"[{event_type}] 检索错误: {error}")

        # ----- 5. 提示词模板事件 -----
        elif event_type == "on_prompt_start":
            print(f"\n[{event_type}] 提示词格式化开始: {name}")

        elif event_type == "on_prompt_end":
            print(f"[{event_type}] 提示词格式化结束: {name}")

        # ----- 6. Agent 特有事件 -----
        elif event_type == "on_agent_action":
            tool_name = data.get("tool", "未知")
            tool_input = data.get("tool_input", {})
            print(f"\n[{event_type}] Agent 决定执行: {tool_name}({tool_input})")

        elif event_type == "on_agent_finish":
            output = data.get("output")
            print(f"\n[{event_type}] Agent 完成: {output}")

        # ----- 7. 自定义事件 -----
        elif event_type == "on_custom_event":
            custom_data = data.get("data")
            print(f"\n[{event_type}] 自定义事件: {custom_data}")

        # ----- 8. 其他未知事件 -----
        else:
            print(f"\n[{event_type}] 未知事件 (名称: {name})")

    print("\n")  # 最终换行
    return {
        "answer": final_answer,
        "messages": all_messages,
    }



async def main_async():
    """异步主循环"""
    agent = build_agent()
    history = []

    print("🚀 LangChain Agent 异步流式 Demo，输入 quit 退出。")
    print("示例：北京天气怎么样？ / 帮我查询订单 A1001")

    while True:
        user_input = input("\n你：").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue

        try:
            result = await arun_agent_stream(agent, user_input, history)
            # 更新历史记录（使用返回的完整消息列表）
            history = result["messages"]
            # 可选：打印最终答案（但其实已经流式输出过了）
            # print(f"AI：{result['answer']}")
        except Exception as exc:
            print(f"❌ 调用失败：{exc}")


def main():
    """同步入口，启动异步主循环"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()