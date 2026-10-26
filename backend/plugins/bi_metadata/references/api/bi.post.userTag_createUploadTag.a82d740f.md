# bi.post.userTag_createUploadTag.a82d740f

删除标签

- 服务：bi；后端相对路径：`/userTag/createUploadTag`；方法：POST。
- 前端路径：/bi-docker/api/userTag/createUploadTag。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:84。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:78；方法 createUploadTag；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "file": {
        "x-source-type": "MultipartFile",
        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
        "description": "#Author zc #Description #Date 2023/8/22 13:39 /"
      },
      "name": {
        "type": "string",
        "description": "#Author zc #Description #Date 2023/8/22 13:39 /"
      },
      "remark": {
        "type": "string",
        "description": "#Author zc #Description #Date 2023/8/22 13:39 /"
      },
      "productRegion": {
        "type": "string",
        "description": "#Author zc #Description #Date 2023/8/22 13:39 /"
      },
      "productKeys": {
        "type": "string",
        "description": "#Author zc #Description #Date 2023/8/22 13:39 /"
      },
      "computeType": {
        "type": "integer",
        "description": "#Author zc #Description #Date 2023/8/22 13:39 /"
      },
      "category": {
        "type": "integer"
      },
      "productKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "entityStr": {
        "type": "string"
      },
      "entity": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "主体名称 对应 entityType /"
          },
          "type": {
            "type": "integer",
            "description": "0.预置主体 1.自定义主体 【标签场景】 /"
          },
          "tableType": {
            "type": "integer",
            "description": "0.事件 1.用户 /"
          },
          "profileType": {
            "type": "string",
            "description": "string,decimal,boolean,array,date /"
          },
          "profileClassify": {
            "type": "integer",
            "description": "0.自定义属性 1.预置属性 2.虚拟属性 /"
          },
          "parentProfileName": {
            "type": "string",
            "description": "0.自定义属性 1.预置属性 2.虚拟属性 /"
          },
          "propertiesName": {
            "type": "string",
            "description": "0.自定义属性 1.预置属性 2.虚拟属性 /"
          },
          "isCustomId": {
            "type": "boolean",
            "description": "0.自定义属性 1.预置属性 2.虚拟属性 /"
          }
        },
        "x-source-type": "UserTagEntity",
        "x-source": {
          "project": "bi-docker",
          "file": "da-dao/src/main/java/com/reyun/da/dao/dto/usertag/UserTagEntity.java",
          "line": 1
        }
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
  "backend_type": "ResultModel<Object>",
  "backend_schema": {
    "x-source-type": "ResultModel<Object>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
