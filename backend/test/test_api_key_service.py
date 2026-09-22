"""用户 API Key 服务测试。"""

import hashlib
import unittest
from unittest.mock import AsyncMock, patch

from backend.services.api_key_service import (
    authenticate_api_key,
    get_api_key_status,
    issue_api_key,
    revoke_api_key,
)


class ApiKeyServiceTests(unittest.IsolatedAsyncioTestCase):
    """验证 API Key 只保存哈希，并能映射回所属用户。"""

    async def test_issue_api_key_does_not_store_plaintext(self) -> None:
        """签发结果包含一次性明文，数据库参数中只能出现哈希。"""
        execute = AsyncMock(return_value=1)
        with (
            patch("backend.services.api_key_service.secrets.token_hex", return_value="0123456789abcdef"),
            patch("backend.services.api_key_service.secrets.token_urlsafe", return_value="secret-value"),
            patch("backend.services.api_key_service.fetch_one", AsyncMock(return_value=None)),
            patch("backend.services.api_key_service.execute", execute),
        ):
            issued = await issue_api_key(7)

        self.assertEqual(issued.api_key, "ap_live_0123456789abcdef.secret-value")
        stored_parameters = execute.await_args.args[1]
        self.assertNotIn(issued.api_key, stored_parameters)
        self.assertNotIn("secret-value", stored_parameters)
        self.assertIn(hashlib.sha256(issued.api_key.encode("utf-8")).hexdigest(), stored_parameters)

    async def test_authenticate_api_key_returns_user_entity(self) -> None:
        """有效密钥应返回包含用户和公开密钥 ID 的认证实体。"""
        api_key = "ap_live_0123456789abcdef.secret-value"
        key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        execute = AsyncMock(return_value=0)
        with (
            patch(
                "backend.services.api_key_service.fetch_one",
                AsyncMock(return_value={"user_id": 7, "username": "api-user", "key_hash": key_hash}),
            ),
            patch("backend.services.api_key_service.execute", execute),
        ):
            user = await authenticate_api_key(api_key)

        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, 7)
        self.assertEqual(user.api_key_id, "0123456789abcdef")
        execute.assert_awaited_once()

    async def test_invalid_api_key_is_rejected_without_database_lookup(self) -> None:
        """格式错误的密钥不应触发数据库查询。"""
        fetch_one = AsyncMock()
        with patch("backend.services.api_key_service.fetch_one", fetch_one):
            user = await authenticate_api_key("invalid")

        self.assertIsNone(user)
        fetch_one.assert_not_awaited()

    async def test_status_and_revoke_use_safe_entities(self) -> None:
        """状态查询不返回哈希，吊销有效密钥时返回实体结果。"""
        with patch(
            "backend.services.api_key_service.fetch_one",
            AsyncMock(return_value={
                "key_prefix": "ap_live_0123456789abcdef",
                "status": "active",
                "created_at": None,
                "last_used_at": None,
            }),
        ):
            status = await get_api_key_status(7)
        self.assertTrue(status.configured)
        self.assertFalse(hasattr(status, "key_hash"))

        with (
            patch(
                "backend.services.api_key_service.fetch_one",
                AsyncMock(return_value={"id": 1}),
            ),
            patch("backend.services.api_key_service.execute", AsyncMock(return_value=0)),
        ):
            result = await revoke_api_key(7)
        self.assertTrue(result.revoked)


if __name__ == "__main__":
    unittest.main()
