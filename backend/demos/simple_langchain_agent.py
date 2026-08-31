"""最小 LangChain Agent Demo：大模型 + 两个模拟 Tool。

运行前设置环境变量：
    export LLM_API_KEY="你的 API Key"
    export LLM_BASE_URL="https://api.deepseek.com"   # 可选
    export LLM_MODEL="deepseek-chat"                 # 可选

运行：
    python backend/demos/simple_langchain_agent.py
"""


import os
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def query_weather(city: str) -> str:
    """查询指定城市的天气。参数 city 是城市名称。"""
    # 这是模拟 Tool，真实项目中可以替换成天气 API 请求。
    mock_data = {
        "北京": "晴，26℃",
        "上海": "多云，28℃",
        "深圳": "小雨，30℃",
    }
    return mock_data.get(city, f"暂时没有 {city} 的天气数据")


@tool
def query_order(order_id: str) -> str:
    """查询订单状态。参数 order_id 是订单编号。"""
    # 这是模拟 Tool，真实项目中可以替换成数据库或订单服务查询。
    mock_data = {
        "A1001": "已发货，预计明天送达",
        "A1002": "待付款",
        "A1003": "已完成",
    }
    return mock_data.get(order_id, "没有找到这个订单")


def build_agent():
    """创建支持 Tool Calling 的 LangChain Agent。"""
    api_key = "sk-0b9d5ce279744c90a423aaf955c843af"
    if not api_key:
        raise RuntimeError("请先设置环境变量 LLM_API_KEY")

    model = ChatOpenAI(
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        temperature=0,
    )

    return create_agent(
        model=model,
        tools=[query_weather, query_order],
        system_prompt=(
            "你是一个简洁的中文助手。"
            "遇到天气或订单问题时必须调用对应工具，不要自己编造数据。"
        ),
    )


def run_agent(agent, user_input: str, history: list | None = None) -> dict[str, Any]:
    """实际调用大模型，并把 Tool 调用与最终回复整理成容易观察的结果。"""
    input_messages = [*(history or []), {"role": "user", "content": user_input}]

    # invoke 内部会自动执行这个循环：
    # 大模型 -> Tool Calling -> 执行 Tool -> Tool 结果发回大模型 -> 最终回答。
    result = agent.invoke({"messages": input_messages})
    all_messages = result["messages"]
    new_messages = all_messages[len(input_messages):]

    execution_steps = []
    final_answer = ""

    for message in new_messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                step = {
                    "type": "tool_call",
                    "tool": call["name"],
                    "arguments": call.get("args", {}),
                }
                execution_steps.append(step)
                print(f"[大模型决定调用 Tool] {step['tool']} 参数={step['arguments']}")

        elif isinstance(message, ToolMessage):
            step = {
                "type": "tool_result",
                "tool": message.name,
                "content": str(message.content),
            }
            execution_steps.append(step)
            print(f"[Tool 返回] {step['tool']} -> {step['content']}")

        elif isinstance(message, AIMessage):
            # 没有 tool_calls 的最后一条 AIMessage 就是大模型整理后的最终回答。
            final_answer = str(message.content)
            execution_steps.append({"type": "final_answer", "content": final_answer})
            print(f"[大模型最终回答] {final_answer}")

    return {
        "answer": final_answer,
        "steps": execution_steps,
        "messages": all_messages,
    }


def main():
    agent = build_agent()
    history = []

    print("LangChain Agent Demo，输入 quit 退出。")
    print("示例：北京天气怎么样？ / 帮我查询订单 A1001")

    while True:
        user_input = input("\n你：").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue

        try:
            result = run_agent(agent, user_input, history)
            history = result["messages"]
            print(f"AI：{result['answer']}")
        except Exception as exc:
            # 实际项目中可以在这里转换为统一错误响应、记录 Trace 或执行重试。
            print(f"调用失败：{exc}")


if __name__ == "__main__":
    main()
