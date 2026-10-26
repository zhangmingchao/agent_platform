# bi.get.export_download_testResultHandler.494d47a3

testResultHandler

- 服务：bi；后端相对路径：`/export/download/testResultHandler`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：special；Schema：declared。
- 说明：下载或导出协议，当前工具只接收 JSON；目录保留接口说明
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/DownloadController.java:213。

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
  "backend_type": "void",
  "backend_schema": {
    "x-source-type": "void",
    "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
  },
  "frontend_schemas": []
}
```
