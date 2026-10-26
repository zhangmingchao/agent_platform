# rule.get.portal_params_selectValueList.da4bf25a

GetSelectParamValueList 获取参数值下拉列表

- 服务：rule；后端相对路径：`/portal/params/selectValueList`；方法：GET。
- 前端路径：/portal/rule/params/selectValueList。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:216。
- 后端源码：rule/router/param_info.go:207。
- 前端源码：solar-engine-fe/src/api/modules/rule/index.ts:67；方法 selectValueList；参数类型 `SelectValueList`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "paramId": {
        "type": "number"
      }
    },
    "required": [
      "paramId"
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
  "backend_type": "e.Response {code,msg,data,trace,timeZone}",
  "backend_schema": {
    "type": "object",
    "properties": {
      "code": {
        "type": "integer"
      },
      "msg": {
        "type": "string"
      },
      "data": {},
      "trace": {
        "type": "string"
      },
      "timeZone": {
        "type": "string"
      }
    }
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
