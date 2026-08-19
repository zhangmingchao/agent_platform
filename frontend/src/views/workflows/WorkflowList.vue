<template>
  <div class="workflow-list">
    <div class="page-header">
      <h2>多 Agent 工作流</h2>
      <el-button type="primary" @click="$router.push('/workflows/new')">
        <el-icon><Plus /></el-icon>
        创建工作流
      </el-button>
    </div>

    <el-table :data="workflows" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="description" label="描述" min-width="240" show-overflow-tooltip />
      <el-table-column label="模式" width="120">
        <template #default="{ row }">
          <el-tag type="info">{{ modeLabel(row.mode) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="步骤数" width="90">
        <template #default="{ row }">{{ row.config?.steps?.length || 0 }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'warning'">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="180">
        <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="310" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="$router.push(`/workflows/${row.id}/run`)">
            <el-icon><VideoPlay /></el-icon>
            运行
          </el-button>
          <el-button size="small" @click="$router.push(`/workflows/${row.id}/edit`)">
            编辑
          </el-button>
          <el-button size="small" @click="openRuns(row)">
            记录
          </el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="runsDialogVisible" title="运行记录" width="900px">
      <el-table :data="runs" v-loading="runsLoading" stripe max-height="460">
        <el-table-column prop="id" label="Run ID" width="90" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="input_text" label="输入" min-width="220" show-overflow-tooltip />
        <el-table-column prop="output_text" label="输出" min-width="220" show-overflow-tooltip />
        <el-table-column prop="created_at" label="运行时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button type="primary" link @click="$router.push(`/workflows/${currentWorkflow?.id}/run?run_id=${row.id}`)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const workflows = ref([])
const loading = ref(false)
const runsDialogVisible = ref(false)
const runsLoading = ref(false)
const runs = ref([])
const currentWorkflow = ref(null)

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''
const modeLabel = (mode) => mode === 'sequential' ? '顺序执行' : mode
const statusType = (status) => status === 'success' ? 'success' : status === 'error' ? 'danger' : 'warning'

const loadWorkflows = async () => {
  loading.value = true
  try {
    workflows.value = await request.get('/api/workflows')
  } finally {
    loading.value = false
  }
}

const openRuns = async (workflow) => {
  currentWorkflow.value = workflow
  runsDialogVisible.value = true
  runsLoading.value = true
  try {
    runs.value = await request.get(`/api/workflows/${workflow.id}/runs`)
  } finally {
    runsLoading.value = false
  }
}

const handleDelete = async (workflow) => {
  await ElMessageBox.confirm(`确定删除工作流 "${workflow.name}" 吗？`, '确认删除', { type: 'warning' })
  await request.delete(`/api/workflows/${workflow.id}`)
  ElMessage.success('删除成功')
  loadWorkflows()
}

onMounted(loadWorkflows)
</script>
