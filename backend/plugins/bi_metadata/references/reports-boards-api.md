# reports-boards 接口参考

自动对照前后端源码生成。目录状态不等于线上验证；调用前使用 `SolarCatalog` 的 describe 获取完整契约。

| 接口 ID | 方法与路径 | 用途 | 状态 / 操作 |
|---|---|---|---|
| `bi.get.boardCollaborator_detail.29f9423a` | GET /boardCollaborator/detail | 查询协作者 | backend_only / read |
| `bi.post.boardCollaborator_save.9443a96d` | POST /boardCollaborator/save | 保存协作者 | backend_only / write |
| `bi.get.boardConfig_getByBoardId.9b0b6ce8` | GET /boardConfig/getByBoardId | 保存配置 | backend_only / read |
| `bi.get.boardConfig_refresh.5378b8e0` | GET /boardConfig/refresh | 获取配置 | matched / write |
| `bi.post.boardConfig_save.0fbf67b8` | POST /boardConfig/save | #endregion 看板设置 | matched / write |
| `bi.post.boardFiltrate_add.e71ca093` | POST /boardFiltrate/add | 列表 | matched / write |
| `bi.get.boardFiltrate_delete.478b42b5` | GET /boardFiltrate/delete | 详情 | matched / write |
| `bi.get.boardFiltrate_detail.2b002e2b` | GET /boardFiltrate/detail | 设置/取消默认 | matched / read |
| `bi.get.boardFiltrate_list.3cf36573` | GET /boardFiltrate/list | list | matched / read |
| `bi.get.boardFiltrate_setDefault.8715535a` | GET /boardFiltrate/setDefault | 修改名称 | matched / write |
| `bi.get.boardFiltrate_updateNameById.590c603c` | GET /boardFiltrate/updateNameById | 新增 | matched / write |
| `bi.get.boardLog_list.b6e9ef19` | GET /boardLog/list | 日志列表 | matched / read |
| `bi.post.boardMenu_batchDelByIds.9613bac2` | POST /boardMenu/batchDelByIds | 批量删除看板 | backend_only / write |
| `bi.post.boardMenu_batchOrder.9ed8e5cb` | POST /boardMenu/batchOrder | 批量排序接口 | matched / write |
| `bi.post.boardMenu_copyBoard.fef70be8` | POST /boardMenu/copyBoard | 复制接口 | matched / write |
| `bi.post.boardMenu_createBoard.63fae0ec` | POST /boardMenu/createBoard | 创建看板 | matched / write |
| `bi.get.boardMenu_createFolder.164ed95a` | GET /boardMenu/createFolder | 创建文件夹 | matched / write |
| `bi.get.boardMenu_findBoardReportContentById.0a65cf26` | GET /boardMenu/findBoardReportContentById | 获取看板的内容 | matched / read |
| `bi.post.boardMenu_findPermList.6ab6ec88` | POST /boardMenu/findPermList | findPermList | backend_only / read |
| `bi.post.boardMenu_findSearchContentByReportIds.15926c5e` | POST /boardMenu/findSearchContentByReportIds | 批量获取报表的搜索条件 | backend_only / read |
| `bi.get.boardMenu_getBoardInfoById.2338436b` | GET /boardMenu/getBoardInfoById | 修改看板-数据回显接口 | matched / read |
| `bi.get.boardMenu_getCopyBoardName.222f58d6` | GET /boardMenu/getCopyBoardName | 获取复制之后的看板名称 | backend_only / read |
| `bi.get.boardMenu_handleBoardMenuData.97407799` | GET /boardMenu/handleBoardMenuData | V2版本看板的账户可见授权-数据处理 | backend_only / write |
| `bi.get.boardMenu_menuList.bd89cfb2` | GET /boardMenu/menuList | 看板列表 | matched / read |
| `bi.get.boardMenu_recycleBinMenu.fb4e60f3` | GET /boardMenu/recycleBinMenu | 获取回收站中数据 | matched / write |
| `bi.get.boardMenu_saveLog.dee0330d` | GET /boardMenu/saveLog | 记录看板操作 | matched / write |
| `bi.get.boardMenu_templateBoardList.ace6d644` | GET /boardMenu/templateBoardList | 模板下看板列表 | matched / write |
| `bi.post.boardMenu_transferReport.c0366697` | POST /boardMenu/transferReport | transferReport | backend_only / read |
| `bi.post.boardMenu_updBoardContent.c57124e3` | POST /boardMenu/updBoardContent | 更新看板的内容/(保存) | matched / write |
| `bi.get.boardMenu_updMenuName.941c187c` | GET /boardMenu/updMenuName | 修改文件夹/看板名称 | matched / write |
| `bi.get.boardMenu_updMenuStatusById.1e9a68bf` | GET /boardMenu/updMenuStatusById | 修改看板状态 | backend_only / write |
| `bi.post.boardMenu_updReportInfoById.c00829e9` | POST /boardMenu/updReportInfoById | 修改看板 | matched / write |
| `bi.get.boardMenu_updateDefault.1f1fd4c2` | GET /boardMenu/updateDefault | 设置/删除默认看板 | matched / write |
| `bi.get.boardMenu_verifyName.fa0b582f` | GET /boardMenu/verifyName | 验证看板名称是否重复 | backend_only / read |
| `bi.post.boardReport_delReport.b5c78991` | POST /boardReport/delReport | 删除看板中的报表 | backend_only / write |
| `bi.post.groupTemplate_add.c8425ae0` | POST /groupTemplate/add | 新增模板 | matched / write |
| `bi.get.groupTemplate_checkTemplateUpdate.df1c8bf5` | GET /groupTemplate/checkTemplateUpdate | 检查模板是否需要更新.true:需要;false:不需要 | backend_only / read |
| `bi.post.groupTemplate_delete.bb4fb3bc` | POST /groupTemplate/delete | 删除模板 | matched / write |
| `bi.get.groupTemplate_detail.57c67b8b` | GET /groupTemplate/detail | 模板详情 | matched / read |
| `bi.post.groupTemplate_editInfo.c5f9b8e7` | POST /groupTemplate/editInfo | 编辑模板 | matched / write |
| `bi.get.groupTemplate_ignoreRelationBoard.247a7523` | GET /groupTemplate/ignoreRelationBoard | 更新关联看板-忽略 | matched / write |
| `bi.get.groupTemplate_list.30b56b1d` | GET /groupTemplate/list | 获取模板列表 | backend_only / read |
| `bi.get.groupTemplate_listPage.cc808649` | GET /groupTemplate/listPage | 获取模板列表 分页查询 | matched / read |
| `bi.post.groupTemplate_newVersion_ignore.94a8ead8` | POST /groupTemplate/newVersion/ignore | 模板同步-忽略 | matched / write |
| `bi.post.groupTemplate_newVersion_sync.f111c46e` | POST /groupTemplate/newVersion/sync | 模板同步-更新 | matched / write |
| `bi.get.groupTemplate_notifySourceBoardUpdateByTenantId.a928173c` | GET /groupTemplate/notifySourceBoardUpdateByTenantId | 根据租户通知源模板更新 | backend_only / internal |
| `bi.post.groupTemplate_templateCreateBoard.b91b9453` | POST /groupTemplate/templateCreateBoard | 模板创建看板-单个 | matched / write |
| `bi.post.groupTemplate_templateCreateBoardBatch.7b56608e` | POST /groupTemplate/templateCreateBoardBatch | 模板创建看板-批量 | matched / write |
| `bi.get.groupTemplate_updRelationBoard.f31be1be` | GET /groupTemplate/updRelationBoard | 更新关联看板-更新 | matched / write |
| `bi.post.groupTemplate_verifyBatch.04f6675f` | POST /groupTemplate/verifyBatch | 模板创建看板-批量校验接口 | matched / read |
| `bi.post.groupTemplate_verifyTemp.c26a1b00` | POST /groupTemplate/verifyTemp | 模板创建看板-校验接口 | matched / read |
| `bi.get.groupTemplateRelation_checkRelationBoardUpdate.2a47c1fe` | GET /groupTemplateRelation/checkRelationBoardUpdate | 检查关联看板是否需要更新.true:需要;false:不需要 | backend_only / read |
| `bi.post.groupTemplateRelation_list.f711ee1b` | POST /groupTemplateRelation/list | 模板关联看板列表 | matched / read |
| `bi.get.health_baseBoard.48e57109` | GET /health/baseBoard | baseBoard | backend_only / internal |
| `bi.get.reportForm_batchDelByIds.6e61e35e` | GET /reportForm/batchDelByIds | 批量删除看板 | backend_only / write |
| `bi.post.reportForm_copyReport.c3d1d808` | POST /reportForm/copyReport | 复制接口 | matched / read |
| `bi.post.reportForm_delById.67a943a1` | POST /reportForm/delById | 删除 | matched / write |
| `bi.get.reportForm_deleteReportFormsByAnalysisBodyId.39e84339` | GET /reportForm/deleteReportFormsByAnalysisBodyId | 删除主体关联报表 | frontend_only / unverified |
| `bi.post.reportForm_findList.f46424f3` | POST /reportForm/findList | 列表查询接口 | matched / read |
| `bi.post.reportForm_findPermList.44b80eeb` | POST /reportForm/findPermList | findPermList | backend_only / read |
| `bi.get.reportForm_getCopyReportName.69c7681c` | GET /reportForm/getCopyReportName | 获取复制之后的报表名称 | backend_only / read |
| `bi.get.reportForm_getReportInfoById.b5c7459c` | GET /reportForm/getReportInfoById | 报表详情 | matched / read |
| `bi.post.reportForm_getReportInfoById.db9f04f8` | POST /reportForm/getReportInfoById | 详情 / | frontend_only / unverified |
| `bi.get.reportForm_getReportListByAnalysisBodyId.4c27da4c` | GET /reportForm/getReportListByAnalysisBodyId | 获取主体关联报表 | frontend_only / unverified |
| `bi.post.reportForm_refreshRbac.c057dcc0` | POST /reportForm/refreshRbac | refreshRbac | backend_only / write |
| `bi.post.reportForm_saveReportForm.5611165f` | POST /reportForm/saveReportForm | 保存报表 | matched / write |
| `bi.post.reportForm_transferReport.3fda2bcf` | POST /reportForm/transferReport | transferReport | backend_only / read |
| `bi.post.reportForm_updMenuName.99f17820` | POST /reportForm/updMenuName | 修改菜单名称 | matched / write |
| `bi.get.reportForm_verifyName.853da7ae` | GET /reportForm/verifyName | 验证看板名称是否重复 | backend_only / read |

## 使用方式

每个接口的参数、返回声明及源码位置见 `references/api/<接口ID>.md`，或调用 SolarCatalog.describe。先检索再读取单个契约，不应一次读取所有接口。
