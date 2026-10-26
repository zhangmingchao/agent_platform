# 接口覆盖与差异

```json
{
  "endpoints": 375,
  "frontend_url_constants": 564,
  "frontend_http_calls": 547,
  "unused_target_urls": 16,
  "unresolved_frontend_calls": 47,
  "service": {
    "bi": 304,
    "rule": 71
  },
  "match_status": {
    "backend_only": 132,
    "frontend_only": 16,
    "matched": 227
  },
  "operation": {
    "internal": 62,
    "read": 148,
    "special": 10,
    "unverified": 17,
    "write": 138
  }
}
```

前端存在、后端缺失的契约和未使用 URL 均保留，不能凭 URL 名称推测可调用性。

## 未使用的前端 URL 常量

| 常量 | 路径 | 源码 |
|---|---|---|
| URL.REPORT.DOWNLOAD_REPORT_USER | /bi-docker/api/export/download/userProfileAnalysis | src/api/url/report.ts:63 |
| URL.ANALYSIS_REPORT.DOWNLOAD_USER_LIST | /bi-docker/api/export/download/userList | src/api/url/analysisReport.ts:49 |
| URL.ANALYSIS_REPORT.VERIFY_NAME | /bi-docker/api/reportForm/verifyName | src/api/url/analysisReport.ts:53 |
| URL.ANALYSIS.EVEDOWN | /bi-docker/api/export/download/ | src/api/url/analysis.ts:23 |
| URL.ANALYSIS.ANALYSIS_SUBJECT_DETAIL | /bi-docker/api/analysisBody/detail | src/api/url/analysis.ts:55 |
| URL.DATAMANAGE.eventList | /bi-docker/api/profileType/findByProductKey | src/api/url/dateManage.ts:7 |
| URL.DATAMANAGE.downloadLogStream | /bi-docker/api/buriedData/logStreamDownload | src/api/url/dateManage.ts:99 |
| URL.DATAMANAGE.USER_PROFILE_LIST | /bi-docker/api/profileUser/findAllUserProfList | src/api/url/dateManage.ts:109 |
| URL.DATAMANAGE.FIND_ALLEVENT_PROF_LIST | /bi-docker/api/profileType/findAllEventProfList | src/api/url/dateManage.ts:113 |
| URL.DATAMANAGE.EVENT_PROFILE_LIST | /bi-docker/api/eventConfig/findEventList | src/api/url/dateManage.ts:117 |
| URL.DATAMANAGE.DIMENSION_DOWNLOAD | /bi-docker/api/dimension/value/download | src/api/url/dateManage.ts:228 |
| URL.PANEL.VERIFY_NAME | /bi-docker/api/boardMenu/verifyName | src/api/url/panel.ts:56 |
| URL.USERGROUP.GET_GROUP_PROFILE_LIST | /bi-docker/api/userTag/getProfileList | src/api/url/userGroup.ts:9 |
| URL.USERGROUP.CREATE_RESULT_GROUP | /bi-docker/api/userGroup/createResultGroup | src/api/url/userGroup.ts:13 |
| URL.USERGROUP.DOWNLOAD | /bi-docker/api/export/download/downTagUserList | src/api/url/userGroup.ts:27 |
| URL.ABTESTING.GETEXPERIMENLAYER | /portal/ab/experiment/getExperimenLayer | src/api/url/abtesting.ts:22 |

## 动态路径或未解析的前端调用

以下调用保留源码位置；运行时拼接的路径不会被猜测成新的可执行接口。目标服务由固定 URL 目录及后端路由对照确认。

