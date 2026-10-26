# bi.any.export_download_downUplGroupTmp.836e1899

下载上传分群模板文件

- 服务：bi；后端相对路径：`/export/download/downUplGroupTmp`；方法：ANY。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：unverified；Schema：declared。
- 说明：未确定 HTTP 方法或非业务方法
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/DownloadController.java:181。

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
