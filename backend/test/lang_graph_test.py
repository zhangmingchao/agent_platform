import json
import typing

from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph


class WorkflowState(MessagesState):
    # Router 分类结果
    route: typing.NotRequired[
        typing.Literal["baidu_search", "weather_query"]
    ]

    # 从用户消息中提取的问题
    question: typing.NotRequired[str]

    # 外部传入的审批结果
    approved: typing.NotRequired[bool]

    # 审批节点处理后的状态
    approval_status: typing.NotRequired[
        typing.Literal["approved", "rejected"]
    ]

    # 最终执行结果
    result: typing.NotRequired[str]


@tool
def baidu_search(query: str) -> str:
    """模拟百度搜索。"""
    return f"百度搜索结果：找到了与“{query}”相关的内容"


@tool
def weather_query(city: str) -> str:
    """模拟天气查询。"""
    weather_data = {
        "北京": "晴，26℃",
        "上海": "多云，28℃",
        "广州": "阵雨，31℃",
    }

    return weather_data.get(city, f"暂时没有查询到{city}的天气")


def receive_input(state: WorkflowState) -> dict[str, typing.Any]:
    """第一步：接收并提取用户输入。"""
    last_message = state["messages"][-1]
    question = str(last_message.content)

    print(f"接收到用户问题：{question}")

    return {
        "question": question,
    }


def router_node(state: WorkflowState) -> dict[str, typing.Any]:
    """第二步：对用户问题进行分类。"""
    question = state["question"]

    weather_keywords = ["天气", "温度", "气温", "下雨"]

    if any(keyword in question for keyword in weather_keywords):
        route = "weather_query"
    else:
        route = "baidu_search"

    print(f"Router 分类结果：{route}")

    return {
        "route": route,
    }


def select_agent(
    state: WorkflowState,
) -> typing.Literal["baidu_search", "weather_query"]:
    """根据 Router 的分类结果选择分支。"""
    return state["route"]


def baidu_search_agent(
    state: WorkflowState,
) -> dict[str, typing.Any]:
    """分类1：百度搜索 Agent。"""
    print("进入百度搜索 Agent")

    result = baidu_search.invoke({
        "query": state["question"],
    })

    return {
        "result": result,
        "messages": [
            {
                "role": "ai",
                "content": result,
            }
        ],
    }


def approval_node(state: WorkflowState) -> dict[str, typing.Any]:
    """天气查询前的审批节点。"""
    approved = state.get("approved", False)

    if approved:
        approval_status = "approved"
        print("审批结果：通过")
    else:
        approval_status = "rejected"
        print("审批结果：拒绝")

    return {
        "approval_status": approval_status,
    }


def select_approval_result(
    state: WorkflowState,
) -> typing.Literal["approved", "rejected"]:
    """根据审批结果选择后续流程。"""
    return state["approval_status"]


def weather_agent(
    state: WorkflowState,
) -> dict[str, typing.Any]:
    """分类2：天气查询 Agent。"""
    print("进入天气查询 Agent")

    question = state["question"]

    city = next(
        (
            city
            for city in ["北京", "上海", "广州"]
            if city in question
        ),
        "北京",
    )

    result = weather_query.invoke({
        "city": city,
    })

    return {
        "result": result,
        "messages": [
            {
                "role": "ai",
                "content": result,
            }
        ],
    }


def rejected_node(
    state: WorkflowState,
) -> dict[str, typing.Any]:
    """审批拒绝后，不执行天气查询。"""
    result = "天气查询审批未通过，任务已终止"

    return {
        "result": result,
        "messages": [
            {
                "role": "ai",
                "content": result,
            }
        ],
    }


def create_graph():
    graph = StateGraph(WorkflowState)

    # 注册节点
    graph.add_node("receive_input", receive_input)
    graph.add_node("router", router_node)
    graph.add_node("baidu_search_agent", baidu_search_agent)
    graph.add_node("approval", approval_node)
    graph.add_node("weather_agent", weather_agent)
    graph.add_node("rejected", rejected_node)

    # START → 接收输入 → Router
    graph.add_edge(START, "receive_input")
    graph.add_edge("receive_input", "router")

    # Router 条件分支
    graph.add_conditional_edges(
        "router",
        select_agent,
        {
            "baidu_search": "baidu_search_agent",
            "weather_query": "approval",
        },
    )

    # 天气审批条件分支
    graph.add_conditional_edges(
        "approval",
        select_approval_result,
        {
            "approved": "weather_agent",
            "rejected": "rejected",
        },
    )

    # 各分支结束
    graph.add_edge("baidu_search_agent", END)
    graph.add_edge("weather_agent", END)
    graph.add_edge("rejected", END)

    return graph.compile()


def run_example(
    graph,
    question: str,
    approved: bool = False,
) -> None:
    result = graph.invoke({
        "messages": [
            {
                "role": "user",
                "content": question,
            }
        ],
        "approved": approved,
    })

    output = {
        "question": result["question"],
        "route": result["route"],
        "approval_status": result.get("approval_status"),
        "result": result["result"],
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    workflow = create_graph()

    print("\n========== 场景1：百度搜索 ==========")
    run_example(
        workflow,
        question="帮我搜索一下 LangGraph 是什么",
    )

    print("\n========== 场景2：天气审批通过 ==========")
    run_example(
        workflow,
        question="北京今天天气怎么样",
        approved=True,
    )

    print("\n========== 场景3：天气审批拒绝 ==========")
    run_example(
        workflow,
        question="上海今天天气怎么样",
        approved=False,
    )
