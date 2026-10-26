# rule.get.portal_experiment_getExperimentGroupList.284e288e

GetExperimentGroupList 获取当前试验下的实验组

- 服务：rule；后端相对路径：`/portal/experiment/getExperimentGroupList`；方法：GET。
- 前端路径：/portal/ab/experiment/getExperimentGroupList。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：rule/router/portal.go:156。
- 后端源码：rule/router/experiment/experiment.go:338。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:47；方法 getExperimentGroupList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "optType": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      }
    },
    "required": [
      "id",
      "optType"
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
