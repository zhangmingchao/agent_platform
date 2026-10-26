# bi.post.buriedData_errorDataTenSummary.b37ba5d4

错误数据

- 服务：bi；后端相对路径：`/buriedData/errorDataTenSummary`；方法：POST。
- 前端路径：/bi-docker/api/buriedData/errorDataTenSummary。
- 状态：frontend_only；操作：unverified；Schema：declared。
- 说明：前端有调用，本地后端无同方法/同路径声明；不可假定部署版本支持
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:207；方法 getErrorDataTenSummary；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  },
  "body_schema": null,
  "path_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

返回声明：

```json
{
  "backend_type": "未匹配",
  "backend_schema": null,
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
