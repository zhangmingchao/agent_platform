"""Sandbox Service HTTP 客户端测试。"""

import unittest
from unittest.mock import AsyncMock, patch

from backend.runtime.sandbox_client import SandboxServiceError, execute_in_sandbox


class SandboxClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_sends_internal_token_and_execution_context(self):
        response = AsyncMock()
        response.status_code = 200
        response.json = lambda: {"status": "completed", "exitCode": 0}
        client = AsyncMock()
        client.post.return_value = response
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        payload = {
            "executionId": "exec-1",
            "userId": 9,
            "workspaceId": "project-1",
            "timeoutSeconds": 30,
        }
        with patch("backend.runtime.sandbox_client.httpx.AsyncClient", return_value=client):
            result = await execute_in_sandbox(payload)
        self.assertEqual(result["status"], "completed")
        _, kwargs = client.post.await_args
        self.assertEqual(kwargs["json"], payload)
        self.assertTrue(kwargs["headers"]["Authorization"].startswith("Bearer "))

    async def test_surfaces_sandbox_rejection(self):
        response = AsyncMock()
        response.status_code = 503
        response.json = lambda: {"detail": "Docker Engine 不可用"}
        client = AsyncMock()
        client.post.return_value = response
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None
        with (
            patch("backend.runtime.sandbox_client.httpx.AsyncClient", return_value=client),
            self.assertRaises(SandboxServiceError),
        ):
            await execute_in_sandbox({"timeoutSeconds": 30})


if __name__ == "__main__":
    unittest.main()
