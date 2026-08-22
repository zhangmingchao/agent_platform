"""模型管理服务 — 用户级 LLM 模型配置。"""
import logging
from datetime import datetime
from typing import List, Dict, Optional

from ..database import execute, fetch_all, fetch_one

log = logging.getLogger("agent-platform")


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_models(user_id: int) -> List[Dict]:
    """列出用户的所有模型。"""
    return await fetch_all(
        "SELECT id, name, provider, model_id, base_url, temperature, max_tokens, is_active, "
        "created_at, updated_at FROM models WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,)
    )


async def get_model(model_id: int, user_id: int) -> Optional[Dict]:
    """根据 ID 获取单个模型，包含供 Agent 工厂使用的 api_key。"""
    return await fetch_one(
        "SELECT * FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )


async def get_model_safe(model_id: int, user_id: int) -> Optional[Dict]:
    """获取不包含 api_key 的模型信息（用于 API 响应）。"""
    return await fetch_one(
        "SELECT id, name, provider, model_id, base_url, temperature, max_tokens, is_active, "
        "created_at, updated_at FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )


async def create_model(user_id: int, data: Dict) -> Dict:
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
            data.get("api_key", ""),
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


async def update_model(model_id: int, user_id: int, data: Dict) -> Optional[Dict]:
    """更新现有模型。"""
    existing = await fetch_one(
        "SELECT id FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )
    if not existing:
        return None

    now = _now()
    await execute(
        "UPDATE models SET name=%s, provider=%s, model_id=%s, api_key=%s, base_url=%s, "
        "temperature=%s, max_tokens=%s, is_active=%s, updated_at=%s WHERE id=%s",
        (
            data.get("name", ""),
            data.get("provider", "openai"),
            data.get("model_id", ""),
            data.get("api_key", ""),
            data.get("base_url", ""),
            data.get("temperature", 0.7),
            data.get("max_tokens", 4096),
            1 if data.get("is_active", True) else 0,
            now,
            model_id,
        )
    )
    return await get_model_safe(model_id, user_id)


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
