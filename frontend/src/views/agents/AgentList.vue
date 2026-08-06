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
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="model" label="模型" width="160" />
      <el-table-column prop="temperature" label="温度" width="100" />
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

const agents = ref([])
const loading = ref(false)

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const loadAgents = async () => {
  loading.value = true
  try {
    agents.value = await request.get('/api/agentsList')
  } finally {
    loading.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除 Agent "${row.name}" 吗？`, '确认删除', { type: 'warning' })
  await request.delete(`/api/agents/${row.id}`)
  ElMessage.success('删除成功')
  loadAgents()
}

onMounted(loadAgents)
</script>