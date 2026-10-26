# rule.post.portal_configDistributionRule_ruleGroup_notifyUpsAudienceTaskStatus.cc1cb8ce

config_distribution.NotifyUpsAudienceTaskStatus

- 服务：rule；后端相对路径：`/portal/configDistributionRule/ruleGroup/notifyUpsAudienceTaskStatus`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：internal；Schema：declared。
- 说明：测试、免登录、服务间调用或维护接口
- 后端源码：rule/router/portal.go:112。
- 后端源码：rule/router/config_distribution/conflict_group.go:195。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
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
  "frontend_schemas": []
}
```
