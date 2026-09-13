"""模型管理服务 — 用户级 LLM 模型配置。"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database import execute, fetch_all, fetch_one
from ..security import decrypt_model_api_key, encrypt_model_api_key

log = logging.getLogger(__name__)


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_models(user_id: int) -> List[Dict[str, Any]]:
    """列出用户的所有模型。"""
    return await fetch_all(
        "SELECT id, name, provider, model_id, base_url, temperature, max_tokens, is_active, "
        "created_at, updated_at FROM models WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,)
    )


async def get_model(model_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """获取模型配置，在内存中解密 API Key 并迁移历史明文。

    Args:
        model_id: 需要读取的模型配置 ID。
        user_id: 模型配置所属的用户 ID，用于资源隔离。

    Returns:
        包含临时 API Key 明文的模型配置；配置不存在时返回 ``None``。
    """
    model = await fetch_one(
        "SELECT * FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )
    if not model:
        return None
    decryption = decrypt_model_api_key(str(model.get("api_key") or ""))
    model["api_key"] = decryption.plaintext
    if decryption.requires_upgrade:
        encrypted_api_key = encrypt_model_api_key(decryption.plaintext)
        await execute(
            "UPDATE models SET api_key=%s WHERE id=%s AND user_id=%s",
            (encrypted_api_key, model_id, user_id),
        )
        log.info("[Model] encrypted legacy api_key for model_id=%s user_id=%s", model_id, user_id)
    return model


async def get_model_safe(model_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """获取不包含 api_key 的模型信息（用于 API 响应）。"""
    return await fetch_one(
        "SELECT id, name, provider, model_id, base_url, temperature, max_tokens, is_active, "
        "created_at, updated_at FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )


async def create_model(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """创建新的模型配置。"""
    now = _now()
    model_id = await execute(
        "INSERT INTO models (user_id, name, provider, model_id, api_key, base_url, "
        "temperature, max_tokens, is_active, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            user_id,
            data.get("name", ""),
            data.get("provider", "openai"),
            data.get("model_id", ""),
            encrypt_model_api_key(str(data.get("api_key") or "")),
            data.get("base_url", ""),
            data.get("temperature", 0.7),
            data.get("max_tokens", 4096),
            1 if data.get("is_active", True) else 0,
            now,
            now,
        )
    )
    log.info("[Model] created id=%s for user=%s", model_id, user_id)
    return await get_model_safe(model_id, user_id)


async def update_model(
    model_id: int,
    user_id: int,
    data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """更新现有模型。"""
    existing = await fetch_one(
        "SELECT id, api_key FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )
    if not existing:
        return None

    now = _now()
    submitted_api_key = str(data.get("api_key") or "")
    # API 不回传已保存的 Key，因此编辑页面提交空值时保留原密文。
    encrypted_api_key = (
        encrypt_model_api_key(submitted_api_key)
        if submitted_api_key
        else str(existing.get("api_key") or "")
    )
    await execute(
        "UPDATE models SET name=%s, provider=%s, model_id=%s, api_key=%s, base_url=%s, "
        "temperature=%s, max_tokens=%s, is_active=%s, updated_at=%s WHERE id=%s",
        (
            data.get("name", ""),
            data.get("provider", "openai"),
            data.get("model_id", ""),
            encrypted_api_key,
            data.get("base_url", ""),
            data.get("temperature", 0.7),
            data.get("max_tokens", 4096),
            1 if data.get("is_active", True) else 0,
            now,
            model_id,
        )
    )
    return await get_model_safe(model_id, user_id)


async def test_model_connection(
    model_id: Optional[int] = None,
    user_id: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """测试模型连接是否可用。支持已保存模型的 ID 或直接传入配置。"""
    from langchain_openai import ChatOpenAI

    if model_id and user_id:
        model = await get_model(model_id, user_id)
        if not model:
            return {"success": False, "detail": "模型不存在"}
    elif config:
        model = config
    else:
        return {"success": False, "detail": "缺少模型配置"}

    api_key = (model.get("api_key") or "").strip()
    model_name = (model.get("model_id") or "").strip()
    base_url = (model.get("base_url") or "").strip()

    if not api_key:
        return {"success": False, "detail": "API Key 为空"}
    if not model_name:
        return {"success": False, "detail": "模型 ID 为空"}

    try:
        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url if base_url else None,
            temperature=0,
            max_tokens=10,
            timeout=15,
            max_retries=0,
        )
        resp = await llm.ainvoke("你好")
        content = resp.content if hasattr(resp, "content") else str(resp)
        preview = str(content)[:100] if content else ""
        return {
            "success": True,
            "detail": "连接成功",
            "model": model_name,
            "response": preview,
        }
    except Exception as exc:
        msg = str(exc)
        if "401" in msg or "Authentication" in msg or "api key" in msg.lower():
            detail = "API Key 无效或已过期"
        elif "connection" in msg.lower() or "timeout" in msg.lower() or "refused" in msg.lower():
            detail = f"无法连接到 API 地址: {base_url or '未设置'}"
        elif "model" in msg.lower() and ("not" in msg.lower() or "does not" in msg.lower()):
            detail = f"模型 ID 不存在: {model_name}"
        else:
            detail = msg[:200]
        return {"success": False, "detail": detail}


async def delete_model(model_id: int, user_id: int) -> bool:
    """删除模型。同时清除引用该模型的 Agent 中的 model_config_id。"""
    # 清除 Agent 中的引用
    await execute(
        "UPDATE agents SET model_config_id=NULL WHERE model_config_id=%s AND user_id=%s",
        (model_id, user_id)
    )
    result = await execute(
        "DELETE FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )
    return result > 0
