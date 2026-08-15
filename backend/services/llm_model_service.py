"""User-scoped LLM model configurations for OpenAI-compatible providers."""
import base64
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken

from ..config import JWT_SECRET
from ..database import execute, fetch_all, fetch_one


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _cipher() -> Fernet:
    digest = hashlib.sha256(JWT_SECRET.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_api_key(value: str) -> str:
    return _cipher().encrypt(value.encode("utf-8")).decode("ascii") if value else ""


def decrypt_api_key(value: str) -> str:
    if not value:
        return ""
    try:
        return _cipher().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        raise ValueError("模型 API Key 无法解密，请重新编辑并保存")


def _mask_api_key(encrypted: str) -> str:
    if not encrypted:
        return ""
    try:
        plain = decrypt_api_key(encrypted)
    except ValueError:
        return "******"
    if len(plain) <= 8:
        return "******"
    return f"{plain[:3]}******{plain[-4:]}"


def _public_model(row: Dict) -> Dict:
    result = dict(row)
    encrypted = result.pop("api_key_encrypted", "") or ""
    result["api_key_masked"] = _mask_api_key(encrypted)
    result["has_api_key"] = bool(encrypted)
    try:
        result["extra_headers"] = json.loads(result.pop("extra_headers_json", "{}") or "{}")
    except json.JSONDecodeError:
        result["extra_headers"] = {}
    return result


async def list_llm_models(user_id: int, enabled_only: bool = False) -> List[Dict]:
    where = " AND enabled=1" if enabled_only else ""
    rows = await fetch_all(
        "SELECT * FROM llm_models WHERE user_id=%s" + where + " ORDER BY is_default DESC, updated_at DESC",
        (user_id,),
    )
    return [_public_model(row) for row in rows]


async def get_llm_model(model_id: int, user_id: int, include_secret: bool = False) -> Optional[Dict]:
    row = await fetch_one("SELECT * FROM llm_models WHERE id=%s AND user_id=%s", (model_id, user_id))
    if not row:
        return None
    if include_secret:
        result = dict(row)
        result["api_key"] = decrypt_api_key(result.pop("api_key_encrypted", "") or "")
        try:
            result["extra_headers"] = json.loads(result.pop("extra_headers_json", "{}") or "{}")
        except json.JSONDecodeError:
            result["extra_headers"] = {}
        return result
    return _public_model(row)


async def get_llm_model_by_key(model_key: str, user_id: int) -> Optional[Dict]:
    row = await fetch_one(
        "SELECT * FROM llm_models WHERE model_key=%s AND user_id=%s AND enabled=1",
        (model_key, user_id),
    )
    if not row:
        return None
    result = dict(row)
    result["api_key"] = decrypt_api_key(result.pop("api_key_encrypted", "") or "")
    try:
        result["extra_headers"] = json.loads(result.pop("extra_headers_json", "{}") or "{}")
    except json.JSONDecodeError:
        result["extra_headers"] = {}
    return result


async def _clear_default(user_id: int) -> None:
    await execute("UPDATE llm_models SET is_default=0 WHERE user_id=%s", (user_id,))


def _values(data: Dict, encrypted_key: str) -> tuple:
    return (
        data["name"].strip(),
        data["model_key"].strip(),
        data["provider"],
        data["model_name"].strip(),
        data["base_url"].strip().rstrip("/"),
        encrypted_key,
        data.get("organization", "").strip(),
        json.dumps(data.get("extra_headers", {}), ensure_ascii=False),
        data.get("timeout_seconds", 60),
        data.get("max_retries", 2),
        bool(data.get("enabled", True)),
        bool(data.get("is_default", False)),
    )


async def create_llm_model(user_id: int, data: Dict) -> Dict:
    if await fetch_one("SELECT id FROM llm_models WHERE user_id=%s AND model_key=%s", (user_id, data["model_key"])):
        raise ValueError("模型标识 model_key 已存在")
    if data.get("is_default"):
        await _clear_default(user_id)
    now = _now()
    model_id = await execute(
        "INSERT INTO llm_models (user_id, name, model_key, provider, model_name, base_url, "
        "api_key_encrypted, organization, extra_headers_json, timeout_seconds, max_retries, "
        "enabled, is_default, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, "
        "%s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, *_values(data, encrypt_api_key(data.get("api_key", ""))), now, now),
    )
    return await get_llm_model(model_id, user_id)


async def update_llm_model(model_id: int, user_id: int, data: Dict) -> Optional[Dict]:
    existing = await fetch_one("SELECT * FROM llm_models WHERE id=%s AND user_id=%s", (model_id, user_id))
    if not existing:
        return None
    duplicate = await fetch_one(
        "SELECT id FROM llm_models WHERE user_id=%s AND model_key=%s AND id<>%s",
        (user_id, data["model_key"], model_id),
    )
    if duplicate:
        raise ValueError("模型标识 model_key 已存在")
    if data.get("is_default"):
        await _clear_default(user_id)
    api_key = data.get("api_key", "")
    encrypted = encrypt_api_key(api_key) if api_key else existing["api_key_encrypted"]
    await execute(
        "UPDATE llm_models SET name=%s, model_key=%s, provider=%s, model_name=%s, base_url=%s, "
        "api_key_encrypted=%s, organization=%s, extra_headers_json=%s, timeout_seconds=%s, "
        "max_retries=%s, enabled=%s, is_default=%s, updated_at=%s WHERE id=%s AND user_id=%s",
        (*_values(data, encrypted), _now(), model_id, user_id),
    )
    return await get_llm_model(model_id, user_id)


async def delete_llm_model(model_id: int, user_id: int) -> bool:
    model = await fetch_one("SELECT model_key FROM llm_models WHERE id=%s AND user_id=%s", (model_id, user_id))
    if not model:
        return False
    agent = await fetch_one(
        "SELECT name FROM agents WHERE user_id=%s AND model=%s LIMIT 1",
        (user_id, model["model_key"]),
    )
    if agent:
        raise ValueError(f"模型正在被 Agent“{agent['name']}”使用，请先修改 Agent")
    await execute("DELETE FROM llm_models WHERE id=%s AND user_id=%s", (model_id, user_id))
    return True
