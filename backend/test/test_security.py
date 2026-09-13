"""密码哈希与模型 API Key 加密测试。"""

import base64
import os
import unittest
from unittest.mock import patch

from backend.auth import authenticate_user
from backend.security import (
    SecretDecryptionError,
    decrypt_model_api_key,
    encrypt_model_api_key,
    hash_password,
    verify_password,
)


class PasswordSecurityTests(unittest.TestCase):
    """验证 Argon2id 密码存储和历史明文迁移判断。"""

    def test_argon2_password_round_trip(self) -> None:
        """新密码应保存为不可逆哈希并能正确验证。"""
        password_hash = hash_password("safe-password")

        self.assertTrue(password_hash.startswith("$argon2id$"))
        self.assertNotIn("safe-password", password_hash)
        result = verify_password("safe-password", password_hash)
        self.assertTrue(result.verified)
        self.assertFalse(result.requires_upgrade)

    def test_legacy_plaintext_password_requires_upgrade(self) -> None:
        """历史明文只有匹配成功时才应标记为需要升级。"""
        result = verify_password("legacy-password", "legacy-password")

        self.assertTrue(result.verified)
        self.assertTrue(result.requires_upgrade)
        self.assertFalse(verify_password("wrong", "legacy-password").verified)


class PasswordMigrationTests(unittest.IsolatedAsyncioTestCase):
    """验证登录成功后历史明文密码会被原位升级。"""

    async def test_authenticate_user_upgrades_legacy_password(self) -> None:
        """历史密码验证成功后数据库更新值必须是 Argon2id 哈希。"""
        with (
            patch(
                "backend.auth.fetch_one",
                return_value={"id": 7, "username": "legacy", "password": "old-password"},
            ),
            patch("backend.auth.execute") as execute,
        ):
            user = await authenticate_user("legacy", "old-password")

        self.assertEqual(user, {"id": 7, "username": "legacy"})
        execute.assert_awaited_once()
        stored_password = execute.await_args.args[1][0]
        self.assertTrue(stored_password.startswith("$argon2id$"))


class ModelApiKeySecurityTests(unittest.TestCase):
    """验证 AES-256-GCM 加密、解密和篡改检测。"""

    def setUp(self) -> None:
        """为每个测试生成独立的 256 位加密主密钥。"""
        self.encoded_key = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")

    def test_api_key_round_trip(self) -> None:
        """加密后的 API Key 应可解密且数据库密文不包含明文。"""
        with patch("backend.security.MODEL_API_KEY_ENCRYPTION_KEY", self.encoded_key):
            ciphertext = encrypt_model_api_key("sk-secret")
            result = decrypt_model_api_key(ciphertext)

        self.assertTrue(ciphertext.startswith("enc:v1:"))
        self.assertNotIn("sk-secret", ciphertext)
        self.assertEqual(result.plaintext, "sk-secret")
        self.assertFalse(result.requires_upgrade)

    def test_legacy_plaintext_api_key_requires_upgrade(self) -> None:
        """历史明文 API Key 应原样返回并标记为需要加密迁移。"""
        result = decrypt_model_api_key("sk-legacy")

        self.assertEqual(result.plaintext, "sk-legacy")
        self.assertTrue(result.requires_upgrade)

    def test_tampered_ciphertext_is_rejected(self) -> None:
        """AES-GCM 认证失败时不得返回任何伪造明文。"""
        with patch("backend.security.MODEL_API_KEY_ENCRYPTION_KEY", self.encoded_key):
            ciphertext = encrypt_model_api_key("sk-secret")
            tampered = ciphertext[:-2] + "AA"
            with self.assertRaises(SecretDecryptionError):
                decrypt_model_api_key(tampered)


if __name__ == "__main__":
    unittest.main()
