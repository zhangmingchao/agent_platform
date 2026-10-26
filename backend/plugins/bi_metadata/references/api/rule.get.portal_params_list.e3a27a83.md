# rule.get.portal_params_list.e3a27a83

GetParamInfoList 获取参数列表

- 服务：rule；后端相对路径：`/portal/params/list`；方法：GET。
- 前端路径：/portal/rule/params/list。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:208。
- 后端源码：rule/router/param_info.go:17。
- 前端源码：solar-engine-fe/src/api/modules/rule/index.ts:13；方法 getParamList；参数类型 `Pick<TTablePayloadType<TAppId & { text: string; }>, "pageNum" | "pageSize" | "orderBy" | "orderColumn" | "appId" | "text">`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "appId": {
        "anyOf": [
          {
            "type": "number"
          },
          {
            "type": "string",
            "const": ""
          }
        ]
      },
      "text": {
        "type": "string",
        "description": "参数名称或描述"
      },
      "pageNum": {
        "type": "number",
        "description": "页码",
        "minimum": 1,
        "default": 1
      },
      "pageSize": {
        "type": "number",
        "description": "每页显示条数",
        "minimum": 1,
        "default": 50,
        "maximum": 200
      },
      "orderBy": {
        "type": "string",
        "description": "排序方式(asc 升序 / desc 降序)"
      },
      "orderColumn": {
        "type": "string",
        "description": "排序列key值"
      }
    },
    "required": [
      "appId"
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
        "pageNum": {
          "type": "number",
          "description": "页码"
        },
        "pageSize": {
          "type": "number",
          "description": "每页显示条数"
        },
        "pageTotal": {
          "type": "number",
          "description": "总页数"
        },
        "total": {
          "type": "number",
          "description": "总条数"
        },
        "channels": {
          "type": "array",
          "items": {
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
          },
          "description": "表格返回数据"
        },
        "sans": {
          "type": "array",
          "items": {
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
        },
        "dataList": {
          "type": "array",
          "items": {
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
        }
      },
      "required": [
        "pageNum",
        "pageSize",
        "pageTotal",
        "total",
        "channels",
        "sans",
        "dataList"
      ]
    }
  ]
}
```
