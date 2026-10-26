# rule.post.portal_experiment_experimentLayer_modify.abceb9f9

ModifyExperimentLayer 编辑试验层

- 服务：rule；后端相对路径：`/portal/experiment/experimentLayer/modify`；方法：POST。
- 前端路径：/portal/ab/experiment/experimentLayer/modify。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：rule/router/portal.go:196。
- 后端源码：rule/router/experiment/experiment_layer.go:81。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:91；方法 editExperimentLayer；参数类型 `any`。

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
        "description": "试验层名称"
      },
      "desc": {
        "type": "string",
        "description": "规则描述"
      },
      "status": {
        "type": "integer",
        "description": "状态。1:可用;-1:删除;"
      },
      "experimentNum": {
        "type": "integer",
        "description": "试验数量"
      },
      "inUse": {
        "type": "integer",
        "description": "试验是否正在运行中。1:是 2:否"
      },
      "experimentList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "试验名称列表"
      },
      "diversionBody": {
        "type": "string",
        "description": "分流主体"
      },
      "diversionBodyType": {
        "type": "integer",
        "description": "分流主体类型"
      },
      "diversionBodyTableType": {
        "type": "integer",
        "description": "分流主体对应属性表"
      },
      "createBy": {
        "type": "integer",
        "description": "创建人id"
      },
      "createAt": {
        "type": "string",
        "description": "创建时间"
      },
      "updateBy": {
        "type": "integer",
        "description": "修改人id"
      },
      "updateAt": {
        "type": "string",
        "description": "修改时间"
      },
      "createByName": {
        "type": "string",
        "description": "创建人账号"
      }
    },
    "x-source-type": "dto_experiment.ExperimentLayerInfoDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/dto_experiment/experiment_layer_info_dto.go",
      "line": 1
    },
    "required": [
      "id"
    ]
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
