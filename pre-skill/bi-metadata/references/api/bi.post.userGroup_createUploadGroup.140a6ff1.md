# bi.post.userGroup_createUploadGroup.140a6ff1

获取分组tag

- 服务：bi；后端相对路径：`/userGroup/createUploadGroup`；方法：POST。
- 前端路径：/bi-docker/api/userGroup/createUploadGroup。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usergroup/UserGroupController.java:119。
- 前端源码：solar-engine-fe/src/api/modules/userGroup/index.ts:22；方法 createUploadGroup；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "file": {
        "x-source-type": "MultipartFile",
        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
        "description": "@Author zc @Description 导入文件实体 @Date 2021/10/25 12:00 /"
      },
      "groupName": {
        "type": "string",
        "description": "@Author zc @Description 导入文件实体 @Date 2021/10/25 12:00 /"
      },
      "remark": {
        "type": "string",
        "description": "@Author zc @Description 导入文件实体 @Date 2021/10/25 12:00 /"
      },
      "productKey": {
        "type": "string",
        "description": "@Author zc @Description 导入文件实体 @Date 2021/10/25 12:00 /"
      },
      "analysisBodyVo": {
        "type": "string",
        "description": "@Author zc @Description 导入文件实体 @Date 2021/10/25 12:00 /"
      }
    },
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
  "backend_type": "ResultModel<String>",
  "backend_schema": {
    "x-source-type": "ResultModel<String>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
