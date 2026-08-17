"""Model management service — user-level LLM model configurations."""
import logging
from datetime import datetime
from typing import List, Dict, Optional

from ..database import execute, fetch_all, fetch_one

log = logging.getLogger("agent-platform")


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_models(user_id: int) -> List[Dict]:
    """List all models for a user."""
    return await fetch_all(
        "SELECT id, name, provider, model_id, base_url, temperature, max_tokens, is_active, "
        "created_at, updated_at FROM models WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,)
    )


async def get_model(model_id: int, user_id: int) -> Optional[Dict]:
    """Get a single model by ID, including api_key for agent factory."""
    return await fetch_one(
        "SELECT * FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )


async def get_model_safe(model_id: int, user_id: int) -> Optional[Dict]:
    """Get model without api_key (for API responses)."""
    return await fetch_one(
        "SELECT id, name, provider, model_id, base_url, temperature, max_tokens, is_active, "
        "created_at, updated_at FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )


async def create_model(user_id: int, data: Dict) -> Dict:
    """Create a new model configuration."""
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
    """Update an existing model."""
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
    """Delete a model. Also clear model_config_id from agents referencing it."""
    # Clear references in agents
    await execute(
        "UPDATE agents SET model_config_id=NULL WHERE model_config_id=%s AND user_id=%s",
        (model_id, user_id)
    )
    result = await execute(
        "DELETE FROM models WHERE id=%s AND user_id=%s",
        (model_id, user_id)
    )
    return result > 0
