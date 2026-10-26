# utilities-internal 接口参考

自动对照前后端源码生成。目录状态不等于线上验证；调用前使用 `SolarCatalog` 的 describe 获取完整契约。

| 接口 ID | 方法与路径 | 用途 | 状态 / 操作 |
|---|---|---|---|
| `bi.get..62430933` | GET / | apiIndex | backend_only / internal |
| `bi.get.aa.4ffa82cb` | GET /aa | aa | backend_only / internal |
| `bi.get.account_reportAssignList.f36385b9` | GET /account/reportAssignList | URL.PANEL.ACCOUNT_LIST | frontend_only / unverified |
| `bi.get.base_getCurrencyTypeList.067d58df` | GET /base/getCurrencyTypeList | 币种列表 | matched / read |
| `bi.get.export_callOfflineDataExport.e83a913d` | GET /export/callOfflineDataExport | 执行文件导出 | backend_only / special |
| `bi.post.export_download_4.192fcab1` | POST /export/download/4 | scaSave($data){ return Http.post(URL.ANALYSIS.SCASAVE, $data); }, | frontend_only / unverified |
| `bi.post.export_download_createOfflineExportBatch.b7ead93a` | POST /export/download/createOfflineExportBatch | 下载(创建离线任务) | backend_only / special |
| `bi.post.export_download_createOfflineExportRecord.c56c74eb` | POST /export/download/createOfflineExportRecord | 下载(创建离线任务) | matched / special |
| `bi.post.export_download_downGroupUserList.4a1531d7` | POST /export/download/downGroupUserList | 下载(用户分群-用户列表) | backend_only / special |
| `bi.post.export_download_downTagUserList.84606a51` | POST /export/download/downTagUserList | 下载(用户标签-用户列表) | backend_only / special |
| `bi.any.export_download_downUplGroupTmp.836e1899` | ANY /export/download/downUplGroupTmp | 下载上传分群模板文件 | backend_only / unverified |
| `bi.get.export_download_testResultHandler.494d47a3` | GET /export/download/testResultHandler | testResultHandler | backend_only / special |
| `bi.post.export_download_userList.00a69e34` | POST /export/download/userList | 下载(用户列表) | backend_only / special |
| `bi.post.export_download_analyseType.482614c5` | POST /export/download/{analyseType} | 下载 | backend_only / special |
| `bi.get.external_getVisitorLog.004845e0` | GET /external/getVisitorLog | getVisitorLog | backend_only / internal |
| `bi.post.external_getVisitorToken.21388d5a` | POST /external/getVisitorToken | getVisitorToken | backend_only / internal |
| `bi.get.health_check.ba70495e` | GET /health/check | healthCheck | backend_only / internal |
| `bi.get.health_deleteFile.bfbb65a0` | GET /health/deleteFile | getOfflineDownloadUrl | backend_only / internal |
| `bi.get.health_getDownloadUrl.9cc7f8f2` | GET /health/getDownloadUrl | saveFile | backend_only / internal |
| `bi.get.health_getOfflineDownloadUrl.bae8cb68` | GET /health/getOfflineDownloadUrl | getDownloadUrl | backend_only / internal |
| `bi.get.health_getReturnSqlTag.6b4f4cad` | GET /health/getReturnSqlTag | getReturnSqlTag | backend_only / internal |
| `bi.get.health_getTestErr.005173c3` | GET /health/getTestErr | getTestErr | backend_only / internal |
| `bi.get.health_getVisitorLog.2f63cda4` | GET /health/getVisitorLog | getVisitorLog | backend_only / internal |
| `bi.get.health_i18n.7b9945f6` | GET /health/i18n | i18n | backend_only / internal |
| `bi.get.health_i18nModel.a6f8e5da` | GET /health/i18nModel | i18nParam | backend_only / internal |
| `bi.get.health_i18nParam.88e1e2bf` | GET /health/i18nParam | i18n | backend_only / internal |
| `bi.get.health_industryJob.8106df08` | GET /health/industryJob | industryJob | backend_only / internal |
| `bi.get.health_initForexRate.d78ee2ce` | GET /health/initForexRate | initForexRate | backend_only / internal |
| `bi.get.health_initProp.c243d4f3` | GET /health/initProp | getReturnSqlTag | backend_only / internal |
| `bi.post.health_invokeParent.f0b5fe60` | POST /health/invokeParent | invokeParent | backend_only / internal |
| `bi.post.health_postTestErr.a3488a12` | POST /health/postTestErr | postTestErr | backend_only / internal |
| `bi.get.health_saveFile.6286c515` | GET /health/saveFile | testWebServer | backend_only / internal |
| `bi.get.health_setReturnSql.4fcd20f5` | GET /health/setReturnSql | setReturnSql | backend_only / internal |
| `bi.get.health_testBB.68c80d68` | GET /health/testBB | testBB | backend_only / internal |
| `bi.get.health_testDb.9e41d751` | GET /health/testDb | testWebServer1 | backend_only / internal |
| `bi.get.health_testReport.012362b3` | GET /health/testReport | testReport | backend_only / internal |
| `bi.get.health_testTag.bd62be05` | GET /health/testTag | testTag | backend_only / internal |
| `bi.get.health_testWebServer.247433f7` | GET /health/testWebServer | testWebServer | backend_only / internal |
| `bi.get.health_testWebServer1.447f0d12` | GET /health/testWebServer1 | deleteFile | backend_only / internal |
| `bi.get.maxAgent_cancelQuestion.6152610a` | GET /maxAgent/cancelQuestion | 取消提问 / | frontend_only / unverified |
| `bi.get.maxAgent_messageList.3449a27d` | GET /maxAgent/messageList | 根据 sessionId 获取历史消息 / | frontend_only / unverified |
| `bi.post.maxAgent_question.d73ad470` | POST /maxAgent/question | 发送问题  新会话：不传 sessionId / | frontend_only / unverified |
| `bi.get.maxAgent_sesssionList.684dff4f` | GET /maxAgent/sesssionList | 获取会话列表（当前登录人） / | frontend_only / unverified |
| `bi.get.maxAgent_updateSessionName.b63fbae7` | GET /maxAgent/updateSessionName | 重命名会话 / | frontend_only / unverified |
| `bi.get.refreshData_refUserAnaBody.a1654642` | GET /refreshData/refUserAnaBody | refUserAnaBody | backend_only / internal |
| `bi.get.refreshData_refreshAnalysisTimeType.ba588518` | GET /refreshData/refreshAnalysisTimeType | refreshTemplate | backend_only / internal |
| `bi.get.refreshData_refreshTemplate.c4520700` | GET /refreshData/refreshTemplate | refreshTemplate | backend_only / internal |
| `bi.get.timeZone_getCurrentTimeZoneDetail.58f8e802` | GET /timeZone/getCurrentTimeZoneDetail | 获取时区对应的小时小时 | matched / read |
| `bi.get.timeZone_getTimeZoneHour.f40f8b24` | GET /timeZone/getTimeZoneHour | 时区列表 | backend_only / read |
| `bi.get.timeZone_getTimeZoneList.26eae09d` | GET /timeZone/getTimeZoneList | list | backend_only / read |
| `bi.get.util_count.d0b474c9` | GET /util/count | getDownloadLimit | backend_only / write |
| `bi.get.util_getAnalysisLimit.f781dee0` | GET /util/getAnalysisLimit | getAnalysisTimeOut | backend_only / read |
| `bi.get.util_getAnalysisTimeOut.7b8b679d` | GET /util/getAnalysisTimeOut | setAnalysisTimeOut | backend_only / read |
| `bi.get.util_getDownloadLimit.749d3f29` | GET /util/getDownloadLimit | getAnalysisLimit | backend_only / read |
| `bi.get.util_refresh0607.e467e18c` | GET /util/refresh0607 | testDing | backend_only / write |
| `bi.get.util_refreshIsNew.1978a87b` | GET /util/refreshIsNew | refreshIsNew | backend_only / write |
| `bi.get.util_refreshSource.04889f8f` | GET /util/refreshSource | refreshSource | backend_only / write |
| `bi.get.util_setAnalysisLimit.56848c6e` | GET /util/setAnalysisLimit | setAnalysisLimit | backend_only / read |
| `bi.get.util_setAnalysisTimeOut.fc0f6f2b` | GET /util/setAnalysisTimeOut | setReturnSql | backend_only / read |
| `bi.get.util_setDownloadLimit.37795294` | GET /util/setDownloadLimit | setAnalysisLimit | backend_only / write |
| `bi.get.util_setReturnSql.3ac52ec3` | GET /util/setReturnSql | setReturnSql | backend_only / write |
| `bi.get.util_testDing.b3a57366` | GET /util/testDing | count | backend_only / write |

## 使用方式

每个接口的参数、返回声明及源码位置见 `references/api/<接口ID>.md`，或调用 SolarCatalog.describe。先检索再读取单个契约，不应一次读取所有接口。
