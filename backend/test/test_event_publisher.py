import asyncio
import json
import unittest
from unittest.mock import patch

from backend.core.event_publisher import RedisStreamEventPublisher


class _FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.fields = None

    def xadd(self, key, fields, **kwargs):
        self.key = key
        self.fields = dict(fields)
        self.kwargs = kwargs
        return self

    def expire(self, key, ttl):
        self.expire_call = (key, ttl)
        return self

    async def execute(self):
        await asyncio.sleep(0)
        event_id = f"1000-{len(self.redis.entries)}"
        self.redis.entries.append((event_id, self.key, self.fields))
        return [event_id, True]


class _FakeRedis:
    def __init__(self):
        self.entries = []

    def pipeline(self, transaction=True):
        return _FakePipeline(self)


class EventPublisherTest(unittest.IsolatedAsyncioTestCase):
    async def test_publishes_ordered_run_event_fields(self):
        redis = _FakeRedis()
        publisher = RedisStreamEventPublisher(run_id=42)

        with patch(
            "backend.core.event_publisher.get_redis",
            return_value=redis,
        ):
            event_ids = await asyncio.gather(
                publisher.publish("token", {"content": "A"}, node_id="agent-a"),
                publisher.publish("token", {"content": "B"}, node_id="agent-b"),
            )

        self.assertEqual(event_ids, ["1000-0", "1000-1"])
        first = redis.entries[0]
        second = redis.entries[1]
        self.assertEqual(first[1], "agent:run:42:events")
        self.assertEqual(first[2]["type"], "token")
        self.assertEqual(first[2]["runId"], "42")
        self.assertEqual(first[2]["nodeId"], "agent-a")
        self.assertEqual(first[2]["sequence"], "1")
        self.assertEqual(json.loads(first[2]["payload"]), {"content": "A"})
        self.assertEqual(second[2]["sequence"], "2")


if __name__ == "__main__":
    unittest.main()
