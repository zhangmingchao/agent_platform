# bi.post.dimension_value_download.e47f99c9

获取纬度值列表

- 服务：bi；后端相对路径：`/dimension/value/download`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：special；Schema：partial。
- 说明：下载或导出协议，当前工具只接收 JSON；目录保留接口说明
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/DimensionValueController.java:97。

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
      "id": {
        "type": "integer"
      },
      "uploadType": {
        "type": "integer"
      },
      "tenantId": {
        "type": "string"
      },
      "prokey": {
        "type": "string"
      },
      "dimensionMainProfileName": {
        "type": "string",
        "description": "纬度对应的主属性 /"
      },
      "dimensionMainProfileClassify": {
        "type": "integer",
        "description": "纬度对应的主属性 /"
      },
      "inputValueList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "纬度对应的主属性 /"
      },
      "searchText": {
        "type": "string",
        "description": "纬度对应的主属性 /"
      },
      "pageNum": {
        "type": "integer",
        "description": "纬度对应的主属性 /"
      },
      "pageSize": {
        "type": "integer",
        "description": "纬度对应的主属性 /"
      },
      "template": {
        "type": "boolean",
        "description": "纬度对应的主属性 /"
      },
      "file": {
        "x-source-type": "MultipartFile",
        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
        "description": "纬度对应的主属性 /"
      },
      "sortFieldName": {
        "type": "string",
        "description": "纬度对应的主属性 /"
      },
      "sortType": {
        "type": "integer",
        "description": "降序 -1 升序 和之前一样"
      }
    },
    "x-source-type": "DimensionValueDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/DimensionValueDto.java",
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
