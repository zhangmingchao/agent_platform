# analysis 接口参考

自动对照前后端源码生成。目录状态不等于线上验证；调用前使用 `SolarCatalog` 的 describe 获取完整契约。

| 接口 ID | 方法与路径 | 用途 | 状态 / 操作 |
|---|---|---|---|
| `bi.post.ab_report_ciSql.5b4934ee` | POST /ab/report/ciSql | 获取置信区间所需数据 | backend_only / internal |
| `bi.post.ab_report_getAudCond.0429b367` | POST /ab/report/getAudCond | ab/下发参数 解析condition | backend_only / internal |
| `bi.post.ab_report_indDaySql.5e8f0cf3` | POST /ab/report/indDaySql | 查询单个指标 | backend_only / internal |
| `bi.post.ab_report_indSumSql.1445b919` | POST /ab/report/indSumSql | 指标汇总值 | backend_only / internal |
| `bi.post.ab_report_retentionSql.5d5bfff9` | POST /ab/report/retentionSql | 留存 | backend_only / internal |
| `bi.post.ab_report_sampleComputer.67908632` | POST /ab/report/sampleComputer | 样本计算器 | backend_only / internal |
| `bi.post.external_report_detail.6e58c0c1` | POST /external/report/detail | reportDetail | backend_only / internal |
| `bi.post.external_report_findPermList.2cadb6e8` | POST /external/report/findPermList | findReportListApi | backend_only / internal |
| `bi.post.report_analysisUserEventList.8f2136a9` | POST /report/analysisUserEventList | 用户详情-事件列表 | matched / read |
| `bi.post.report_analysisUserInfoSummary.ba89644e` | POST /report/analysisUserInfoSummary | 用户详情-事件汇总 | matched / read |
| `bi.post.report_analysisUserList.0bece0ea` | POST /report/analysisUserList | 分析模型-用户列表 | matched / read |
| `bi.get.report_checkAnalysisBody.18696097` | GET /report/checkAnalysisBody | 检查分析主体与当前应用是否匹配 | matched / read |
| `bi.post.report_eventAnalysis.e914f96e` | POST /report/eventAnalysis | 事件分析 | matched / read |
| `bi.post.report_findAnalysisEventList.684ec0b4` | POST /report/findAnalysisEventList | 分析下钻 事件列表 | backend_only / read |
| `bi.post.report_findAnalysisUser.7e4496a4` | POST /report/findAnalysisUser | 用户细察 | matched / read |
| `bi.post.report_findEventsAndProfiles.7b84403b` | POST /report/findEventsAndProfiles | AB试验，获取事件、设备属性、用户属性列表 | matched / read |
| `bi.get.report_findIndex.99eced35` | GET /report/findIndex | 事件分析选择框 | matched / read |
| `bi.post.report_findProfVal.74b90b75` | POST /report/findProfVal | 属性数值下拉 | matched / read |
| `bi.post.report_findProfilesByBoard.79216f01` | POST /report/findProfilesByBoard | 看板全局筛选属性列表 | matched / read |
| `bi.get.report_findUserProfileIndex.cd897b95` | GET /report/findUserProfileIndex | 用户属性分析选择框 | matched / read |
| `bi.post.report_funnelAnalysis.741b386a` | POST /report/funnelAnalysis | 漏斗分析 | matched / read |
| `bi.post.report_retentionAnalysis.b88a0e54` | POST /report/retentionAnalysis | 留存分析 | matched / read |
| `bi.post.report_scatterAnalysis.a5cda4e7` | POST /report/scatterAnalysis | 分布分析 | matched / read |
| `bi.post.report_traceAnalysis.c1d50a0f` | POST /report/traceAnalysis | 路径分析 | matched / read |
| `bi.get.report_userDetail.c01360b7` | GET /report/userDetail | 用户详情-明细 | matched / read |
| `bi.post.report_userPropertyAnalysis.8fad057a` | POST /report/userPropertyAnalysis | 用户属性分析 | matched / read |
| `bi.post.report_v2_findProfilesByEvents.9e8ce207` | POST /report/v2/findProfilesByEvents | 分组、筛选属性列表-支持多个事件查询[最新，支持虚拟事件] | matched / read |
| `bi.post.report_v3_findProfilesByEvents.b5904bd7` | POST /report/v3/findProfilesByEvents | 条件标签筛选属性列表 | matched / read |

## 使用方式

每个接口的参数、返回声明及源码位置见 `references/api/<接口ID>.md`，或调用 SolarCatalog.describe。先检索再读取单个契约，不应一次读取所有接口。
