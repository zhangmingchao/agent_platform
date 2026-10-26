# bi.post.export_download_createOfflineExportRecord.c56c74eb

下载(创建离线任务)

- 服务：bi；后端相对路径：`/export/download/createOfflineExportRecord`；方法：POST。
- 前端路径：/bi-docker/api/export/download/createOfflineExportRecord。
- 状态：matched；操作：special；Schema：partial。
- 说明：下载或导出协议，当前工具只接收 JSON；目录保留接口说明
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/DownloadController.java:304。
- 前端源码：solar-engine-fe/src/api/modules/anasysis/index.ts:58；方法 exportDownload；参数类型 `any`。

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
        "type": "integer",
        "description": "主键ID /"
      },
      "uid": {
        "type": "integer",
        "description": "用户ID 主键 /"
      },
      "productList": {
        "type": "string",
        "description": "产品列表，按product_key逗号分割 /"
      },
      "module": {
        "type": "string",
        "description": "模块 /"
      },
      "fileName": {
        "type": "string",
        "description": "文件名 /"
      },
      "conditionString": {
        "type": "string",
        "description": "筛选 /"
      },
      "condition": {
        "x-source-type": "Object",
        "x-unresolved": "动态 JSON，参数形状需查调用页面",
        "description": "筛选 /"
      },
      "fileSize": {
        "type": "integer",
        "description": "文件大小 /"
      },
      "status": {
        "type": "integer",
        "description": "状态：0:生成中 1:完成，2:生成失败,3:已过期 /"
      },
      "resultSize": {
        "type": "integer",
        "description": "总条数"
      },
      "timeZone": {
        "type": "string",
        "description": "总条数"
      },
      "appIds": {
        "type": "string",
        "description": "总条数"
      },
      "isAllApp": {
        "type": "string",
        "description": "总条数"
      },
      "language": {
        "type": "string",
        "description": "总条数"
      },
      "parentId": {
        "type": "integer",
        "description": "总条数"
      },
      "userCode": {
        "type": "string",
        "description": "总条数"
      },
      "appKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "return JSON.toJSONString(new DetailInfo(resultSize, timeZone, appKeyList));"
      }
    },
    "x-source-type": "OfflineExportRecordDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/event/OfflineExportRecordDto.java",
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
