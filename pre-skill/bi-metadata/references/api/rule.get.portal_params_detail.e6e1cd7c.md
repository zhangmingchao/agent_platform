# rule.get.portal_params_detail.e6e1cd7c

GetParamDetail 获取参数详情

- 服务：rule；后端相对路径：`/portal/params/detail`；方法：GET。
- 前端路径：/portal/rule/params/detail。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:212。
- 后端源码：rule/router/param_info.go:103。
- 前端源码：solar-engine-fe/src/api/modules/rule/index.ts:37；方法 detail；参数类型 `Detail`。

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
      "type": "object",
      "properties": {
        "id": {
          "type": "number"
        },
        "name": {
          "type": "string",
          "description": "参数名称"
        },
        "type": {
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
            }
          ],
          "description": "参数类型"
        },
        "typeText": {
          "type": "string",
          "description": "参数类型名称"
        },
        "valueCount": {
          "type": "number",
          "description": "参数数值"
        },
        "valueList": {
          "type": "array",
          "items": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "number"
              },
              {
                "type": "boolean",
                "const": false
              },
              {
                "type": "boolean",
                "const": true
              }
            ]
          },
          "description": "参数值list集合"
        },
        "desc": {
          "type": "string",
          "description": "参数描述"
        },
        "ruleRefCount": {
          "type": "number",
          "description": "试验引用数"
        },
        "abRefCount": {
          "type": "number",
          "description": "规则引用数"
        },
        "updateAt": {
          "type": "string",
          "description": "数据更新时间"
        },
        "createBy": {
          "type": "number",
          "description": "创建人主键Id"
        },
        "createUser": {
          "type": "string",
          "description": "创建人名称"
        }
      },
      "required": [
        "id",
        "name",
        "type",
        "typeText",
        "valueCount",
        "valueList",
        "desc",
        "ruleRefCount",
        "abRefCount",
        "updateAt",
        "createBy",
        "createUser"
      ]
    }
  ]
}
```
