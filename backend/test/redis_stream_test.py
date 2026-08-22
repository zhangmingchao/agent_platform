import json
import threading
import time

import redis





REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
RUN_ID = "run_demo_001"
STREAM_KEY = f"agent:run:{RUN_ID}:events"


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)

def write_event(event_type:str,payload:dict ) -> str:
    """向 Redis Stream 追加一条事件，返回 Redis 自动生成的 eventId。"""
    print(f"[生产者]写入event_id=  ,type={event_type},payload={json.dumps(payload)}")
    event_id = redis_client.xadd(STREAM_KEY, {
        "type":event_type,
        "payload": json.dumps(payload),
    })
    print(f"[生产者]写入event_id={event_id},type={event_type},payload={json.dumps(payload)}")
    return event_id


def agent_producer():
    """模拟后台 Agent Worker 持续产生状态、工具调用和 LLM Token。"""
    write_event("status", {"status": "RUNNING", "message": "Agent 开始执行"})
    time.sleep(1)

    write_event(
        "tool_result",
        {
            "tool": "query_sales_data",
            "status": "success",
            "message": "销售数据查询完成",
        },
    )
    time.sleep(1)

    answer_parts = [
        "华北区销售额下降，",
        "主要原因是订单量下降 18%，",
        "同时广告转化率下降 12%。",
    ]

    for content in answer_parts:
        write_event("token", {"content": content})
        time.sleep(0.8)

    write_event(
        "completed",
        {
            "status": "COMPLETED",
            "finalAnswer": "".join(answer_parts),
        },
    )

def event_consumer(start_event_id: str = "0-0"):
    """
    模拟 SSE Event 接口持续读取 Stream。

    start_event_id:
    - "0-0"：从头读取。
    - 指定某个 Redis Stream eventId：从该事件之后继续读取。
    """
    last_event_id = start_event_id
    answer = ""

    print(f"[消费者] 从 {last_event_id} 开始读取")

    while True:
        results = redis_client.xread(
            streams={STREAM_KEY: last_event_id},
            count=10,
            block=3000,
        )

        if not results:
            print("[消费者] 暂时没有新事件，继续等待")
            continue

        for _, events in results:
            for event_id, fields in events:
                last_event_id = event_id

                event_type = fields["type"]
                payload = json.loads(fields["payload"])

                print(
                    f"[消费者] 收到 eventId={event_id}, "
                    f"type={event_type}, payload={payload}"
                )

                if event_type == "token":
                    answer += payload["content"]
                    print(f"[消费者] 当前回答：{answer}")

                if event_type == "completed":
                    print(f"[消费者] 最终回答：{payload['finalAnswer']}")
                    print(f"[消费者] 最后事件 ID：{last_event_id}")
                    return


def main():
    # 仅用于保证每次演示输出干净。
    # 正式环境不要在创建任务时删除历史 Stream。
    redis_client.delete(STREAM_KEY)

    consumer_thread = threading.Thread(
        target=event_consumer,
        name="event-consumer",
    )

    producer_thread = threading.Thread(
        target=agent_producer,
        name="agent-producer",
    )

    consumer_thread.start()
    time.sleep(0.3)
    producer_thread.start()

    producer_thread.join()
    consumer_thread.join()


if __name__ == "__main__":
    main()