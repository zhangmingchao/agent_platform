import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId

from backend.services import mongo_trace_service


class MongoTraceServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_span_contains_owner_and_workflow_scope(self):
        collection = SimpleNamespace(
            insert_one=AsyncMock(return_value=SimpleNamespace(inserted_id=ObjectId()))
        )
        with patch.object(mongo_trace_service, "get_trace_spans_collection", return_value=collection):
            span_id = await mongo_trace_service.create_trace_span(
                trace_run_id=10,
                user_id=20,
                agent_id=30,
                workflow_run_id=40,
                workflow_step_id=50,
                span_type="llm",
                name="deepseek-chat",
                input_data={"prompt": "hello"},
            )

        self.assertTrue(ObjectId.is_valid(span_id))
        document = collection.insert_one.await_args.args[0]
        self.assertEqual(document["trace_run_id"], 10)
        self.assertEqual(document["user_id"], 20)
        self.assertEqual(document["workflow"], {"run_id": 40, "step_id": 50})
        self.assertEqual(document["status"], "running")
        self.assertIsNotNone(document["expire_at"])

    async def test_finish_span_updates_terminal_fields(self):
        collection = SimpleNamespace(update_one=AsyncMock())
        span_id = str(ObjectId())
        with patch.object(mongo_trace_service, "get_trace_spans_collection", return_value=collection):
            await mongo_trace_service.finish_trace_span(
                span_id,
                output_data={"answer": "ok"},
                tokens_used=12,
                duration_ms=35,
            )

        query, update = collection.update_one.await_args.args
        self.assertEqual(query["_id"], ObjectId(span_id))
        self.assertEqual(update["$set"]["status"], "success")
        self.assertEqual(update["$set"]["tokens_used"], 12)
        self.assertEqual(update["$set"]["output_data"], {"answer": "ok"})


if __name__ == "__main__":
    unittest.main()