| 方法 | 表达式 | 源码 |
|---|---|---|
| GET | URL.REPORT.COLUMNS | src/api/modules/report/index.ts:13 |
| POST | URL.REPORT.SAVE_COLUMNS | src/api/modules/report/index.ts:17 |
| POST | URL.REPORT.OLD_OPTIMIZE_LIST | src/api/modules/report/index.ts:22 |
| POST | URL.REPORT.OPTIMIZE_LIST | src/api/modules/report/index.ts:26 |
| POST | URL.REPORT.HOUR_OPTIMIZE_LIST | src/api/modules/report/index.ts:30 |
| POST | URL.REPORT.OLD_OPTIMIZE_LIST_TOTAL | src/api/modules/report/index.ts:34 |
| POST | URL.REPORT.OPTIMIZE_LIST_TOTAL | src/api/modules/report/index.ts:38 |
| POST | URL.REPORT.HOUR_OPTIMIZE_LIST_TOTAL | src/api/modules/report/index.ts:42 |
| POST | URL.REPORT.OLD_DOWNLOAD_REPORT_OPTIMIZE | src/api/modules/report/index.ts:46 |
| POST | URL.REPORT.DOWNLOAD_REPORT_OPTIMIZE | src/api/modules/report/index.ts:50 |
| POST | URL.REPORT.DOWNLOAD_REPORT_HOUR_OPTIMIZE | src/api/modules/report/index.ts:54 |
| POST | URL.REPORT.OLD_APP_LIST | src/api/modules/report/index.ts:59 |
| POST | URL.REPORT.APP_LIST | src/api/modules/report/index.ts:63 |
| POST | URL.REPORT.OLD_APP_LIST_TOTAL | src/api/modules/report/index.ts:68 |
| POST | URL.REPORT.APP_LIST_TOTAL | src/api/modules/report/index.ts:72 |
| POST | URL.REPORT.OLD_DOWNLOAD_REPORT_APP | src/api/modules/report/index.ts:77 |
| POST | URL.REPORT.DOWNLOAD_REPORT_APP | src/api/modules/report/index.ts:82 |
| POST | URL.REPORT.FINANCE_PROMOTION | src/api/modules/report/index.ts:87 |
| POST | URL.REPORT.FINANCE_PROMOTION_TOTAL | src/api/modules/report/index.ts:91 |
| POST | URL.REPORT.DOWNLOAD_REPORT_FINANCE_PROMOTION | src/api/modules/report/index.ts:96 |
| POST | URL.REPORT.FINANCE_MONETIZATION | src/api/modules/report/index.ts:101 |
| POST | URL.REPORT.FINANCE_MONETIZATION_TOTAL | src/api/modules/report/index.ts:105 |
| POST | URL.REPORT.DOWNLOAD_REPORT_FINANCE_MONETIZATION | src/api/modules/report/index.ts:109 |
| POST | URL.REPORT.FINANCE_ROI | src/api/modules/report/index.ts:114 |
| POST | URL.REPORT.FINANCE_ROI_TOTAL | src/api/modules/report/index.ts:118 |
| POST | URL.REPORT.DOWNLOAD_REPORT_FINANCE_ROI | src/api/modules/report/index.ts:122 |
| GET | URL.REPORT.REPORT_APP_SUMMARY | src/api/modules/report/index.ts:130 |
| GET | URL.REPORT.OLD_REPORT_APP_ANALYSIS_CHART | src/api/modules/report/index.ts:137 |
| GET | URL.REPORT.REPORT_APP_ANALYSIS_CHART | src/api/modules/report/index.ts:144 |
| GET | URL.REPORT.OLD_REPORT_APP_TABLE_LIST | src/api/modules/report/index.ts:151 |
| GET | URL.REPORT.REPORT_APP_TABLE_LIST | src/api/modules/report/index.ts:158 |
| GET | URL.REPORT.GET_APP_VERSION_LIST | src/api/modules/report/index.ts:166 |
| GET | URL.REPORT.GET_ROI_TRACKER_LIST | src/api/modules/report/index.ts:170 |
| GET | URL.REPORT.GET_ROI_OPTIMIZER_LIST | src/api/modules/report/index.ts:174 |
| GET | URL.REPORT.GET_AD_TYPE_LIST | src/api/modules/report/index.ts:178 |
| GET | URL.REPORT.CHANNEL_PACKAGE_LIST | src/api/modules/report/index.ts:182 |
| GET | URL.REPORT.GET_ROI_REPORT_LIST | src/api/modules/report/index.ts:192 |
| POST | URL.REPORT.SAVE_ROI_REPORT | src/api/modules/report/index.ts:213 |
| POST | URL.REPORT.COPY_ROI_REPORT | src/api/modules/report/index.ts:221 |
| POST | URL.REPORT.DELETE_ROI_REPORT | src/api/modules/report/index.ts:226 |
| GET | URL.REPORT.GET_ROI_REPORT_BY_ID | src/api/modules/report/index.ts:231 |
| POST | URL.REPORT.RECORD_LAST_VISIT_REPORT | src/api/modules/report/index.ts:236 |
| GET | URL.REPORT.GET_LAST_VISIT_REPORT | src/api/modules/report/index.ts:241 |
| GET | URL.REPORT.UPDATE_TIME | src/api/modules/report/index.ts:245 |
| GET | `${URL.COMMON.CHECK_TAG}?t=${new Date().getTime()}` | src/api/modules/common/index.ts:15 |
| POST | url | src/api/modules/dataManage/index.ts:23 |
| POST | url | src/api/modules/dataManage/index.ts:323 |
