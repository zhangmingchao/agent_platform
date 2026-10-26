# bi.get.base_getCurrencyTypeList.067d58df

币种列表

- 服务：bi；后端相对路径：`/base/getCurrencyTypeList`；方法：GET。
- 前端路径：/bi-docker/api/base/getCurrencyTypeList。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/BaseController.java:40。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:76；方法 getCurrencyTypeList；参数类型 `none`。

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
  "backend_type": "ResultModel<Object>",
  "backend_schema": {
    "x-source-type": "ResultModel<Object>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
