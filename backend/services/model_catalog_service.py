"""百炼模型目录：后端凭据、完整目录缓存、文字聊天筛选和搜索分页。"""
import asyncio
import time
from pathlib import Path

import httpx
from pydantic import ValidationError

from ..config import (
    BAILIAN_CATALOG_API_KEY, BAILIAN_CATALOG_API_KEY_FILE,
    BAILIAN_CATALOG_CACHE_SECONDS, BAILIAN_CATALOG_URL, BAILIAN_INFERENCE_BASE_URL,
)
from ..models.model_catalog import (
    BailianUpstreamResponse, CatalogModel, ModelCatalogPage,
)


class ModelCatalogError(Exception):
    """可向用户展示的目录错误；消息由本服务生成，不携带上游原文。"""

    def __init__(self, detail: str, status_code: int = 502) -> None:
        """detail 为安全提示，status_code 为平台响应状态，避免误触登录失效。"""
        super().__init__(detail)
        self.detail: str = detail
        self.status_code: int = status_code


class ModelCatalogService:
    """维护单进程目录缓存，并用锁合并并发加载。"""

    def __init__(self) -> None:
        """缓存公开模型、有效截止时间及互斥锁，不缓存 API Key。"""
        self._items: tuple[CatalogModel, ...] = ()
        self._expires_at: float = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    def _read_api_key(self) -> str:
        """优先读取环境配置，其次读取本地凭据文件；缺失时给出配置提示。"""
        key = BAILIAN_CATALOG_API_KEY.strip()
        if not key:
            try:
                key = Path(BAILIAN_CATALOG_API_KEY_FILE).read_text(encoding="utf-8").strip()
            except OSError:
                pass
        if not key:
            raise ModelCatalogError("未配置百炼目录查询凭据，请配置 BAILIAN_CATALOG_API_KEY，或使用自定义添加", 503)
        return key

    async def _fetch_all(self) -> tuple[CatalogModel, ...]:
        """以 100 条分页查询上游，完整成功后才替换缓存；失败不缓存半份数据。"""
        key = self._read_api_key()
        items: list[CatalogModel] = []
        seen: set[str] = set()
        try:
            async with asyncio.timeout(25), httpx.AsyncClient(timeout=10) as client:
                for page_no in range(1, 51):
                    response = await client.get(
                        BAILIAN_CATALOG_URL,
                        headers={"Authorization": f"Bearer {key}"},
                        params={"page_no": page_no, "page_size": 100},
                    )
                    if response.status_code in (401, 403):
                        raise ModelCatalogError("百炼目录查询凭据无效或无权限，请检查后端配置", 503)
                    if response.status_code == 429:
                        raise ModelCatalogError("百炼目录请求过于频繁，请稍后重试", 503)
                    response.raise_for_status()
                    data = BailianUpstreamResponse.model_validate(response.json())
                    if not data.success or data.output is None:
                        raise ModelCatalogError("百炼目录查询失败，请稍后重试")
                    for model in data.output.models:
                        if model.supports_text_chat() and model.model not in seen:
                            seen.add(model.model)
                            items.append(CatalogModel(
                                model_id=model.model, name=model.name or model.model,
                                description=model.description, base_url=BAILIAN_INFERENCE_BASE_URL,
                                features=model.features, context_window=model.model_info.context_window,
                                max_output_tokens=model.model_info.max_output_tokens,
                            ))
                    if page_no * 100 >= data.output.total:
                        return tuple(items)
                    if len(data.output.models) != 100:
                        raise ModelCatalogError("百炼目录分页不完整，请稍后重试")
        except (httpx.HTTPError, TimeoutError):
            raise ModelCatalogError("无法连接百炼模型目录，请检查网络并重试") from None
        except (ValidationError, ValueError):
            raise ModelCatalogError("百炼模型目录格式异常，请稍后重试") from None
        raise ModelCatalogError("百炼目录超出分页限制，请稍后重试")

    async def list_models(
        self, page_no: int = 1, page_size: int = 10, search: str = "", refresh: bool = False,
    ) -> ModelCatalogPage:
        """返回实体分页；page_no 页码，page_size 页长，search 全目录关键词，refresh 强制更新。"""
        requested_at = time.monotonic()
        async with self._lock:
            # 等待锁期间若另一请求已刷新，则复用结果，避免连续重复查询。
            refreshed_since_request = self._expires_at - BAILIAN_CATALOG_CACHE_SECONDS >= requested_at
            if time.monotonic() >= self._expires_at or (refresh and not refreshed_since_request):
                items = await self._fetch_all()
                self._items = items
                self._expires_at = time.monotonic() + BAILIAN_CATALOG_CACHE_SECONDS
        keyword = search.strip().casefold()
        matching = [item for item in self._items if keyword in f"{item.name} {item.model_id}".casefold()]
        start = (page_no - 1) * page_size
        return ModelCatalogPage(items=matching[start:start + page_size], total=len(matching), page_no=page_no, page_size=page_size)


# 路由复用服务实例，让搜索和分页共享缓存。
model_catalog_service = ModelCatalogService()
