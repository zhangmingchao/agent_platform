# bi.post.external_report_detail.6e58c0c1

reportDetail

- 服务：bi；后端相对路径：`/external/report/detail`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：internal；Schema：declared。
- 说明：测试、维护、认证或服务间调用 Controller，非 Agent 业务入口
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/nologin/NoLoginController.java:185。

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
      "reportId": {
        "type": "integer"
      },
      "timeZone": {
        "type": "string"
      },
      "timeParticleStr": {
        "type": "string"
      },
      "timeParticle": {
        "type": "integer"
      },
      "startDate": {
        "type": "string"
      },
      "dateType": {
        "type": "integer"
      },
      "endDate": {
        "type": "string"
      }
    },
    "x-source-type": "ReportDetailApiVo",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/analysis/ReportDetailApiVo.java",
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
  "backend_type": "void",
  "backend_schema": {
    "x-source-type": "void",
    "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
  },
  "frontend_schemas": []
}
```
