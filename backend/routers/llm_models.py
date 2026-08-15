from typing import Dict, Literal

from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator

from ..auth import get_current_user
from ..services.llm_model_service import (
    create_llm_model,
    delete_llm_model,
    get_llm_model,
    list_llm_models,
    update_llm_model,
)

router = APIRouter(prefix="/api/llm-models", tags=["LLM Models"])


class LlmModelPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    model_key: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9._:-]+$")
    provider: Literal["openai", "deepseek", "openai_compatible"] = "openai_compatible"
    model_name: str = Field(min_length=1, max_length=200)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str = Field(default="", max_length=1000)
    organization: str = Field(default="", max_length=200)
    extra_headers: Dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=60, ge=5, le=600)
    max_retries: int = Field(default=2, ge=0, le=10)
    enabled: bool = True
    is_default: bool = False

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("base_url 必须以 http:// 或 https:// 开头")
        return value


@router.get("list")
async def api_list_llm_models(user: Dict = Depends(get_current_user)):
    return await list_llm_models(user["user_id"])


@router.get("/{model_id}")
async def api_get_llm_model(model_id: int, user: Dict = Depends(get_current_user)):
    model = await get_llm_model(model_id, user["user_id"])
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return model


@router.post("")
async def api_create_llm_model(data: LlmModelPayload, user: Dict = Depends(get_current_user)):
    try:
        return await create_llm_model(user["user_id"], data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{model_id}")
async def api_update_llm_model(model_id: int, data: LlmModelPayload, user: Dict = Depends(get_current_user)):
    try:
        model = await update_llm_model(model_id, user["user_id"], data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return model


@router.delete("/{model_id}")
async def api_delete_llm_model(model_id: int, user: Dict = Depends(get_current_user)):
    try:
        deleted = await delete_llm_model(model_id, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return {"success": True}


@router.post("/{model_id}/test")
async def api_test_llm_model(model_id: int, user: Dict = Depends(get_current_user)):
    model = await get_llm_model(model_id, user["user_id"], include_secret=True)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    if not model["api_key"]:
        raise HTTPException(status_code=400, detail="请先配置 API Key")
    try:
        client = AsyncOpenAI(
            api_key=model["api_key"],
            base_url=model["base_url"],
            organization=model.get("organization") or None,
            default_headers=model.get("extra_headers") or None,
            timeout=model["timeout_seconds"],
            max_retries=model["max_retries"],
        )
        response = await client.chat.completions.create(
            model=model["model_name"],
            messages=[{"role": "user", "content": "只回复 OK"}],
            max_tokens=8,
            temperature=0,
        )
        content = response.choices[0].message.content if response.choices else ""
        return {"success": True, "model": model["model_name"], "response": content or ""}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"模型连接测试失败：{exc}")
