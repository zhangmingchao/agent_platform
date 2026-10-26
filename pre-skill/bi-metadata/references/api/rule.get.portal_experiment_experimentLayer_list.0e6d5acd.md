# rule.get.portal_experiment_experimentLayer_list.0e6d5acd

GetExperimentLayerList 获取试验层列表

- 服务：rule；后端相对路径：`/portal/experiment/experimentLayer/list`；方法：GET。
- 前端路径：/portal/ab/experiment/experimentLayer/list。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:170。
- 后端源码：rule/router/experiment/experiment_layer.go:15。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:106；方法 experimentLayerTableList；参数类型 `Pick<TTablePayloadType<TAppId>, "pageNum" | "pageSize" | "orderBy" | "orderColumn" | "appId">`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
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
      "appId",
      "pageNum",
      "pageSize"
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
              "name": {
                "type": "string",
                "description": "试验层名称"
              },
              "id": {
                "type": "number",
                "description": "试验层主键Id"
              },
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
              "desc": {
                "type": "string",
                "description": "试验层描述"
              },
              "diversionBody": {
                "type": "string",
                "description": "分流主体名称"
              },
              "diversionBodyType": {
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
                "description": "分流主体类型"
              },
              "diversionBodyTableType": {
                "anyOf": [
                  {
                    "type": "number",
                    "const": 0
                  },
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
                  }
                ],
                "description": "属性类型（自定义ID - 属性）"
              },
              "inUse": {
                "type": "number",
                "description": "是否被引用"
              },
              "experimentNum": {
                "type": "number",
                "description": "试验数"
              },
              "experimentList": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "试验列表"
              },
              "createBy": {
                "type": "number",
                "description": "创建人主键Id"
              },
              "createByName": {
                "type": "string",
                "description": "创建人名称"
              }
            },
            "required": [
              "name",
              "id",
              "appId",
              "desc",
              "diversionBody",
              "diversionBodyType",
              "diversionBodyTableType",
              "inUse",
              "experimentNum",
              "experimentList",
              "createBy",
              "createByName"
            ]
          },
          "description": "表格返回数据"
        },
        "sans": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {
                "type": "string",
                "description": "试验层名称"
              },
              "id": {
                "type": "number",
                "description": "试验层主键Id"
              },
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
              "desc": {
                "type": "string",
                "description": "试验层描述"
              },
              "diversionBody": {
                "type": "string",
                "description": "分流主体名称"
              },
              "diversionBodyType": {
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
                "description": "分流主体类型"
              },
              "diversionBodyTableType": {
                "anyOf": [
                  {
                    "type": "number",
                    "const": 0
                  },
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
                  }
                ],
                "description": "属性类型（自定义ID - 属性）"
              },
              "inUse": {
                "type": "number",
                "description": "是否被引用"
              },
              "experimentNum": {
                "type": "number",
                "description": "试验数"
              },
              "experimentList": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "试验列表"
              },
              "createBy": {
                "type": "number",
                "description": "创建人主键Id"
              },
              "createByName": {
                "type": "string",
                "description": "创建人名称"
              }
            },
            "required": [
              "name",
              "id",
              "appId",
              "desc",
              "diversionBody",
              "diversionBodyType",
              "diversionBodyTableType",
              "inUse",
              "experimentNum",
              "experimentList",
              "createBy",
              "createByName"
            ]
          }
        },
        "dataList": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {
                "type": "string",
                "description": "试验层名称"
              },
              "id": {
                "type": "number",
                "description": "试验层主键Id"
              },
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
              "desc": {
                "type": "string",
                "description": "试验层描述"
              },
              "diversionBody": {
                "type": "string",
                "description": "分流主体名称"
              },
              "diversionBodyType": {
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
                "description": "分流主体类型"
              },
              "diversionBodyTableType": {
                "anyOf": [
                  {
                    "type": "number",
                    "const": 0
                  },
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
                  }
                ],
                "description": "属性类型（自定义ID - 属性）"
              },
              "inUse": {
                "type": "number",
                "description": "是否被引用"
              },
              "experimentNum": {
                "type": "number",
                "description": "试验数"
              },
              "experimentList": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "试验列表"
              },
              "createBy": {
                "type": "number",
                "description": "创建人主键Id"
              },
              "createByName": {
                "type": "string",
                "description": "创建人名称"
              }
            },
            "required": [
              "name",
              "id",
              "appId",
              "desc",
              "diversionBody",
              "diversionBodyType",
              "diversionBodyTableType",
              "inUse",
              "experimentNum",
              "experimentList",
              "createBy",
              "createByName"
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
