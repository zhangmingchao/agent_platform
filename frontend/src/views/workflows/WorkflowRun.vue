<template>
  <div class="workflow-run">
    <div class="page-header">
      <h2>{{ workflow?.name || '运行工作流' }}</h2>
      <div>
        <el-button @click="$router.push('/workflows')">返回列表</el-button>
        <el-button type="primary" @click="$router.push(`/workflows/${route.params.id}/edit`)">编辑</el-button>
      </div>
    </div>

    <div class="run-layout">
      <!-- 左侧：输入面板 -->
      <div class="run-input-panel">
        <div class="panel-title">任务输入</div>
        <el-input
          v-model="input"
          type="textarea"
          :rows="8"
          placeholder="输入要交给多 Agent 工作流处理的任务"
        />
        <div class="run-actions">
          <el-button type="primary" :loading="running" @click="handleRun">
            <el-icon><VideoPlay /></el-icon>
            运行工作流
          </el-button>
        </div>
        <el-divider />
        <div class="panel-title">工作流信息</div>
        <div class="workflow-desc">{{ workflow?.description || '暂无描述' }}</div>

        <template v-if="!isGraphWorkflow">
          <el-divider />
          <div class="panel-title">步骤列表</div>
          <div class="step-list">
            <div v-for="(step, index) in workflowSteps" :key="index" class="step-item">
              <div class="step-index">{{ index + 1 }}</div>
              <div class="step-content">
                <div class="step-role">{{ step.role || `Step ${index + 1}` }}</div>
                <div class="step-agent">{{ agentName(step.agent_id) }}</div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 中间：流程图（画布）或顺序输出 -->
      <div class="run-canvas-panel" v-if="isGraphWorkflow">
        <div class="canvas-header">
          <span class="canvas-title">执行流程图</span>
          <div class="legend">
            <span class="legend-item"><span class="dot pending"></span>等待</span>
            <span class="legend-item"><span class="dot running"></span>执行中</span>
            <span class="legend-item"><span class="dot success"></span>完成</span>
            <span class="legend-item"><span class="dot error"></span>失败</span>
          </div>
        </div>
        <div class="canvas-container">
          <VueFlow
            :nodes="flowNodes"
            :edges="flowEdges"
            :node-types="nodeTypes"
            :default-edge-options="{ type: 'smoothstep', animated: true }"
            :nodes-connectable="false"
            :nodes-draggable="false"
            :elements-selectable="true"
            fit-view-on-init
            @node-click="onNodeClick"
          >
            <Background pattern-color="#aaa" :gap="16" />
            <Controls :show-interactive="false" />
            <MiniMap />
          </VueFlow>
        </div>
      </div>

      <!-- 右侧：节点详情面板 -->
      <div class="run-detail-panel" v-if="isGraphWorkflow">
        <template v-if="selectedStep">
          <div class="panel-title">节点详情</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="节点">{{ selectedStep.role_name || selectedStep.node_id || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusType(selectedStep.status)" size="small">{{ selectedStep.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Agent">{{ agentName(selectedStep.agent_id) }}</el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ formatDate(selectedStep.started_at) }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{ formatDate(selectedStep.finished_at) }}</el-descriptions-item>
            <el-descriptions-item label="Trace" v-if="selectedStep.trace_run_id">
              <el-button type="primary" link size="small" @click="$router.push(`/traces?trace_id=${selectedStep.trace_run_id}`)">
                查看 Trace
              </el-button>
            </el-descriptions-item>
          </el-descriptions>
          <div v-if="selectedStep.instruction" class="detail-section">
            <div class="detail-label">指令</div>
            <pre class="result-text">{{ selectedStep.instruction }}</pre>
          </div>
          <div class="detail-section">
            <div class="detail-label">输入</div>
            <pre class="result-text">{{ selectedStep.input_text || '无' }}</pre>
          </div>
          <div class="detail-section">
            <div class="detail-label">输出</div>
            <pre class="result-text">{{ selectedStep.output_text || selectedStep.error_text || '无输出' }}</pre>
          </div>
        </template>
        <el-empty v-else description="点击流程图中的节点查看执行详情" :image-size="60" />
      </div>
    </div>

    <!-- 顺序步骤输出（非图工作流） -->
    <div class="seq-output" v-if="!isGraphWorkflow">
      <el-tabs v-model="activeTab" class="result-tabs">
        <el-tab-pane label="本次结果" name="current">
          <el-empty v-if="!currentRun" description="还没有运行结果" />
          <template v-else>
            <el-alert :title="runStatusTitle(currentRun.status)" :type="runStatusAlert(currentRun.status)" :closable="false" show-icon />

            <!-- 流式事件日志 -->
            <div class="result-section" v-if="currentRun.streamLogs && currentRun.streamLogs.length">
              <div class="section-title">执行日志</div>
              <div class="stream-log">
                <div v-for="(log, i) in currentRun.streamLogs" :key="i" class="log-item" :class="log.type">
                  <span class="log-time">{{ new Date(log.timestamp).toLocaleTimeString('zh-CN') }}</span>
                  <span class="log-text">{{ log.text }}</span>
                </div>
              </div>
            </div>

            <!-- 实时流式输出 -->
            <div class="result-section" v-if="currentRun.activeNodeId">
              <div class="section-title">实时输出 ({{ activeStepName }})</div>
              <pre class="result-text streaming">{{ activeStepOutput || '等待输出...' }}</pre>
            </div>

            <div class="result-section" v-if="currentRun.output || currentRun.output_text">
              <div class="section-title">最终输出</div>
              <pre class="result-text">{{ currentRun.output || currentRun.output_text }}</pre>
            </div>
            <div class="result-section" v-if="currentRun.error_text">
              <div class="section-title">错误信息</div>
              <pre class="result-text error">{{ currentRun.error_text }}</pre>
            </div>
            <div class="result-section">
              <div class="section-title">步骤输出</div>
              <el-collapse>
                <el-collapse-item
                  v-for="step in currentRun.steps || []"
                  :key="step.node_id || step.step_order"
                  :title="`${step.role_name || step.role || 'Step ' + step.step_order} [${step.status}]`"
                >
                  <div class="trace-link" v-if="step.trace_run_id">
                    <el-button type="primary" link @click="$router.push(`/traces?trace_id=${step.trace_run_id}`)">查看 Trace</el-button>
                  </div>
                  <pre class="result-text">{{ step.streamOutput || step.output_text || step.error_text || '无输出' }}</pre>
                </el-collapse-item>
              </el-collapse>
            </div>
          </template>
        </el-tab-pane>
        <el-tab-pane label="运行记录" name="runs">
          <el-table :data="runs" v-loading="runsLoading" stripe>
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
                <el-button type="primary" link @click="loadRunDetail(row.id)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 图工作流：流式输出 + 最终结果 + 运行记录 -->
    <div class="graph-output" v-if="isGraphWorkflow">
      <el-tabs v-model="activeTab" class="result-tabs">
        <el-tab-pane label="实时输出" name="current">
          <el-empty v-if="!currentRun" description="还没有运行结果" />
          <template v-else>
            <el-alert :title="runStatusTitle(currentRun.status)" :type="runStatusAlert(currentRun.status)" :closable="false" show-icon />

            <!-- Streaming event log -->
            <div class="result-section" v-if="currentRun.streamLogs && currentRun.streamLogs.length">
              <div class="section-title">执行日志</div>
              <div class="stream-log">
                <div v-for="(log, i) in currentRun.streamLogs" :key="i" class="log-item" :class="log.type">
                  <span class="log-time">{{ new Date(log.timestamp).toLocaleTimeString('zh-CN') }}</span>
                  <span class="log-text">{{ log.text }}</span>
                </div>
              </div>
            </div>

            <!-- 当前活动节点的实时流式输出 -->
            <div class="result-section" v-if="currentRun.activeNodeId">
              <div class="section-title">实时输出 ({{ activeStepName }})</div>
              <pre class="result-text streaming">{{ activeStepOutput || '等待输出...' }}</pre>
            </div>

            <!-- 最终输出 -->
            <div class="result-section" v-if="currentRun.output || currentRun.output_text">
              <div class="section-title">最终输出</div>
              <pre class="result-text">{{ currentRun.output || currentRun.output_text }}</pre>
            </div>
            <div class="result-section" v-if="currentRun.error_text">
              <div class="section-title">错误信息</div>
              <pre class="result-text error">{{ currentRun.error_text }}</pre>
            </div>

            <!-- 节点输出 -->
            <div class="result-section">
              <div class="section-title">节点输出</div>
              <el-collapse>
                <el-collapse-item
                  v-for="step in currentRun.steps || []"
                  :key="step.node_id || step.id || step.step_order"
                  :title="`${step.role_name || step.node_id || 'Step ' + step.step_order} [${step.status}]`"
                >
                  <div class="trace-link" v-if="step.trace_run_id">
                    <el-button type="primary" link @click="$router.push(`/traces?trace_id=${step.trace_run_id}`)">查看 Trace</el-button>
                  </div>
                  <pre class="result-text">{{ step.streamOutput || step.output_text || step.error_text || '无输出' }}</pre>
                </el-collapse-item>
              </el-collapse>
            </div>
          </template>
        </el-tab-pane>
        <el-tab-pane label="运行记录" name="runs">
          <el-table :data="runs" v-loading="runsLoading" stripe>
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
                <el-button type="primary" link @click="loadRunDetail(row.id)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-drawer v-model="detailVisible" title="运行详情" size="55%">
      <template v-if="runDetail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Run ID">{{ runDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusType(runDetail.status)">{{ runDetail.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDate(runDetail.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ formatDate(runDetail.finished_at) }}</el-descriptions-item>
        </el-descriptions>
        <div class="result-section">
          <div class="section-title">输入</div>
          <pre class="result-text">{{ runDetail.input_text }}</pre>
        </div>
        <div class="result-section">
          <div class="section-title">最终输出</div>
          <pre class="result-text">{{ runDetail.output_text || runDetail.error_text || '无输出' }}</pre>
        </div>
        <div class="result-section">
          <div class="section-title">步骤详情</div>
          <el-collapse>
            <el-collapse-item
              v-for="step in runDetail.steps || []"
              :key="step.id"
              :title="`Step ${step.step_order} · ${step.role_name || step.node_id || ''} · ${agentName(step.agent_id)}`"
            >
              <div class="step-detail-block">
                <div class="trace-link" v-if="step.trace_run_id">
                  <el-button type="primary" link @click="$router.push(`/traces?trace_id=${step.trace_run_id}`)">查看该步骤 Trace</el-button>
                </div>
                <div class="detail-label">步骤指令</div>
                <pre class="result-text">{{ step.instruction || '无' }}</pre>
                <div class="detail-label">输入</div>
                <pre class="result-text">{{ step.input_text || '无' }}</pre>
                <div class="detail-label">输出</div>
                <pre class="result-text">{{ step.output_text || step.error_text || '无输出' }}</pre>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, markRaw, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

import InputNode from './nodes/InputNode.vue'
import AgentNode from './nodes/AgentNode.vue'
import ConditionNode from './nodes/ConditionNode.vue'
import ParallelNode from './nodes/ParallelNode.vue'
import OutputNode from './nodes/OutputNode.vue'
import request from '../../utils/request'

const route = useRoute()
const workflow = ref(null)
const agents = ref([])
const input = ref('')
const running = ref(false)
const currentRun = ref(null)
const activeTab = ref('current')
const runs = ref([])
const runsLoading = ref(false)
const detailVisible = ref(false)
const runDetail = ref(null)
const streamController = ref(null)
const selectedNodeId = ref(null)

const nodeTypes = {
  input: markRaw(InputNode),
  agent: markRaw(AgentNode),
  condition: markRaw(ConditionNode),
  parallel: markRaw(ParallelNode),
  output: markRaw(OutputNode),
}

const isGraphWorkflow = computed(() => {
  const config = workflow.value?.config
  return !!(config && Array.isArray(config.nodes) && Array.isArray(config.edges))
})

const workflowSteps = computed(() => workflow.value?.config?.steps || [])

const flowEdges = computed(() => {
  const edges = workflow.value?.config?.edges || []
  const nodes = workflow.value?.config?.nodes || []
  const condNodes = {}
  for (const n of nodes) {
    if (n.type === 'condition') condNodes[n.id] = n.data?.conditions || []
  }
  return edges.map(e => {
    const sh = e.source_handle ?? e.sourceHandle ?? null
    const th = e.target_handle ?? e.targetHandle ?? null
    let label = ''
    if (sh && sh.startsWith('cond-')) {
      const idx = parseInt(sh.replace('cond-', ''))
      const conds = condNodes[e.source] || []
      if (conds[idx]) label = conds[idx].label || ''
    }
    return { ...e, sourceHandle: sh, targetHandle: th, type: 'smoothstep', animated: true, label }
  })
})

const flowNodes = computed(() => {
  const nodes = workflow.value?.config?.nodes || []
  const steps = currentRun.value?.steps || []
  const currentNodeId = currentRun.value?.current_node_id

  return nodes.map(n => {
    const step = steps.find(s => s.node_id === n.id)
    let status = 'pending'
    if (step) {
      status = step.status || 'pending'
    } else if (n.id === currentNodeId) {
      status = 'running'
    }
    return {
      ...n,
      class: `status-${status}`,
      data: { ...n.data, status },
    }
  })
})

const selectedStep = computed(() => {
  if (!selectedNodeId.value) return null
  const steps = currentRun.value?.steps || []
  return steps.find(s => s.node_id === selectedNodeId.value) || null
})

const activeStep = computed(() => {
  const nodeId = currentRun.value?.activeNodeId
  if (!nodeId) return null
  return currentRun.value?.steps?.find(s => s.node_id === nodeId) || null
})

const activeStepOutput = computed(() => activeStep.value?.streamOutput || '')
const activeStepName = computed(() => activeStep.value?.role_name || activeStep.value?.node_id || '')

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''
const statusType = (status) => status === 'success' ? 'success' : status === 'error' ? 'danger' : 'warning'
const runStatusTitle = (status) => status === 'success' ? '运行成功' : status === 'error' ? '运行失败' : '运行中'
const runStatusAlert = (status) => status === 'success' ? 'success' : status === 'error' ? 'error' : 'info'
const agentName = (agentId) => agents.value.find(a => a.id === agentId)?.name || (agentId ? `Agent #${agentId}` : '-')

const onNodeClick = ({ node }) => {
  selectedNodeId.value = node.id
}

const loadBaseData = async () => {
  const [workflowData, agentList] = await Promise.all([
    request.get(`/api/workflows/${route.params.id}`),
    request.get('/api/agentsList')
  ])
  workflow.value = workflowData
  agents.value = agentList
}

const loadRuns = async () => {
  runsLoading.value = true
  try {
    runs.value = await request.get(`/api/workflows/${route.params.id}/runs`)
  } finally {
    runsLoading.value = false
  }
}

const handleRun = async () => {
  if (!input.value.trim()) {
    ElMessage.warning('请输入任务内容')
    return
  }
  running.value = true
  selectedNodeId.value = null

  currentRun.value = {
    status: 'running',
    steps: [],
    streamLogs: [],
    activeNodeId: null,
    input: input.value,
    output: null,
  }
  activeTab.value = 'current'

  if (streamController.value) {
    streamController.value.abort()
  }
  const controller = new AbortController()
  streamController.value = controller
  const token = localStorage.getItem('token')

  try {
    const run = await request.post(`/api/workflows/${route.params.id}/run`, {
      input: input.value,
    })
    currentRun.value.run_id = run.run_id
    currentRun.value.workflow_id = run.workflow_id

    const response = await fetch(`/api/workflows/runs/${run.run_id}/events`, {
      method: 'GET',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      signal: controller.signal,
    })

    if (!response.ok || !response.body) {
      throw new Error('无法订阅工作流事件')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() || ''

      for (const rawEvent of events) {
        const lines = rawEvent.split('\n')
        const eventLine = lines.find(l => l.startsWith('event: '))
        const dataLine = lines.find(l => l.startsWith('data: '))
        if (!dataLine) continue
        const eventType = eventLine ? eventLine.slice(7).trim() : 'message'
        const payload = JSON.parse(dataLine.slice(6))
        handleStreamEvent(eventType, payload)
      }
    }
    loadRuns()
  } catch (e) {
    if (!controller.signal.aborted) {
      ElMessage.error(e.message || '工作流事件订阅失败')
      running.value = false
    }
  }
}

const handleStreamEvent = (eventType, data) => {
  const log = (type, nodeId, text) => {
    currentRun.value.streamLogs.push({ type, node_id: nodeId, text, timestamp: Date.now() })
  }

  switch (eventType) {
    case 'start':
      currentRun.value.run_id = data.run_id
      currentRun.value.workflow_id = data.workflow_id
      log('start', null, `运行 #${data.run_id} 已启动`)
      break

    case 'node_start': {
      currentRun.value.activeNodeId = data.node_id
      const existing = currentRun.value.steps.find(s => s.node_id === data.node_id)
      if (!existing) {
        currentRun.value.steps.push({
          node_id: data.node_id,
          node_type: data.node_type,
          role_name: data.label,
          step_order: data.step_order,
          status: 'running',
          streamOutput: '',
          output_text: '',
        })
      } else {
        existing.status = 'running'
      }
      log('node_start', data.node_id, `▶ ${data.label} 开始执行`)
      break
    }

    case 'token': {
      const step = currentRun.value.steps.find(s => s.node_id === data.node_id)
      if (step) {
        step.streamOutput += data.content
      }
      break
    }

    case 'node_done': {
      const step = currentRun.value.steps.find(s => s.node_id === data.node_id)
      if (step) {
        step.status = 'success'
        step.output_text = data.output
      }
      log('node_done', data.node_id, `✓ ${step?.role_name || data.node_id} 完成`)
      break
    }

    case 'branch':
      log('branch', data.node_id, `→ 条件分支: ${data.branch_label || '分支 ' + (data.branch_idx + 1)}`)
      break

    case 'parallel_start':
      log('parallel_start', data.node_id, `⚡ 并行执行 ${data.branch_count} 个分支`)
      break

    case 'parallel_done':
      log('parallel_done', data.node_id, `⚡ 并行执行完成，结果已合并`)
      break

    case 'tool_start':
      log('tool_start', data.node_id, `🔧 调用工具: ${data.tool}`)
      break

    case 'tool_end':
      log('tool_end', data.node_id, `🔧 工具 ${data.tool} 返回`)
      break

    case 'done':
      currentRun.value.status = 'success'
      currentRun.value.output = data.output
      currentRun.value.activeNodeId = null
      running.value = false
      log('done', null, '✅ 工作流执行完成')
      if (data.run_id) {
        request.get(`/api/workflows/runs/${data.run_id}`).then(run => {
          const savedLogs = currentRun.value.streamLogs
          const savedSteps = currentRun.value.steps
          currentRun.value = { ...run, streamLogs: savedLogs, steps: run.steps?.length ? run.steps : savedSteps }
        })
      }
      loadRuns()
      break

    case 'error':
      currentRun.value.status = 'error'
      currentRun.value.error_text = data.detail
      currentRun.value.activeNodeId = null
      running.value = false
      log('error', null, `❌ 执行失败: ${data.detail}`)
      loadRuns()
      break
  }
}

const loadRunDetail = async (runId) => {
  runDetail.value = await request.get(`/api/workflows/runs/${runId}`)
  detailVisible.value = true
}

onMounted(async () => {
  await loadBaseData()
  await loadRuns()
  if (route.query.run_id) {
    await loadRunDetail(route.query.run_id)
  }
})

onBeforeUnmount(() => {
  if (streamController.value) {
    streamController.value.abort()
  }
})
</script>

<style scoped>
.workflow-run { max-width: 1600px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.run-layout {
  display: grid;
  grid-template-columns: 300px 1fr 340px;
  gap: 16px;
  margin-bottom: 16px;
}
.run-input-panel,
.run-canvas-panel,
.run-detail-panel {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}
.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
.workflow-desc {
  color: #606266;
  line-height: 1.6;
  min-height: 24px;
  font-size: 13px;
}
.run-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
.canvas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.canvas-title {
  font-size: 16px;
  font-weight: 600;
}
.legend {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.dot.pending { background: #d1d5db; }
.dot.running { background: #f59e0b; animation: pulse-dot 1.5s infinite; }
.dot.success { background: #22c55e; }
.dot.error { background: #ef4444; }
@keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.canvas-container {
  position: relative;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  min-height: 500px;
  height: 500px;
}
.detail-section {
  margin-top: 12px;
}
.detail-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}
.result-text {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #303133;
  line-height: 1.6;
  max-height: 300px;
  overflow: auto;
  padding: 10px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
}
.result-text.error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #dc2626;
}
.step-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.step-item {
  display: flex;
  gap: 10px;
}
.step-index {
  align-items: center;
  background: #ecf5ff;
  border-radius: 50%;
  color: #409eff;
  display: flex;
  flex: 0 0 26px;
  font-size: 12px;
  font-weight: 600;
  height: 26px;
  justify-content: center;
}
.step-content { min-width: 0; }
.step-role { font-weight: 600; font-size: 14px; }
.step-agent { color: #606266; font-size: 12px; }
.trace-link {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
.result-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}
.result-section {
  margin-top: 16px;
}
.section-title {
  font-weight: 600;
  margin-bottom: 8px;
}
.step-detail-block {
  display: flex;
  flex-direction: column;
}
.seq-output, .graph-output {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}
.stream-log {
  background: #1e293b;
  border-radius: 6px;
  padding: 12px;
  max-height: 240px;
  overflow-y: auto;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.8;
}
.log-item {
  display: flex;
  gap: 8px;
  color: #cbd5e1;
}
.log-time {
  color: #64748b;
  flex-shrink: 0;
  font-size: 11px;
  padding-top: 1px;
}
.log-text {
  color: #e2e8f0;
}
.log-item.node_start .log-text { color: #60a5fa; }
.log-item.node_done .log-text { color: #4ade80; }
.log-item.branch .log-text { color: #fbbf24; }
.log-item.parallel_start .log-text { color: #a78bfa; }
.log-item.parallel_done .log-text { color: #a78bfa; }
.log-item.tool_start .log-text { color: #f97316; }
.log-item.tool_end .log-text { color: #f97316; }
.log-item.error .log-text { color: #f87171; }
.log-item.done .log-text { color: #4ade80; }
.result-text.streaming {
  border-color: #f59e0b;
  background: #fffbeb;
  min-height: 60px;
}
</style>

<style>
/* Vue Flow 节点状态样式（全局） */
.vf-node {
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 14px;
  min-width: 140px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transition: border-color 0.3s, box-shadow 0.3s;
}
.vf-node.input-node, .vf-node.output-node {
  background: #f0fdf4;
  border-color: #86efac;
}
.vf-node.agent-node {
  background: #eff6ff;
  border-color: #93c5fd;
}
.vf-node.condition-node {
  background: #fef3c7;
  border-color: #fcd34d;
}
.vf-node.parallel-node {
  background: #f5f3ff;
  border-color: #c4b5fd;
}
.node-header {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
}
.node-icon { font-size: 20px; margin-bottom: 4px; color: #6b7280; }
.node-label { font-size: 14px; font-weight: 600; color: #1f2937; }
.node-desc { font-size: 12px; color: #6b7280; margin-top: 2px; }
.node-branches { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.branch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: #fff;
  border-radius: 4px;
  font-size: 12px;
  position: relative;
}
.branch-label { font-weight: 500; color: #92400e; }
.branch-handle {
  width: 10px !important;
  height: 10px !important;
  background: #f59e0b !important;
  border: 2px solid #fff !important;
}
.vue-flow__node { cursor: pointer; }
.vue-flow__node.selected .vf-node {
  box-shadow: 0 0 0 2px #409eff, 0 8px 20px rgba(64,158,255,0.2);
}
.vue-flow__edge-path { stroke-width: 2; }
.vue-flow__edge.animated .vue-flow__edge-path { stroke-dasharray: 6; animation: dashmove 0.5s linear infinite; }
@keyframes dashmove { to { stroke-dashoffset: -6; } }
.vue-flow__edge-textwrapper { font-size: 11px; font-weight: 600; }
.vue-flow__edge-text { font-size: 11px; font-weight: 600; fill: #92400e; }

/* 节点状态颜色 */
.vue-flow__node.status-pending .vf-node {
  opacity: 0.5;
  border-color: #d1d5db;
}
.vue-flow__node.status-running .vf-node {
  border-color: #f59e0b;
  box-shadow: 0 0 0 2px #f59e0b, 0 4px 16px rgba(245,158,11,0.3);
  animation: node-pulse 1.5s ease-in-out infinite;
}
.vue-flow__node.status-success .vf-node {
  border-color: #22c55e;
  box-shadow: 0 0 0 2px #22c55e, 0 4px 12px rgba(34,197,94,0.2);
}
.vue-flow__node.status-error .vf-node {
  border-color: #ef4444;
  box-shadow: 0 0 0 2px #ef4444, 0 4px 12px rgba(239,68,68,0.2);
}
@keyframes node-pulse {
  0%, 100% { box-shadow: 0 0 0 2px #f59e0b, 0 4px 16px rgba(245,158,11,0.3); }
  50% { box-shadow: 0 0 0 4px #f59e0b, 0 4px 24px rgba(245,158,11,0.5); }
}
</style>
