<template>
  <div class="trace-page">
    <div class="page-header">
      <h2>Trace 调用链</h2>
      <el-button :loading="loading" @click="loadTraces">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-table :data="traces" v-loading="loading" stripe @row-click="openTrace">
      <el-table-column prop="id" label="Trace ID" width="100" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="agent_name" label="Agent" width="160" show-overflow-tooltip />
      <el-table-column prop="session_title" label="会话" width="180" show-overflow-tooltip />
      <el-table-column label="工作流" width="220" show-overflow-tooltip>
        <template #default="{ row }">
          <span v-if="row.workflow_name">
            {{ row.workflow_name }} / Run #{{ row.workflow_run_id }} / Step {{ row.step_order }}
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="input_text" label="用户输入" min-width="260" show-overflow-tooltip />
      <el-table-column prop="model" label="模型" width="150" />
      <el-table-column prop="span_count" label="节点" width="80" />
      <el-table-column label="耗时" width="100">
        <template #default="{ row }">{{ formatDuration(row.duration_ms) }}</template>
      </el-table-column>
      <el-table-column label="开始时间" width="180">
        <template #default="{ row }">{{ formatDate(row.started_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click.stop="openTrace(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="drawerVisible" :title="`Trace #${currentTrace?.id || ''}`" size="70%">
      <div v-loading="detailLoading" class="trace-detail">
        <template v-if="currentTrace">
          <el-descriptions :column="3" border class="trace-summary">
            <el-descriptions-item label="状态">
              <el-tag :type="statusType(currentTrace.status)" size="small">
                {{ statusText(currentTrace.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Agent">{{ currentTrace.agent_name }}</el-descriptions-item>
            <el-descriptions-item label="模型">{{ currentTrace.model }}</el-descriptions-item>
            <el-descriptions-item label="会话">{{ currentTrace.session_title }}</el-descriptions-item>
            <el-descriptions-item label="工作流">
              <span v-if="currentTrace.workflow_name">
                {{ currentTrace.workflow_name }} / Run #{{ currentTrace.workflow_run_id }} / Step {{ currentTrace.step_order }}
              </span>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="总耗时">{{ formatDuration(currentTrace.duration_ms) }}</el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ formatDate(currentTrace.started_at) }}</el-descriptions-item>
          </el-descriptions>

          <section class="trace-io">
            <h4>用户输入</h4>
            <pre>{{ currentTrace.input_text }}</pre>
          </section>

          <h3 class="chain-title">调用链</h3>
          <el-timeline>
            <el-timeline-item
              v-for="span in currentTrace.spans"
              :key="span.id"
              :type="statusType(span.status)"
              :timestamp="`${formatDate(span.started_at)} · ${formatDuration(span.duration_ms)}`"
              placement="top"
            >
              <el-card shadow="never" class="span-card">
                <div class="span-header">
                  <div>
                    <el-tag size="small" effect="plain">{{ spanTypeText(span.span_type) }}</el-tag>
                    <strong>{{ span.name }}</strong>
                    <span v-if="span.round_no" class="round-label">第 {{ span.round_no }} 轮</span>
                  </div>
                  <el-tag :type="statusType(span.status)" size="small">{{ statusText(span.status) }}</el-tag>
                </div>
                <el-collapse v-if="span.input_data || span.output_data || span.error_text">
                  <el-collapse-item v-if="span.input_data" title="输入" name="input">
                    <pre class="json-content">{{ pretty(span.input_data) }}</pre>
                  </el-collapse-item>
                  <el-collapse-item v-if="span.output_data" title="输出" name="output">
                    <pre class="json-content">{{ pretty(span.output_data) }}</pre>
                  </el-collapse-item>
                  <el-collapse-item v-if="span.error_text" title="错误" name="error">
                    <pre class="error-content">{{ span.error_text }}</pre>
                  </el-collapse-item>
                </el-collapse>
              </el-card>
            </el-timeline-item>
          </el-timeline>

          <section v-if="currentTrace.output_text" class="trace-io">
            <h4>最终输出</h4>
            <pre>{{ currentTrace.output_text }}</pre>
          </section>
          <el-alert
            v-if="currentTrace.error_text"
            type="error"
            :title="currentTrace.error_text"
            :closable="false"
            show-icon
          />
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import request from '../../utils/request'

const route = useRoute()
const traces = ref([])
const loading = ref(false)
const drawerVisible = ref(false)
const detailLoading = ref(false)
const currentTrace = ref(null)

const statusType = (status) => ({
  success: 'success', ok: 'success', error: 'danger', cancelled: 'warning', running: 'primary'
}[status] || 'info')
const statusText = (status) => ({
  success: '成功', ok: '成功', error: '失败', cancelled: '已取消', running: '运行中'
}[status] || status)
const spanTypeText = (type) => ({ llm: 'LLM', tool: '工具', setup: '准备' }[type] || type)
const formatDuration = (ms = 0) => ms >= 1000 ? `${(ms / 1000).toFixed(2)} s` : `${ms || 0} ms`
const formatDate = (date) => date ? new Date(date).toLocaleString('zh-CN') : '-'
const pretty = (value) => {
  if (!value) return ''
  try { return JSON.stringify(JSON.parse(value), null, 2) } catch (e) { return value }
}

const loadTraces = async () => {
  loading.value = true
  try {
    traces.value = await request.get('/api/traces', { params: { limit: 200, _t: Date.now() } })
  } finally {
    loading.value = false
  }
}

const openTrace = async (row) => {
  drawerVisible.value = true
  detailLoading.value = true
  currentTrace.value = null
  try {
    currentTrace.value = await request.get(`/api/traces/${row.id}`)
  } finally {
    detailLoading.value = false
  }
}

onMounted(async () => {
  await loadTraces()
  const traceId = Number(route.query.trace_id)
  if (traceId) {
    await openTrace({ id: traceId })
  }
})
</script>

<style scoped>
.trace-page :deep(.el-table__row) { cursor: pointer; }
.trace-summary { margin-bottom: 20px; }
.trace-io { margin: 18px 0; }
.trace-io h4, .chain-title { margin: 0 0 10px; }
.trace-io pre, .json-content, .error-content {
  max-height: 360px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border-radius: 6px;
  background: #f5f7fa;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.55;
}
.error-content { background: #fef0f0; color: #c45656; }
.span-card { border-color: #e5e7eb; }
.span-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.span-header strong { margin-left: 8px; }
.round-label { margin-left: 8px; color: #909399; font-size: 12px; }
.span-card :deep(.el-collapse) { margin-top: 12px; border-bottom: none; }
</style>
