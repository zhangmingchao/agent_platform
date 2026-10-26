# bi.get.buriedData_findRuleEventApp.c61f833f

数据埋点 - 已创建该规则事件的应用列表

- 服务：bi；后端相对路径：`/buriedData/findRuleEventApp`；方法：GET。
- 前端路径：/bi-docker/api/buriedData/findRuleEventApp。
- 状态：frontend_only；操作：unverified；Schema：declared。
- 说明：前端有调用，本地后端无同方法/同路径声明；不可假定部署版本支持
- 前端源码：solar-engine-fe/src/api/modules/app/index.ts:86；方法 ruleEventAppList；参数类型 `any`。

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
