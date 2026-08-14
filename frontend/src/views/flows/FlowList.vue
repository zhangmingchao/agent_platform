<template>
  <div>
    <div class="page-header"><h2>Flow 编排</h2><el-button type="primary" @click="$router.push('/flows/new')"><el-icon><Plus /></el-icon>创建 Flow</el-button></div>
    <el-alert title="Flow 按有向图串联 Crew、条件、人工审批、数据转换和结束节点。" type="info" :closable="false" show-icon style="margin-bottom:16px" />
    <el-table :data="flows" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="description" label="描述" min-width="260" show-overflow-tooltip />
      <el-table-column prop="node_count" label="节点数" width="100" />
      <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '停用' }}</el-tag></template></el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="180"><template #default="{ row }">{{ formatDate(row.updated_at) }}</template></el-table-column>
      <el-table-column label="操作" width="230" fixed="right"><template #default="{ row }"><el-button type="primary" size="small" :disabled="!row.enabled" @click="$router.push(`/flows/${row.id}/chat`)">运行</el-button><el-button size="small" @click="$router.push(`/flows/${row.id}/edit`)">编辑</el-button><el-button type="danger" size="small" @click="remove(row)">删除</el-button></template></el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'
const flows = ref([]), loading = ref(false)
const formatDate = value => value ? new Date(value).toLocaleString('zh-CN') : '-'
const load = async () => { loading.value = true; try { flows.value = await request.get('/api/flows') } finally { loading.value = false } }
const remove = async row => { try { await ElMessageBox.confirm(`确定删除 Flow“${row.name}”吗？相关会话也会删除。`, '确认删除', { type: 'warning' }) } catch { return }; await request.delete(`/api/flows/${row.id}`); ElMessage.success('已删除'); await load() }
onMounted(load)
</script>
