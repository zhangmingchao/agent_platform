# rule.get.portal_params_abRefList.79050d88

GetExperimentByParamId 根据参数ID获取实验

- 服务：rule；后端相对路径：`/portal/params/abRefList`；方法：GET。
- 前端路径：/portal/rule/params/abRefList。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:209。
- 后端源码：rule/router/param_info.go:52。
- 前端源码：solar-engine-fe/src/api/modules/rule/index.ts:19；方法 getAbRefList；参数类型 `RefList`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "paramId": {
        "anyOf": [
          {
            "type": "number"
          },
          {
            "type": "string",
            "const": ""
          }
        ],
        "description": "参数Id"
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
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "number",
            "description": "试验 / 规则 主键Id"
          },
          "name": {
            "type": "string",
            "description": "试验 / 规则 名称"
          },
          "valueId": {
            "type": "number",
            "description": "参数值主键Id"
          },
          "value": {
            "type": "string",
            "description": "参数值"
          },
          "statusText": {
            "type": "string",
            "description": "状态名称"
          },
          "abGroup": {
            "type": "number",
            "description": "试验分组主键Id"
          },
          "abGroupName": {
            "type": "string",
            "description": "试验分组名称"
          },
          "status": {
            "anyOf": [
              {
                "type": "number",
                "const": 1
              },
              {
                "type": "number",
                "const": 2
              },
              {
                "type": "number",
                "const": 3
              },
              {
                "type": "number",
                "const": 4
              },
              {
                "type": "number",
                "const": 5
              },
              {
                "type": "number",
                "const": 6
              },
              {
                "type": "number",
                "const": -1
              }
            ],
            "description": "状态类型"
          }
        },
        "required": [
          "id",
          "name",
          "valueId",
          "value",
          "statusText",
          "abGroup",
          "abGroupName",
          "status"
        ]
      }
    }
  ]
}
```
