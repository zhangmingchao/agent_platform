import json
import typing

from langgraph.graph import StateGraph, MessagesState, START, END

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}



if __name__ == "__main__":
    graph = StateGraph(MessagesState)
    graph.add_node(mock_llm)
    graph.add_edge(START, "mock_llm")
    graph.add_edge("mock_llm", END)
    graph = graph.compile()

    result:dict[str, typing.Any] = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
    print(json.dumps(result))