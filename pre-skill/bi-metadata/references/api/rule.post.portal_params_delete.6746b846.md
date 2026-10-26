# rule.post.portal_params_delete.6746b846

DeleteParam 删除参数

- 服务：rule；后端相对路径：`/portal/params/delete`；方法：POST。
- 前端路径：/portal/rule/params/delete。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：rule/router/portal.go:223。
- 后端源码：rule/router/param_info.go:173。
- 前端源码：solar-engine-fe/src/api/modules/rule/index.ts:55；方法 delete；参数类型 `TParamId`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  },
  "body_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer"
      },
      "appId": {
        "type": "integer",
        "description": "应用id"
      },
      "name": {
        "type": "string",
        "description": "参数名称"
      },
      "type": {
        "type": "integer",
        "description": "参数类型"
      },
      "typeText": {
        "type": "string",
        "description": "参数类型"
      },
      "desc": {
        "type": "string",
        "description": "描述"
      },
      "valueList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer",
              "description": "ID"
            },
            "paramId": {
              "type": "integer",
              "description": "参数ID"
            },
            "value": {
              "x-source-type": "any",
              "x-unresolved": "动态 JSON，参数形状需查调用页面",
              "description": "参数值"
            },
            "isDefault": {
              "type": "integer",
              "description": "是否是默认，1-是，2-否"
            },
            "inUse": {
              "type": "integer",
              "description": "是否在使用，1-是，2-否"
            }
          },
          "x-source-type": "ParamValueDto",
          "x-source": {
            "project": "rule",
            "file": "pkg/dto/param_value_dto.go",
            "line": 1
          }
        },
        "description": "值列表"
      }
    },
    "x-source-type": "dto.ParamInfoDetailDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/param_info_dto.go",
      "line": 1
    }
  },
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
