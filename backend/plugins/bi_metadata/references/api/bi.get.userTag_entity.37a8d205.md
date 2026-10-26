# bi.get.userTag_entity.37a8d205

#region 创建相关 标签主体

- 服务：bi；后端相对路径：`/userTag/entity`；方法：GET。
- 前端路径：/bi-docker/api/userTag/entity。
- 状态：matched；操作：write；Schema：declared。
- 说明：源码未明确证明只读，使用修改入口；需核实业务意图
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:152。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:47；方法 fetchTagEntityList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKeys": {
        "type": "string"
      },
      "category": {
        "type": "integer",
        "default": 1
      }
    },
    "required": [
      "productKeys"
    ],
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
