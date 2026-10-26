# bi.post.dimension_value_createByFile.b24ec74e

新增维度值

- 服务：bi；后端相对路径：`/dimension/value/createByFile`；方法：POST。
- 前端路径：/bi-docker/api/dimension/value/createByFile。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/DimensionValueController.java:64。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:343；方法 dimensionCreate；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
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
        "description": "纬度对应的主属性 /",
        "minimum": 1,
        "default": 1
      },
      "pageSize": {
        "type": "integer",
        "description": "纬度对应的主属性 /",
        "minimum": 1,
        "default": 50,
        "maximum": 200
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
  "backend_type": "ResultModel",
  "backend_schema": {
    "type": "object",
    "properties": {
      "code": {
        "type": "integer",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "msg": {
        "type": "string",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "timeZone": {
        "type": "string",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "data": {
        "x-source-type": "T",
        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "msgType": {
        "type": "integer",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      }
    },
    "x-source-type": "ResultModel",
    "x-source": {
      "project": "bi-docker",
      "file": "da-common/src/main/java/com/reyun/da/common/api/ResultModel.java",
      "line": 1
    }
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
