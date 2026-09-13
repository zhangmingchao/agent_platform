"""模型 API Key 密文保存与历史数据迁移测试。"""

import base64
import os
import unittest
from unittest.mock import AsyncMock, patch

from backend.services.model_service import get_model


class ModelSecretMigrationTests(unittest.IsolatedAsyncioTestCase):
    """验证模型读取链路不会继续保留历史明文。"""

    async def test_get_model_encrypts_legacy_api_key(self) -> None:
        """读取历史明文后应向调用方返回明文，并把数据库更新为密文。"""
        encoded_key = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")
        model_row = {"id": 3, "user_id": 9, "api_key": "sk-legacy"}
        execute = AsyncMock()

        with (
            patch("backend.services.model_service.fetch_one", AsyncMock(return_value=model_row)),
            patch("backend.services.model_service.execute", execute),
            patch("backend.security.MODEL_API_KEY_ENCRYPTION_KEY", encoded_key),
        ):
            model = await get_model(3, 9)

        self.assertIsNotNone(model)
        self.assertEqual(model["api_key"], "sk-legacy")
        encrypted_value = execute.await_args.args[1][0]
        self.assertTrue(encrypted_value.startswith("enc:v1:"))
        self.assertNotIn("sk-legacy", encrypted_value)


if __name__ == "__main__":
    unittest.main()
