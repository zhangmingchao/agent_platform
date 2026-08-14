<template>
  <div>
    <div class="page-header">
      <h2>Crew 管理</h2>
      <el-button type="primary" @click="$router.push('/crews/new')"><el-icon><Plus /></el-icon>创建 Crew</el-button>
    </div>
    <el-alert title="Crew 将多个 Agent 与 Task 组合成可执行团队，支持顺序执行和层级委派。" type="info" :closable="false" show-icon style="margin-bottom:16px" />
    <el-table :data="crews" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="description" label="描述" min-width="240" show-overflow-tooltip />
      <el-table-column label="执行方式" width="130"><template #default="{ row }"><el-tag>{{ row.process === 'hierarchical' ? '层级委派' : '顺序执行' }}</el-tag></template></el-table-column>
      <el-table-column prop="manager_name" label="Manager" width="160" show-overflow-tooltip />
      <el-table-column prop="agent_count" label="Agent" width="90" />
      <el-table-column prop="task_count" label="Task" width="90" />
      <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '停用' }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="230" fixed="right"><template #default="{ row }"><el-button type="primary" size="small" :disabled="!row.enabled" @click="$router.push(`/crews/${row.id}/chat`)">运行</el-button><el-button size="small" @click="$router.push(`/crews/${row.id}/edit`)">编辑</el-button><el-button type="danger" size="small" @click="remove(row)">删除</el-button></template></el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const crews = ref([])
const loading = ref(false)
const load = async () => { loading.value = true; try { crews.value = await request.get('/api/crews') } finally { loading.value = false } }
const remove = async row => {
  try { await ElMessageBox.confirm(`确定删除 Crew“${row.name}”吗？相关会话也会删除。`, '确认删除', { type: 'warning' }) } catch { return }
  await request.delete(`/api/crews/${row.id}`)
  ElMessage.success('已删除')
  await load()
}
onMounted(load)
</script>
