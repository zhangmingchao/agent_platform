# rule.get.portal_experiment_setOnline.820548b1

SetOnline 试验上线

- 服务：rule；后端相对路径：`/portal/experiment/setOnline`；方法：GET。
- 前端路径：/portal/ab/experiment/setOnline。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：rule/router/portal.go:182。
- 后端源码：rule/router/experiment/experiment.go:134。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:17；方法 online；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      }
    },
    "required": [
      "id"
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
