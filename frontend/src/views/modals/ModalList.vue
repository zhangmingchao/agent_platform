<template>
  <div>
    <div class="page-header">
      <h2>模型管理</h2>
      <el-button type="primary" @click="$router.push('/modals/new')">
        <el-icon><Plus /></el-icon>
        创建模型
      </el-button>
    </div>
    <el-alert
      title="在此配置 Agent 可使用的 LLM 模型。Agent 表单的模型下拉会从已启用的模型中读取；未匹配时回退到全局 DeepSeek 配置。"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    />
    <el-table :data="modals" v-loading="loading" stripe>
      <el-table-column label="名称" width="180">
        <template #default="{ row }">
          <span>{{ row.name }}</span>
          <el-tag v-if="row.is_default" type="warning" size="small" style="margin-left: 6px">默认</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="model_key" label="模型标识" width="150" />
      <el-table-column prop="provider" label="提供商" width="140" />
      <el-table-column prop="model_name" label="模型名称" width="160" />
      <el-table-column prop="base_url" label="Base URL" min-width="200" show-overflow-tooltip />
      <el-table-column label="API Key" width="160">
        <template #default="{ row }">
          <span v-if="row.has_api_key">{{ row.api_key_masked }}</span>
          <el-tag v-else type="danger" size="small">未配置</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/modals/${row.id}/edit`)">编辑</el-button>
          <el-button type="success" size="small" :loading="testingId === row.id" @click="handleTest(row)">测试</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const modals = ref([])
const loading = ref(false)
const testingId = ref(null)

const load = async () => {
  loading.value = true
  try {
    modals.value = await request.get('/api/llm-models/list')
  } finally {
    loading.value = false
  }
}

const handleTest = async (row) => {
  testingId.value = row.id
  try {
    const res = await request.post(`/api/llm-models/${row.id}/test`)
    ElMessage.success(`连接成功，模型返回：${res.response || '(空)'}`)
  } catch (e) {
    // request 拦截器统一提示错误
  } finally {
    testingId.value = null
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除模型"${row.name}"吗？`, '确认删除', { type: 'warning' })
  await request.delete(`/api/llm-models/${row.id}`)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>
