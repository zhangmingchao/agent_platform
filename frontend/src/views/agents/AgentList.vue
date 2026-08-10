<template>
  <div class="agent-list">
    <div class="page-header">
      <h2>Agent 管理</h2>
      <el-button type="primary" @click="$router.push('/agents/new')">
        <el-icon><Plus /></el-icon>
        创建 Agent
      </el-button>
    </div>

    <el-table :data="agents" v-loading="loading" stripe>
      <el-table-column label="名称" width="180">
        <template #default="{ row }">
          <InlineEdit :model-value="row.name" :maxlength="200" placeholder="未命名" @save="saveAgentField(row, 'name', $event)" />
        </template>
      </el-table-column>
      <el-table-column label="描述">
        <template #default="{ row }">
          <InlineEdit :model-value="row.description" placeholder="暂无描述" @save="saveAgentField(row, 'description', $event)" />
        </template>
      </el-table-column>
      <el-table-column prop="model" label="模型" width="160" />
      <el-table-column prop="temperature" label="温度" width="100" />
      <el-table-column prop="iteration_count" label="迭代次数" width="100" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="$router.push(`/agents/${row.id}/chat`)">
            <el-icon><ChatDotRound /></el-icon>
            对话
          </el-button>
          <el-button size="small" @click="$router.push(`/agents/${row.id}/edit`)">
            编辑
          </el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted,onActivated } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'
import InlineEdit from '../../components/InlineEdit.vue'

// 表格数据和加载状态。
const agents = ref([])
const loading = ref(false)

// 用于表格“创建时间”列的展示。
const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

// 从后端读取当前用户拥有的 Agent 列表。
const loadAgents = async () => {
  loading.value = true
  try {
    agents.value = await request.get('/api/agentsList')
  } finally {
    loading.value = false
  }
}

const handleDelete = async (row) => {
  // 二次确认，避免用户误删。
  await ElMessageBox.confirm(`确定删除 Agent "${row.name}" 吗？`, '确认删除', { type: 'warning' })
  // 删除成功后重新加载列表，保持界面与数据库一致。
  await request.delete(`/api/agents/${row.id}`)
  ElMessage.success('删除成功')
  loadAgents()
}

const saveAgentField = async (row, field, value) => {
  const originalValue = row[field] || ''
  if (field === 'name' && !value) {
    ElMessage.warning('Agent 名称不能为空')
    return
  }
  if (value === originalValue) return

  try {
    const detail = await request.get(`/api/agents/${row.id}`)
    const updated = await request.put(`/api/agents/${row.id}`, {
      name: field === 'name' ? value : detail.name,
      description: field === 'description' ? value : (detail.description || ''),
      system_prompt: detail.system_prompt || '',
      iteration_count: detail.iteration_count || 6,
      model: detail.model,
      temperature: detail.temperature,
      skill_ids: detail.skills?.map(skill => skill.id) || [],
      mcp_ids: detail.mcps?.map(mcp => mcp.id) || []
    })
    row.name = updated.name
    row.description = updated.description
    ElMessage.success(`${field === 'name' ? '名称' : '描述'}已保存`)
  } catch (e) { /* request 拦截器统一提示错误 */ }
}

// 页面首次挂载时自动加载表格数据。
onMounted(loadAgents)
</script>
