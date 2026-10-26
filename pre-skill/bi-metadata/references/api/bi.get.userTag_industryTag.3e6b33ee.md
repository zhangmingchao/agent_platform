# bi.get.userTag_industryTag.3e6b33ee

获取行业标签

- 服务：bi；后端相对路径：`/userTag/industryTag`；方法：GET。
- 前端路径：/bi-docker/api/userTag/industryTag。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:121。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:10；方法 getIndustryTag；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productRegion": {
        "type": "string",
        "description": "产品区域"
      },
      "productIds": {
        "type": "string",
        "description": "产品ID列表"
      },
      "appIds": {
        "type": "string",
        "description": "应用ID列表"
      },
      "type": {
        "type": "integer",
        "description": "统计类别.1:权重;2:数量",
        "default": 1
      }
    },
    "required": [
      "productRegion"
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
