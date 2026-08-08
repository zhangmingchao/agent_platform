"""一个最小的 async generator（异步生成器）示例。

运行方式（在项目根目录）：
    backend/.venv/bin/python backend/async_generator_demo.py
"""

import asyncio
from typing import AsyncGenerator


async def fake_chat_stream(message: str) -> AsyncGenerator[str, None]:
    """模拟大模型逐段返回回答。

    AsyncGenerator[str, None] 的含义：
    - str：每次 yield 给调用方的数据类型是字符串。
    - None：调用方不会通过 asend() 给生成器传入额外数据。
    """
    answer_parts = ["你好，", "我是一个", "异步生成器", "示例！"]

    print(f"[生成器] 收到用户消息：{message}")

    for part in answer_parts:
        # 模拟调用模型或网络请求时的等待。
        # await 等待期间，事件循环可以执行其他异步任务。
        await asyncio.sleep(0.5)

        # 不用等全部 answer_parts 准备好；每得到一段就立即交给调用方。
        yield part

    print("[生成器] 所有分段都已发送")


async def main() -> None:
    print("[调用方] 开始接收流式回复")

    full_answer = []

    # async for 会不断等待下一次 yield 出来的内容。
    # 当 fake_chat_stream 执行结束时，循环会自动结束。
    async for chunk in fake_chat_stream("请介绍 async generator"):
        print(f"[调用方] 本次收到：{chunk}")
        full_answer.append(chunk)

    print(f"[调用方] 拼接后的完整回复：{''.join(full_answer)}")


if __name__ == "__main__":
    # asyncio.run() 创建事件循环，并运行 async main()。
    asyncio.run(main())
