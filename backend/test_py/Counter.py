import asyncio


class Counter:
    """自定义异步迭代器：模拟流式输出 1 到 limit"""

    def __init__(self, limit: int):
        self.limit = limit
        self.count = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.count >= self.limit:
            raise StopAsyncIteration  # 循环结束信号
        self.count += 1
        await asyncio.sleep(0.3)  # 模拟网络延迟（LLM 吐 token 的间隔）
        return self.count


async def main():
    print("=== 演示 1：异步迭代器基本用法 ===")
    counter = Counter(5)
    async for num in counter:
        print(f"收到: {num}")

    print("\n=== 演示 2：模拟 CrewAI 的 execution 对象（流式 + 最终结果）===")

    class FakeCrewOutput:
        """模拟 CrewAI 的 CrewOutput：既能 async for 流式拿 chunk，又能 .result 拿完整结果"""

        def __init__(self, chunks: list):
            self._chunks = chunks
            self._index = 0
            self.result = "".join(chunks)  # 完整结果

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self._index >= len(self._chunks):
                raise StopAsyncIteration
            chunk = self._chunks[self._index]
            self._index += 1
            await asyncio.sleep(0.2)  # 模拟 LLM 吐字延迟
            return chunk

    # 模拟 LLM 流式返回的 token 片段
    execution = FakeCrewOutput(["你", "好", "，", "今天", "天气", "不错", "！"])

    print("流式接收：")
    async for chunk in execution:
        print(f"  chunk: {chunk}")

    print(f"\n最终完整结果: {execution.result}")

    print("\n=== 演示 3：模拟项目的 event_queue 模式 ===")

    event_queue = asyncio.Queue()

    async def background_task():
        """后台任务：往队列里 put 事件"""
        for i in range(3):
            await asyncio.sleep(0.3)
            await event_queue.put({"type": "chunk", "content": f"事件 {i}"})
        return "后台任务完成"

    task = asyncio.create_task(background_task())

    print("主流程消费队列：")
    while not task.done() or not event_queue.empty():
        try:
            event = await asyncio.wait_for(event_queue.get(), timeout=0.5)
            print(f"  收到: {event}")
        except asyncio.TimeoutError:
            continue

    final = await task
    print(f"最终结果: {final}")


if __name__ == "__main__":
    asyncio.run(main())