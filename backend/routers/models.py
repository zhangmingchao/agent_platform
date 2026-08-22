"""模型路由 — 用户级 LLM 模型管理。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..services.model_service import (
    create_model, delete_model, get_model_safe, list_models, update_model
)

router = APIRouter(prefix="/api", tags=["Models"])


class ModelCreate(BaseModel):
    name: str
    provider: str = "openai"
    model_id: str
    api_key: str
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    is_active: bool = True


class ModelUpdate(ModelCreate):
    pass


@router.get("/modelsList")
async def api_list_models(user: dict = Depends(get_current_user)):
    return await list_models(user["user_id"])


@router.get("/models/{model_id}")
async def api_get_model(model_id: int, user: dict = Depends(get_current_user)):
    model = await get_model_safe(model_id, user["user_id"])
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.post("/models")
async def api_create_model(data: ModelCreate, user: dict = Depends(get_current_user)):
    return await create_model(user["user_id"], data.dict())


@router.put("/models/{model_id}")
async def api_update_model(model_id: int, data: ModelUpdate, user: dict = Depends(get_current_user)):
    model = await update_model(model_id, user["user_id"], data.dict())
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.delete("/models/{model_id}")
async def api_delete_model(model_id: int, user: dict = Depends(get_current_user)):
    success = await delete_model(model_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="模型不存在")
    return {"success": True}
