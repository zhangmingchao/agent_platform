"""认证凭据与模型密钥的安全处理工具。"""

import base64
import binascii
import hmac
import os
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from .config import MODEL_API_KEY_ENCRYPTION_KEY


_PASSWORD_HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
_ARGON2_PREFIX = "$argon2"
_API_KEY_PREFIX = "enc:v1:"
_API_KEY_ASSOCIATED_DATA = b"agent-platform:model-api-key:v1"


class SecurityConfigurationError(RuntimeError):
    """表示安全功能缺少必要配置或配置格式不正确。"""


class SecretDecryptionError(ValueError):
    """表示密文已损坏、密钥错误或密文格式不合法。"""


@dataclass(frozen=True)
class PasswordVerificationResult:
    """密码校验结果。

    Attributes:
        verified: 用户输入的密码是否正确。
        requires_upgrade: 数据库中的旧密码是否需要升级为 Argon2 哈希。
    """

    verified: bool
    requires_upgrade: bool


@dataclass(frozen=True)
class ApiKeyDecryptionResult:
    """模型 API Key 解密结果。

    Attributes:
        plaintext: 供模型客户端临时使用的 API Key 明文。
        requires_upgrade: 数据库存储值是否为需要原位加密的历史明文。
    """

    plaintext: str
    requires_upgrade: bool


def hash_password(password: str) -> str:
    """使用 Argon2id 生成不可逆密码哈希。

    Args:
        password: 用户提交的密码明文，只在当前调用期间存在于内存中。

    Returns:
        包含算法参数和随机盐值的 Argon2id 哈希字符串。
    """
    if not isinstance(password, str) or not password:
        raise ValueError("密码不能为空")
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, stored_password: str) -> PasswordVerificationResult:
    """校验密码，并识别需要迁移的历史明文密码。

    Args:
        password: 用户本次提交的密码明文。
        stored_password: 数据库保存的 Argon2 哈希或历史明文密码。

    Returns:
        包含校验状态和是否需要升级标记的实体。
    """
    if not password or not stored_password:
        return PasswordVerificationResult(verified=False, requires_upgrade=False)
    if not stored_password.startswith(_ARGON2_PREFIX):
        verified = hmac.compare_digest(password, stored_password)
        return PasswordVerificationResult(verified=verified, requires_upgrade=verified)
    try:
        verified = _PASSWORD_HASHER.verify(stored_password, password)
        return PasswordVerificationResult(
            verified=verified,
            requires_upgrade=verified and _PASSWORD_HASHER.check_needs_rehash(stored_password),
        )
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return PasswordVerificationResult(verified=False, requires_upgrade=False)


def _decode_encryption_key() -> bytes:
    """读取并校验 Base64 编码的 256 位模型密钥加密主密钥。"""
    encoded_key = MODEL_API_KEY_ENCRYPTION_KEY.strip()
    if not encoded_key:
        raise SecurityConfigurationError(
            "未配置 MODEL_API_KEY_ENCRYPTION_KEY，无法安全保存或读取模型 API Key"
        )
    try:
        padding = "=" * (-len(encoded_key) % 4)
        key = base64.urlsafe_b64decode(encoded_key + padding)
    except (ValueError, TypeError, binascii.Error) as exc:
        raise SecurityConfigurationError("MODEL_API_KEY_ENCRYPTION_KEY 不是有效的 Base64") from exc
    if len(key) != 32:
        raise SecurityConfigurationError("MODEL_API_KEY_ENCRYPTION_KEY 解码后必须为 32 字节")
    return key


def encrypt_model_api_key(api_key: str) -> str:
    """使用 AES-256-GCM 加密模型 API Key。

    Args:
        api_key: 待保存的模型 API Key 明文。

    Returns:
        带版本前缀、随机 Nonce 和认证标签的 Base64 密文。
    """
    if not api_key:
        return ""
    nonce = os.urandom(12)
    ciphertext = AESGCM(_decode_encryption_key()).encrypt(
        nonce,
        api_key.encode("utf-8"),
        _API_KEY_ASSOCIATED_DATA,
    )
    payload = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return f"{_API_KEY_PREFIX}{payload}"


def decrypt_model_api_key(stored_api_key: str) -> ApiKeyDecryptionResult:
    """解密模型 API Key，并兼容需要迁移的历史明文。

    Args:
        stored_api_key: 数据库保存的版本化密文或历史明文 API Key。

    Returns:
        包含 API Key 明文和是否需要升级标记的实体。
    """
    if not stored_api_key:
        return ApiKeyDecryptionResult(plaintext="", requires_upgrade=False)
    if not stored_api_key.startswith(_API_KEY_PREFIX):
        return ApiKeyDecryptionResult(plaintext=stored_api_key, requires_upgrade=True)
    try:
        payload = base64.urlsafe_b64decode(stored_api_key[len(_API_KEY_PREFIX):])
        if len(payload) < 29:
            raise ValueError("密文长度不足")
        plaintext = AESGCM(_decode_encryption_key()).decrypt(
            payload[:12],
            payload[12:],
            _API_KEY_ASSOCIATED_DATA,
        )
        return ApiKeyDecryptionResult(
            plaintext=plaintext.decode("utf-8"),
            requires_upgrade=False,
        )
    except SecurityConfigurationError:
        raise
    except (InvalidTag, ValueError, UnicodeDecodeError, binascii.Error) as exc:
        raise SecretDecryptionError("模型 API Key 解密失败，请检查加密密钥配置") from exc
