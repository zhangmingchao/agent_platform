# rule.post.portal_experiment_setOffline.8245ee25

SetOffline 试验下线

- 服务：rule；后端相对路径：`/portal/experiment/setOffline`；方法：POST。
- 前端路径：/portal/ab/experiment/setOffline。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：rule/router/portal.go:188。
- 后端源码：rule/router/experiment/experiment.go:220。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:32；方法 offline；参数类型 `any`。

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
      "experimentGroupId": {
        "type": "integer"
      },
      "paramList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer"
            },
            "experimentGroupId": {
              "type": "integer",
              "description": "试验分组id"
            },
            "paramId": {
              "type": "integer",
              "description": "试验参数id"
            },
            "paramName": {
              "type": "string",
              "description": "参数名称"
            },
            "paramValueId": {
              "type": "integer",
              "description": "试验参数值id"
            },
            "paramValueText": {
              "type": "string",
              "description": "试验参数值文本"
            }
          },
          "x-source-type": "ExperimentGroupParamsDto",
          "x-source": {
            "project": "rule",
            "file": "pkg/dto/dto_experiment/experiment_group_params_dto.go",
            "line": 1
          }
        }
      },
      "ruleGroupId": {
        "type": "integer"
      },
      "conflictRuleGroupIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      }
    },
    "x-source-type": "dto_experiment.ExperimentOfflineDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/dto_experiment/experiment_dto.go",
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
