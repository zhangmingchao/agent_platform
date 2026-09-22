"""模型路由 — 用户级 LLM 模型管理。"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from ..auth import get_current_user
from ..config import HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS, MODEL_TEST_RATE_LIMIT
from ..llm_adapters.registry import list_llm_adapters
from ..rate_limit import RateLimitRule, enforce_rate_limit
from ..models.token_quota import ModelTokenQuotaExceededError, TokenQuotaMode
from ..services.model_service import (
    create_model, delete_model, get_model_safe, list_models, test_model_connection, update_model
)

router = APIRouter(prefix="/api", tags=["Models"])
MODEL_TEST_RULE = RateLimitRule(
    name="model-test-user",
    limit=MODEL_TEST_RATE_LIMIT,
    window_seconds=HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS,
)


class ModelCreate(BaseModel):
    """创建模型配置的请求参数。"""

    name: str
    provider: str = "openai"
    model_id: str
    api_key: str = Field(min_length=1, max_length=500)
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    quota_mode: TokenQuotaMode = TokenQuotaMode.UNLIMITED
    daily_token_limit: Optional[int] = Field(default=None, gt=0, le=10_000_000_000)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_token_quota(self) -> "ModelCreate":
        """每日模式必须提供限额；不限额模式统一清空限额值。"""
        if self.quota_mode is TokenQuotaMode.DAILY and self.daily_token_limit is None:
            raise ValueError("每日限额模式必须填写 daily_token_limit")
        if self.quota_mode is TokenQuotaMode.UNLIMITED:
            self.daily_token_limit = None
        return self


class ModelUpdate(ModelCreate):
    """模型更新参数；API Key 留空时保留数据库中的原密文。"""

    api_key: str = Field(default="", max_length=500)


@router.get("/modelsList")
async def api_list_models(user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    return await list_models(user["user_id"])


@router.get("/models/adapters")
async def api_list_model_adapters(user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """列出当前后端注册的 LLM Adapter。"""
    return [item.to_dict() for item in list_llm_adapters()]


@router.get("/models/{model_id}")
async def api_get_model(model_id: int, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    model = await get_model_safe(model_id, user["user_id"])
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.post("/models")
async def api_create_model(data: ModelCreate, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return await create_model(user["user_id"], data.dict())


@router.put("/models/{model_id}")
async def api_update_model(model_id: int, data: ModelUpdate, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    model = await update_model(model_id, user["user_id"], data.dict())
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.delete("/models/{model_id}")
async def api_delete_model(model_id: int, user: dict = Depends(get_current_user)) -> Dict[str, bool]:
    success = await delete_model(model_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="模型不存在")
    return {"success": True}


@router.post("/models/{model_id}/test")
async def api_test_model(model_id: int, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """测试已保存的模型连接是否可用。"""
    await enforce_rate_limit(MODEL_TEST_RULE, str(user["user_id"]))
    try:
        result = await test_model_connection(model_id=model_id, user_id=user["user_id"])
    except ModelTokenQuotaExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    return result


@router.post("/models/test")
async def api_test_model_config(data: ModelCreate, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """测试未保存的模型配置是否可用（编辑/创建时实时校验）。"""
    await enforce_rate_limit(MODEL_TEST_RULE, str(user["user_id"]))
    result = await test_model_connection(config=data.dict())
    return result
