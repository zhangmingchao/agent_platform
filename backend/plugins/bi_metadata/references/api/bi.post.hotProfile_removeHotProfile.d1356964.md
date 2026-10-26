# bi.post.hotProfile_removeHotProfile.d1356964

取消

- 服务：bi；后端相对路径：`/hotProfile/removeHotProfile`；方法：POST。
- 前端路径：/bi-docker/api/hotProfile/removeHotProfile。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/HotProfileController.java:49。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:248；方法 removeStore；参数类型 `any`。

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
      "productKey": {
        "type": "string"
      },
      "type": {
        "type": "integer"
      },
      "value": {
        "type": "string"
      },
      "name": {
        "type": "string"
      },
      "userId": {
        "type": "integer"
      },
      "profileName": {
        "type": "string"
      },
      "createAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      }
    },
    "x-source-type": "HotProfileDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/datamanage/HotProfileDto.java",
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
