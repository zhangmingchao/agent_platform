# rule.get.portal_configDistributionRule_ruleGroup_getFileUploadTemplate.d889f35d

GetFileUploadTemplate 获取文件上传下载模板

- 服务：rule；后端相对路径：`/portal/configDistributionRule/ruleGroup/getFileUploadTemplate`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：special；Schema：declared。
- 说明：下载或导出协议，当前工具只接收 JSON；目录保留接口说明
- 后端源码：rule/router/portal.go:82。
- 后端源码：rule/router/config_distribution/conflict_group.go:217。

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
