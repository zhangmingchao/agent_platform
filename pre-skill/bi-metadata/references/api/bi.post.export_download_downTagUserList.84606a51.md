# bi.post.export_download_downTagUserList.84606a51

下载(用户标签-用户列表)

- 服务：bi；后端相对路径：`/export/download/downTagUserList`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：special；Schema：partial。
- 说明：下载或导出协议，当前工具只接收 JSON；目录保留接口说明
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/DownloadController.java:157。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  },
  "body_schema": {
    "x-source-type": "JSONObject",
    "x-unresolved": "动态 JSON，参数形状需查调用页面"
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
