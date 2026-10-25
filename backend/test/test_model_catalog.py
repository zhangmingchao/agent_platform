"""目录完整性、过滤、缓存、凭据保护及认证路由测试。"""
import unittest
from unittest.mock import patch

import httpx
from fastapi import FastAPI

from backend.auth import get_current_user
from backend.routers.models import router
from backend.services.model_catalog_service import ModelCatalogError, ModelCatalogService


class ModelCatalogTests(unittest.IsolatedAsyncioTestCase):
    """模拟上游，覆盖跨页搜索和失败后的缓存行为。"""

    def model(self, index: int, **changes: object) -> dict[str, object]:
        """index 为模型序号，changes 为上游字段覆盖；字典只用于模拟 JSON 边界。"""
        return {
            'model': f'qwen-{index}', 'name': f'模型{index}', 'description': '说明',
            'capabilities': ['TG'],
            'inference_metadata': {'request_modality': ['Text'], 'response_modality': ['Text']},
            **changes,
        }

    async def test_full_search_cache_refresh_and_filter(self) -> None:
        """搜索可命中第二页，过滤向量/实时/下线模型，翻页复用缓存。"""
        calls: list[int] = []
        def upstream(request: httpx.Request) -> httpx.Response:
            """request 为模拟的上游请求，验证凭据仅用于 Authorization。"""
            self.assertEqual(request.headers['authorization'], 'Bearer test-secret')
            page = int(request.url.params['page_no'])
            calls.append(page)
            records = [self.model(i) for i in range(100)] if page == 1 else [
                self.model(100), self.model(101, capabilities=['Embedding']),
                self.model(102, model='qwen-realtime'), self.model(103, inference_offline_info={'date': '2026'}),
                self.model(104, inference_metadata={'request_modality': ['Image'], 'response_modality': ['Text']}),
            ]
            return httpx.Response(200, json={'success': True, 'output': {'total': 105, 'models': records}})
        original_client = httpx.AsyncClient
        service = ModelCatalogService()
        with patch('backend.services.model_catalog_service.BAILIAN_CATALOG_API_KEY', 'test-secret'), patch(
            'backend.services.model_catalog_service.httpx.AsyncClient',
            side_effect=lambda **kwargs: original_client(transport=httpx.MockTransport(upstream), **kwargs),
        ):
            result = await service.list_models(search='QWEN-100')
            self.assertEqual(result.total, 1)
            self.assertEqual(result.items[0].model_id, 'qwen-100')
            self.assertNotIn('test-secret', result.model_dump_json())
            self.assertFalse(result.items[0].base_url.endswith('/chat/completions'))
            self.assertEqual((await service.list_models(page_no=11)).total, 101)
            self.assertEqual(calls, [1, 2])
            await service.list_models(refresh=True)
            self.assertEqual(calls, [1, 2, 1, 2])

    async def test_upstream_errors_are_safe_and_not_cached(self) -> None:
        """上游鉴权、格式和业务失败均使用安全消息，不缓存失败结果。"""
        original_client = httpx.AsyncClient
        for status, payload in [(401, {'detail': 'test-secret'}), (429, {}), (200, {'success': False}), (200, {'success': True, 'output': {}})]:
            with self.subTest(status=status, payload=payload):
                service = ModelCatalogService()
                with patch('backend.services.model_catalog_service.BAILIAN_CATALOG_API_KEY', 'test-secret'), patch(
                    'backend.services.model_catalog_service.httpx.AsyncClient',
                    side_effect=lambda **kwargs: original_client(transport=httpx.MockTransport(lambda request: httpx.Response(status, json=payload)), **kwargs),
                ):
                    with self.assertRaises(ModelCatalogError) as raised:
                        await service.list_models()
                    self.assertNotIn('test-secret', str(raised.exception))
                    self.assertEqual(service._expires_at, 0)

    async def test_network_error_and_incomplete_pagination(self) -> None:
        """网络失败及不足整页的上游响应不能被当作完整目录缓存。"""
        original_client = httpx.AsyncClient
        def timeout(request: httpx.Request) -> httpx.Response:
            """request 为模拟请求，抛出含敏感原文的网络异常以验证脱敏。"""
            raise httpx.ReadTimeout('test-secret', request=request)
        def incomplete(request: httpx.Request) -> httpx.Response:
            """request 为模拟请求，故意返回总量大于当前不完整页的响应。"""
            return httpx.Response(200, json={'success': True, 'output': {'total': 200, 'models': [self.model(1)]}})
        for handler in (timeout, incomplete):
            service = ModelCatalogService()
            with patch('backend.services.model_catalog_service.BAILIAN_CATALOG_API_KEY', 'test-secret'), patch(
                'backend.services.model_catalog_service.httpx.AsyncClient',
                side_effect=lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs),
            ):
                with self.assertRaises(ModelCatalogError) as raised:
                    await service.list_models()
                self.assertNotIn('test-secret', str(raised.exception))
                self.assertEqual(service._expires_at, 0)

    async def test_missing_credentials(self) -> None:
        """没有环境或文件凭据时，提示自定义添加，不访问上游。"""
        with patch('backend.services.model_catalog_service.BAILIAN_CATALOG_API_KEY', ''), patch(
            'backend.services.model_catalog_service.Path.read_text', side_effect=FileNotFoundError,
        ):
            with self.assertRaises(ModelCatalogError) as raised:
                await ModelCatalogService().list_models()
            self.assertEqual(raised.exception.status_code, 503)
            self.assertIn('自定义添加', raised.exception.detail)

    async def test_authenticated_static_route_and_validation(self) -> None:
        """静态目录路径不被整数 ID 路由截获，未登录和非法分页被拒绝。"""
        app = FastAPI()
        app.include_router(router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            self.assertIn((await client.get('/api/models/catalog')).status_code, (401, 403))
            app.dependency_overrides[get_current_user] = lambda: {'user_id': 1}
            self.assertEqual((await client.get('/api/models/catalog?page_no=0')).status_code, 422)
            with patch('backend.services.model_catalog_service.ModelCatalogService._read_api_key', side_effect=ModelCatalogError('未配置目录凭据', 503)):
                response = await client.get('/api/models/catalog')
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()['detail'], '未配置目录凭据')


if __name__ == '__main__':
    unittest.main()
