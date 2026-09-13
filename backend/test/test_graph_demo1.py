# pip install langgraph langchain-core

from typing import Literal, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph


class RouterState(TypedDict, total=False):
    question: str
    route: Literal["agent_a", "agent_b"]
    answer: str


@tool
def baidu_search(query: str) -> str:
    """模拟百度搜索。"""
    return f"[百度搜索结果] 关于“{query}”的搜索结果：这是模拟数据。"


@tool
def weather_query(city: str) -> str:
    """模拟天气查询。"""
    weather_data = {
        "北京": "晴，26℃",
        "上海": "多云，28℃",
        "广州": "阵雨，31℃",
    }
    return weather_data.get(city, f"暂时没有查询到{city}的天气")


def router_node(state: RouterState) -> RouterState:
    """模拟问题分类 Router。"""
    question = state["question"]

    weather_keywords = ["天气", "温度", "下雨", "气温"]

    if any(keyword in question for keyword in weather_keywords):
        route = "agent_b"
    else:
        route = "agent_a"

    print(f"Router 分类结果：{route}")
    return {"route": route}


def agent_a_node(state: RouterState) -> RouterState:
    """AgentA：负责百度搜索。"""
    print("进入 AgentA")
    result = baidu_search.invoke({"query": state["question"]})
    return {"answer": result}


def agent_b_node(state: RouterState) -> RouterState:
    """AgentB：负责天气查询。"""
    print("进入 AgentB")

    question = state["question"]
    city = next(
        (name for name in ["北京", "上海", "广州"] if name in question),
        "北京",
    )

    result = weather_query.invoke({"city": city})
    return {"answer": result}


def select_route(state: RouterState) -> str:
    return state["route"]


builder = StateGraph(RouterState)

builder.add_node("router", router_node)
builder.add_node("agent_a", agent_a_node)
builder.add_node("agent_b", agent_b_node)

builder.add_edge(START, "router")

builder.add_conditional_edges(
    "router",
    select_route,
    {
        "agent_a": "agent_a",
        "agent_b": "agent_b",
    },
)

# 两个 Agent 执行完毕后都直接结束
builder.add_edge("agent_a", END)
builder.add_edge("agent_b", END)

graph = builder.compile()


if __name__ == "__main__":
    questions = [
        "帮我搜索一下 LangGraph 是什么",
        "北京今天天气怎么样",
    ]

    for question in questions:
        print(f"\n用户问题：{question}")
        result = graph.invoke({"question": question})
        print(f"最终答案：{result['answer']}")
