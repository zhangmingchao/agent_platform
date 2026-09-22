<template>
  <div class="chat-page">
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <h3>{{ agent?.name || '对话' }}</h3>
        <el-button size="small" @click="$router.push('/agents')">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>

      <div class="session-list">
        <div class="session-header">
          <span>会话列表</span>
          <el-button type="primary" size="small" @click="createSession">
            <el-icon><Plus /></el-icon>
            新会话
          </el-button>
        </div>
        <div class="session-items">
          <div
            v-for="s in sessions"
            :key="s.id"
            :class="['session-item', { active: s.id === currentSessionId }]"
            @click="selectSession(s)"
          >
            <div class="session-title-row">
              <div class="session-title">{{ s.title || '新对话' }}</div>
              <el-button
                class="session-delete"
                type="danger"
                link
                size="small"
                :disabled="streaming && s.id === currentSessionId"
                @click.stop="deleteSession(s)"
              >
                删除
              </el-button>
            </div>
            <div class="session-time">{{ formatTime(s.updated_at) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-main">
      <div class="chat-messages" ref="messagesContainer">
        <div v-if="!currentSessionId" class="empty-state">
          <el-icon :size="64" color="#d1d5db"><ChatDotRound /></el-icon>
          <p>选择或创建一个会话开始对话</p>
        </div>
        <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
          <div class="message-avatar">
            <el-avatar v-if="msg.role === 'user'" :icon="UserFilled" />
            <el-avatar v-else :icon="Robot" class="ai-avatar" />
          </div>
          <div class="message-content">
            <div class="message-role">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
            <div v-if="msg.role === 'assistant' && msg.task_plan" class="plan-panel completed">
              <div class="plan-header">
                <strong>{{ msg.task_plan.goal }}</strong>
                <el-tag size="small" :type="planStatusType(msg.task_plan.status)">
                  {{ planStatusText(msg.task_plan.status) }}
                </el-tag>
              </div>
              <div class="plan-steps">
                <div v-for="step in msg.task_plan.steps" :key="step.step_key" class="plan-step">
                  <span class="plan-step-marker" :class="`status-${step.status}`"></span>
                  <span class="plan-step-order">{{ step.order }}</span>
                  <span class="plan-step-title">{{ step.title }}</span>
                  <span class="plan-step-status">{{ planStepStatusText(step.status) }}</span>
                </div>
              </div>
            </div>
            <!-- 执行说明与正式回答分开存储，历史消息中默认折叠。 -->
            <div v-if="msg.role === 'assistant' && msg.reasoning_content" class="thinking-panel completed">
              <div class="panel-header" @click="msg.reasoningExpanded = !msg.reasoningExpanded">
                <div class="panel-title">
                  <el-icon class="thinking-icon"><MagicStick /></el-icon>
                  <span>查看思考过程</span>
                </div>
                <el-icon class="toggle-icon" :class="{ expanded: msg.reasoningExpanded }"><ArrowDown /></el-icon>
              </div>
              <div v-show="msg.reasoningExpanded" class="thinking-content markdown-body" v-html="renderMarkdown(msg.reasoning_content)"></div>
            </div>
            <!-- 用户消息的图片附件 -->
            <div v-if="msg.role === 'user' && messageImages(msg).length" class="msg-images">
              <img
                v-for="(img, i) in messageImages(msg)"
                :key="i"
                :src="img"
                class="msg-image"
                @click="previewImage(img)"
              />
            </div>
            <div v-if="msg.role === 'user' && messageFiles(msg).length" class="msg-files">
              <a
                v-for="file in messageFiles(msg)"
                :key="file.id"
                :href="`/api/runtime/files/${file.id}`"
                class="msg-file"
                @click.prevent="downloadRuntimeFile(file)"
              >{{ file.name }}</a>
            </div>
            <div
              :class="['message-text', { 'markdown-body': msg.role === 'assistant' }]"
              v-html="renderMessage(msg)"
            ></div>
            <pre v-if="msg.role === 'assistant' && msg.structured_content" class="structured-result">{{ formatStructured(msg.structured_content) }}</pre>
          </div>
        </div>

        <div v-if="pendingFiles.length > 0" class="file-preview-area">
          <div v-for="(file, i) in pendingFiles" :key="file.id" class="file-preview-item">
            <span>{{ file.name }}</span>
            <el-button link type="danger" @click="removeFile(i)">移除</el-button>
          </div>
        </div>
        <div v-if="streaming" class="message assistant">
          <div class="message-avatar">
            <el-avatar :icon="Robot" class="ai-avatar" />
          </div>
          <div class="message-content">
            <div v-if="taskPlan" class="plan-panel">
              <div class="plan-header">
                <strong>{{ taskPlan.goal }}</strong>
                <el-tag size="small" :type="planStatusType(taskPlan.status)">
                  {{ planStatusText(taskPlan.status) }}
                </el-tag>
              </div>
              <div class="plan-steps">
                <div v-for="step in taskPlan.steps" :key="step.step_key" class="plan-step">
                  <span class="plan-step-marker" :class="`status-${step.status}`"></span>
                  <span class="plan-step-order">{{ step.order }}</span>
                  <span class="plan-step-title">{{ step.title }}</span>
                  <span class="plan-step-status">{{ planStepStatusText(step.status) }}</span>
                </div>
              </div>
            </div>
            <!-- 思考过程面板 -->
            <div v-if="thinkingText || pendingText" class="thinking-panel">
              <div class="panel-header" @click="showThinking = !showThinking">
                <div class="panel-title">
                  <el-icon class="thinking-icon"><MagicStick /></el-icon>
                  <span>{{ pendingText ? '处理中' : '思考过程' }}</span>
                </div>
                <el-icon class="toggle-icon" :class="{ expanded: showThinking }"><ArrowDown /></el-icon>
              </div>
              <div v-show="showThinking" class="thinking-content markdown-body" v-html="renderMarkdown(thinkingText + pendingText)"></div>
            </div>
            <!-- 工具调用面板 -->
            <div v-if="toolCalls.length > 0" class="tool-calls-panel">
              <div v-for="tc in toolCalls" :key="tc.id" class="tool-call-item">
                <el-icon v-if="tc.status === 'running'"><Loading /></el-icon>
                <el-icon v-else><Check /></el-icon>
                <span class="tool-name">{{ tc.name }}</span>
                <span v-if="tc.input" class="tool-input">{{ tc.input }}</span>
              </div>
            </div>
            <!-- 最终回答 -->
            <div v-if="streamingText" class="message-text markdown-body streaming-content">
              <span v-html="renderMarkdown(streamingText)"></span><span class="cursor">|</span>
            </div>
            <pre v-if="structuredResult" class="structured-result">{{ formatStructured(structuredResult) }}</pre>
            <div v-else-if="toolCalls.length === 0 && !thinkingText" class="thinking-indicator">
              AI 思考中<span class="dots">...</span>
            </div>
            <el-button
              v-if="streaming"
              class="stop-btn"
              type="danger"
              size="small"
              plain
              @click="stopGenerate"
            >
              <el-icon><VideoPause /></el-icon>
              停止生成
            </el-button>
          </div>
        </div>
      </div>

      <div class="chat-input" v-if="currentSessionId">
        <!-- 图片预览区 -->
        <div v-if="pendingImages.length > 0" class="image-preview-area">
          <div v-for="(img, i) in pendingImages" :key="i" class="image-preview-item">
            <img :src="img" class="preview-thumb" />
            <el-button
              class="remove-image"
              type="danger"
              circle
              size="small"
              @click="removeImage(i)"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="input-row">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="3"
            placeholder="输入消息..."
            @keydown.enter.exact.prevent="sendMessage"
            @paste="handlePaste"
            :disabled="streaming"
          />
          <div class="input-actions">
            <el-upload
              :show-file-list="false"
              :before-upload="handleImageSelect"
              accept="image/*"
              :disabled="streaming || pendingImages.length >= 3"
            >
              <el-button :disabled="streaming || pendingImages.length >= 3" title="上传图片">
                <el-icon><Picture /></el-icon>
              </el-button>
            </el-upload>
            <el-upload
              :show-file-list="false"
              :before-upload="handleRuntimeFileSelect"
              accept=".csv,.xlsx,.xls,.docx,.pdf,.json,.md,.txt"
              :disabled="streaming || uploadingFile || pendingFiles.length >= 10"
            >
              <el-button :loading="uploadingFile" title="上传数据或文档">文件</el-button>
            </el-upload>
            <el-button type="primary" :loading="streaming" @click="sendMessage">
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </div>
        </div>
        <div class="input-hint">支持图片，以及 CSV、Excel、Word、PDF、JSON、Markdown 和文本文件</div>
      </div>
    </div>

    <aside v-if="currentSessionId" class="observer-panel">
      <div class="observer-header">
        <div>
          <h3>执行观察</h3>
          <p>{{ loopDebug.statusText }}</p>
        </div>
        <el-tag size="small" :type="loopDebug.tagType">{{ loopDebug.phaseLabel }}</el-tag>
      </div>

      <el-tabs v-model="observerTab" stretch>
        <el-tab-pane label="时间线" name="timeline">
          <div v-if="loopTimeline.length === 0" class="observer-empty">等待本轮执行事件</div>
          <div v-else class="timeline-list">
            <div
              v-for="event in loopTimeline"
              :key="event.local_id"
              class="timeline-item"
              :class="`phase-${event.phase_group}`"
            >
              <span class="timeline-dot"></span>
              <div class="timeline-body">
                <div class="timeline-title">
                  <span>{{ event.phase_label }}</span>
                  <small>{{ event.time_text }}</small>
                </div>
                <div class="timeline-meta">{{ event.detail }}</div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="Trace" name="trace">
          <div v-if="loopTraceSteps.length === 0" class="observer-empty">暂无步骤结构</div>
          <div v-else class="trace-tree">
            <div v-for="step in loopTraceSteps" :key="step.step_id" class="trace-step">
              <div class="trace-step-title">
                <span>Step {{ step.step_no }}</span>
                <small>{{ step.status }}</small>
              </div>
              <div class="trace-children">
                <div v-for="item in step.items" :key="item.local_id" class="trace-child">
                  <span class="trace-kind">{{ item.kind }}</span>
                  <span class="trace-name">{{ item.name || item.phase_label }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="调试" name="debug">
          <div class="debug-grid">
            <span>Phase</span><strong>{{ loopDebug.phase || '-' }}</strong>
            <span>Step</span><strong>{{ loopDebug.step_no || '-' }}</strong>
            <span>Tool</span><strong>{{ loopDebug.tool || '-' }}</strong>
            <span>Turn</span><strong>{{ loopDebug.turn_id || '-' }}</strong>
            <span>Run</span><strong>{{ loopDebug.run_id || '-' }}</strong>
          </div>
          <div class="debug-events">
            <div v-for="event in loopTimeline.slice(-8).reverse()" :key="`debug-${event.local_id}`">
              {{ event.phase }} · {{ event.name || event.detail }}
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </aside>

    <!-- 图片预览弹窗 -->
    <el-dialog v-model="imageViewerVisible" title="图片预览" width="auto" @close="imageViewerVisible = false">
      <img :src="viewerImage" style="max-width: 100%; max-height: 70vh; display: block; margin: 0 auto;" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPause, ArrowDown, MagicStick } from '@element-plus/icons-vue'
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import request from '../../utils/request'

const markdown = new MarkdownIt({
  breaks: true,
  html: false,
  linkify: true,
  typographer: true
})

const escapeHtml = (content = '') => content
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#039;')
  .replaceAll('\n', '<br>')

const renderMarkdown = (content = '') => DOMPurify.sanitize(markdown.render(content))
const normalizeLegacyStreamMessage = (content = '') => {
  const fragments = content.split(/\n{2,}/).filter(Boolean)
  const shortFragments = fragments.filter(fragment => fragment.trim().length <= 8)
  if (fragments.length >= 5 && shortFragments.length / fragments.length >= 0.7) {
    return fragments.join('')
  }
  return content
}

// 解析数据库中的 attachments 字段（可能是 JSON 字符串或列表）
const parseAttachments = (raw) => {
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  if (typeof raw === 'string') {
    try { return JSON.parse(raw) } catch { return [] }
  }
  return []
}

const renderMessage = (message) => {
  if (message.role === 'assistant') {
    return renderMarkdown(normalizeLegacyStreamMessage(message.content))
  }
  return escapeHtml(message.content)
}

const route = useRoute()
const agentId = computed(() => route.params.id)

const agent = ref(null)
const sessions = ref([])
const currentSessionId = ref(null)
const messages = ref([])
const inputText = ref('')
const streaming = ref(false)
const streamingText = ref('')
const structuredResult = ref(null)
const taskPlan = ref(null)
const thinkingText = ref('')
// 每个 LLM 轮次独立缓存；轮次完成前仅用于实时展示，不提前判定为正文。
const pendingRounds = ref({})
const pendingText = computed(() => Object.values(pendingRounds.value).join(''))
const showThinking = ref(true)
const toolCalls = ref([])
const messagesContainer = ref(null)
const pendingImages = ref([])
const pendingFiles = ref([])
const uploadingFile = ref(false)
const imageViewerVisible = ref(false)
const viewerImage = ref('')
const abortController = ref(null)
const observerTab = ref('timeline')
const loopTimeline = ref([])
const loopTraceSteps = computed(() => {
  const steps = []
  const byId = new Map()
  for (const event of loopTimeline.value) {
    if (!event.step_id) continue
    if (!byId.has(event.step_id)) {
      const step = {
        step_id: event.step_id,
        step_no: event.step_no,
        status: '运行中',
        items: []
      }
      byId.set(event.step_id, step)
      steps.push(step)
    }
    const step = byId.get(event.step_id)
    if (event.phase === 'step/end') {
      step.status = event.reason === 'turn_completed' ? '完成' : event.reason || '结束'
    }
    if (['llm/start', 'llm/end', 'tool/start', 'tool/end'].includes(event.phase)) {
      step.items.push(event)
    }
  }
  return steps
})
const loopDebug = computed(() => {
  const latest = loopTimeline.value[loopTimeline.value.length - 1]
  if (!latest) {
    return {
      phase: '',
      phaseLabel: '空闲',
      statusText: '当前没有运行中的观察数据',
      tagType: 'info',
      step_no: '',
      tool: '',
      turn_id: '',
      run_id: ''
    }
  }
  const isError = ['turn/error', 'turn/timeout'].includes(latest.phase)
  const isDone = latest.phase === 'turn/end'
  const currentTool = [...loopTimeline.value].reverse().find(item => item.phase === 'tool/start' || item.phase === 'tool/end')
  return {
    phase: latest.phase,
    phaseLabel: latest.phase_label,
    statusText: latest.detail || '正在执行',
    tagType: isError ? 'danger' : (isDone ? 'success' : 'primary'),
    step_no: latest.step_no,
    tool: currentTool?.name || '',
    turn_id: latest.turn_id,
    run_id: latest.run_id
  }
})

const phaseLabels = {
  'turn/start': '本轮开始',
  'step/start': '步骤开始',
  'llm/start': '模型开始',
  'llm/end': '模型结束',
  'tool/start': '工具开始',
  'tool/end': '工具结束',
  'step/end': '步骤结束',
  'turn/end': '本轮完成',
  'turn/error': '本轮失败',
  'turn/timeout': '本轮超时',
  'turn/cancelled': '本轮取消'
}

const phaseGroup = (phase = '') => {
  if (phase.startsWith('turn/')) return 'turn'
  if (phase.startsWith('step/')) return 'step'
  if (phase.startsWith('llm/')) return 'llm'
  if (phase.startsWith('tool/')) return 'tool'
  return 'other'
}

const loopEventDetail = (event) => {
  if (event.name) return event.name
  if (event.reason) return event.reason
  if (event.status) return event.status
  if (event.error) return event.error
  return event.step_no ? `Step ${event.step_no}` : ''
}

const appendLoopEvent = (event) => {
  const createdAt = new Date()
  loopTimeline.value.push({
    ...event,
    local_id: `${Date.now()}-${loopTimeline.value.length}`,
    phase_label: phaseLabels[event.phase] || event.phase,
    phase_group: phaseGroup(event.phase),
    detail: loopEventDetail(event),
    time_text: createdAt.toLocaleTimeString('zh-CN', { hour12: false }),
    created_at: createdAt
  })
}

const resetLoopObserver = () => {
  loopTimeline.value = []
  observerTab.value = 'timeline'
}

const formatTime = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatStructured = (value) => {
  if (!value) return ''
  if (typeof value === 'string') {
    try { return JSON.stringify(JSON.parse(value), null, 2) } catch { return value }
  }
  return JSON.stringify(value, null, 2)
}

const planStatusText = (status) => ({
  pending: '待执行', running: '执行中', completed: '已完成', failed: '失败'
}[status] || status)
const planStatusType = (status) => ({
  running: 'primary', completed: 'success', failed: 'danger'
}[status] || 'info')
const planStepStatusText = (status) => ({
  pending: '等待', running: '执行中', completed: '完成', failed: '失败', skipped: '跳过'
}[status] || status)

// 使用服务端返回的稳定 step_key 更新实时计划步骤。
const updateTaskPlanStep = (step) => {
  if (!taskPlan.value || !step) return
  const steps = taskPlan.value.steps || []
  const index = steps.findIndex(item => item.step_key === step.step_key)
  if (index >= 0) steps[index] = { ...steps[index], ...step }
  taskPlan.value = { ...taskPlan.value, steps: [...steps], status: step.status === 'failed' ? 'failed' : 'running' }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const loadAgent = async () => {
  agent.value = await request.get(`/api/agents/${agentId.value}`)
}

const loadSessions = async () => {
  sessions.value = await request.get('/api/sessions', {
    params: { agent_id: Number(agentId.value) }
  })
}

const selectSession = async (session) => {
  currentSessionId.value = session.id
  resetLoopObserver()
  const msgs = await request.get(`/api/sessions/${session.id}/messages`)
  // 解析每条消息的 attachments
  messages.value = msgs.map(m => ({
    ...m,
    attachments: parseAttachments(m.attachments),
    reasoningExpanded: false
  }))
  messages.value.unshift({"role":"assistant","content":"你好啊！请说出你的问题！","attachments":null})
  scrollToBottom()
}

const createSession = async () => {
  const session = await request.post('/api/sessions', { agent_id: agentId.value })
  currentSessionId.value = session.session_id
  resetLoopObserver()
  messages.value = [{"role":"assistant","content":"你好啊！请说出你的问题！","attachments":null}]
  await loadSessions()
}

const deleteSession = async (session) => {
  if (streaming.value && session.id === currentSessionId.value) {
    ElMessage.warning('当前会话正在生成回复，暂时不能删除')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定删除会话"${session.title || '新对话'}"吗？删除后无法恢复。`,
      '删除会话',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch (e) {
    return
  }
  await request.delete(`/api/sessions/${session.id}`)
  const deletingCurrent = session.id === currentSessionId.value
  await loadSessions()
  if (deletingCurrent) {
    currentSessionId.value = null
    messages.value = []
    streamingText.value = ''
    if (sessions.value.length > 0) await selectSession(sessions.value[0])
  }
  ElMessage.success('会话已删除')
}

// ── 图片处理 ─────────────────────────────────

const compressImage = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        const maxWidth = 1024
        const maxHeight = 1024
        let { width, height } = img
        if (width > maxWidth) {
          height = Math.round(height * maxWidth / width)
          width = maxWidth
        }
        if (height > maxHeight) {
          width = Math.round(width * maxHeight / height)
          height = maxHeight
        }
        canvas.width = width
        canvas.height = height
        ctx.drawImage(img, 0, 0, width, height)
        const dataUrl = canvas.toDataURL('image/jpeg', 0.85)
        resolve(dataUrl)
      }
      img.onerror = reject
      img.src = e.target.result
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const handleImageSelect = async (file) => {
  if (pendingImages.value.length >= 3) {
    ElMessage.warning('单次最多发送 3 张图片')
    return false
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning('单张图片不能超过 2MB')
    return false
  }
  try {
    const dataUrl = await compressImage(file)
    pendingImages.value.push(dataUrl)
  } catch {
    ElMessage.error('图片处理失败')
  }
  return false  // 阻止 el-upload 自动上传
}

const handlePaste = (e) => {
  const items = e.clipboardData?.items
  if (!items) return
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault()
      const file = item.getAsFile()
      if (file) {
        handleImageSelect(file)
      }
    }
  }
}

const removeImage = (index) => {
  pendingImages.value.splice(index, 1)
}

const previewImage = (url) => {
  viewerImage.value = url
  imageViewerVisible.value = true
}

// 返回消息中可用于预览的图片附件。
const messageImages = (message) => parseAttachments(message.attachments)
  .filter(item => typeof item === 'string' && item.startsWith('data:image/'))

// 返回消息中的 Runtime 文件附件。
const messageFiles = (message) => parseAttachments(message.attachments)
  .filter(item => item && typeof item === 'object' && item.kind === 'runtime_file')

// 上传普通文件并保存后端返回的逻辑文件 ID。
const handleRuntimeFileSelect = async (file) => {
  if (pendingFiles.value.length >= 10) {
    ElMessage.warning('单次最多使用 10 个文件')
    return false
  }
  const form = new FormData()
  form.append('file', file)
  if (currentSessionId.value) form.append('session_id', String(currentSessionId.value))
  uploadingFile.value = true
  try {
    const uploaded = await request.post('/api/runtime/files', form)
    pendingFiles.value.push(uploaded)
    ElMessage.success(`已上传 ${uploaded.name}`)
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || '文件上传失败')
  } finally {
    uploadingFile.value = false
  }
  return false
}

// 从待发送列表中移除文件，不删除服务端原文件。
const removeFile = (index) => {
  pendingFiles.value.splice(index, 1)
}

// 携带登录凭证下载 Runtime 文件，并在浏览器中保存。
const downloadRuntimeFile = async (file) => {
  try {
    const blob = await request.get(`/api/runtime/files/${file.id}`, { responseType: 'blob' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = file.name || 'runtime-file'
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('文件下载失败')
  }
}

// ── 发送消息 ─────────────────────────────────

const sendMessage = async () => {
  const text = inputText.value.trim()
  if ((!text && pendingImages.value.length === 0 && pendingFiles.value.length === 0) || streaming.value) return

  if (!currentSessionId.value) {
    await createSession()
  }

  // 本地先展示用户消息（含图片）
  const sentFiles = [...pendingFiles.value]
  const userMsg = {
    role: 'user',
    content: text || '(附件)',
    attachments: [...pendingImages.value, ...sentFiles]
  }
  messages.value.push(userMsg)
  inputText.value = ''
  const sentImages = [...pendingImages.value]
  pendingImages.value = []
  pendingFiles.value = []
  scrollToBottom()

  streaming.value = true
  resetLoopObserver()
  streamingText.value = ''
  structuredResult.value = null
  taskPlan.value = null
  thinkingText.value = ''
  pendingRounds.value = {}
  showThinking.value = true
  toolCalls.value = []
  abortController.value = new AbortController()

  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: text || '请描述这些图片',
        session_id: currentSessionId.value,
        images: sentImages.length ? sentImages : undefined,
        file_ids: sentFiles.length ? sentFiles.map(file => file.id) : undefined
      }),
      signal: abortController.value.signal
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      if (response.status === 429) {
        ElMessage.warning(error.detail || '该会话正在生成回复，请等待完成或点击停止生成')
      } else {
        throw new Error(error.detail || `请求失败（${response.status}）`)
      }
      return
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (line.startsWith('data:')) {
          const payload = line.slice(5)
          try {
            const event = JSON.parse(payload)
            if (event.type === 'done') {
              streaming.value = false
            } else if (event.type === 'llm_round_start') {
              pendingRounds.value[event.round_id] = ''
            } else if (event.type === 'pending_text_delta') {
              const roundId = event.round_id || 'unknown'
              pendingRounds.value[roundId] = (pendingRounds.value[roundId] || '') + (event.content || '')
            } else if (event.type === 'llm_round_classified') {
              const roundText = pendingRounds.value[event.round_id] || ''
              if (event.classification === 'answer') streamingText.value += roundText
              else thinkingText.value += roundText
              delete pendingRounds.value[event.round_id]
            } else if (event.type === 'structured_result') {
              try { structuredResult.value = JSON.parse(event.content) } catch { structuredResult.value = event.content }
            } else if (event.type === 'plan_created') {
              taskPlan.value = event.plan || null
            } else if (event.type === 'plan_step_started' || event.type === 'plan_step_completed' || event.type === 'plan_step_failed') {
              updateTaskPlanStep(event.step)
            } else if (event.type === 'plan_completed') {
              taskPlan.value = event.plan || taskPlan.value
            } else if (event.type === 'agent_loop_event') {
              appendLoopEvent(event)
            } else if (event.type === 'tool_started') {
              toolCalls.value.push({ id: event.tool_run_id, name: event.name, input: event.input || '', status: 'running' })
              scrollToBottom()
            } else if (event.type === 'tool_completed') {
              const toolCall = toolCalls.value.find(item => item.id === event.tool_run_id)
              if (toolCall) toolCall.status = 'done'
            } else if (event.type === 'error') {
              ElMessage.error(event.content || '对话错误')
            }
          } catch (e) {
            if (payload === '') streaming.value = false
            else streamingText.value += payload
          }
        }
      }
      scrollToBottom()
    }

    if (streamingText.value) {
      messages.value.push({ role: 'assistant', content: streamingText.value, reasoning_content: thinkingText.value || null, reasoningExpanded: false, structured_content: structuredResult.value, task_plan: taskPlan.value })
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      // 用户主动停止，保留已生成的内容
      if (streamingText.value) {
        messages.value.push({ role: 'assistant', content: streamingText.value, reasoning_content: thinkingText.value || null, reasoningExpanded: false, task_plan: taskPlan.value })
      }
    } else {
      ElMessage.error(e.message || '对话请求失败')
    }
  } finally {
    streaming.value = false
    streamingText.value = ''
    structuredResult.value = null
    taskPlan.value = null
    thinkingText.value = ''
    pendingRounds.value = {}
    toolCalls.value = []
    abortController.value = null
    loadSessions()
  }
}

const stopGenerate = () => {
  if (abortController.value) {
    abortController.value.abort()
  }
  streaming.value = false
  if (streamingText.value) {
    messages.value.push({ role: 'assistant', content: streamingText.value, reasoning_content: thinkingText.value || null, reasoningExpanded: false, task_plan: taskPlan.value })
  }
  streamingText.value = ''
  taskPlan.value = null
  thinkingText.value = ''
  pendingRounds.value = {}
  toolCalls.value = []
  appendLoopEvent({
    type: 'agent_loop_event',
    phase: 'turn/cancelled',
    turn_id: `session_${currentSessionId.value || 'unknown'}`,
    status: 'cancelled'
  })
}

onMounted(async () => {
  await loadAgent()
  await loadSessions()
  if (sessions.value.length > 0) {
    selectSession(sessions.value[0])
  }
})
</script>

<style scoped>
.structured-result {
  margin-top: 10px;
  padding: 10px;
  max-height: 320px;
  overflow: auto;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  background: #eff6ff;
  color: #1e3a8a;
  white-space: pre-wrap;
}
.chat-page {
  display: flex;
  height: calc(100vh - 120px);
  gap: 16px;
}
.chat-sidebar {
  width: 260px;
  background: #fff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
}
.session-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.session-header {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #6b7280;
}
.session-items {
  flex: 1;
  overflow-y: auto;
}
.session-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.15s;
}
.session-item:hover {
  background: #f9fafb;
}
.session-item.active {
  background: #eff6ff;
  border-left: 3px solid #409EFF;
}
.session-title {
  min-width: 0;
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.session-time {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}
.chat-main {
  flex: 1;
  min-width: 0;
  background: #fff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.observer-panel {
  width: 320px;
  min-width: 320px;
  background: #fff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.observer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px 10px;
  border-bottom: 1px solid #e5e7eb;
}
.observer-header h3 {
  margin: 0;
  font-size: 15px;
  color: #111827;
}
.observer-header p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}
.observer-panel :deep(.el-tabs) {
  min-height: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
}
.observer-panel :deep(.el-tabs__content) {
  min-height: 0;
  flex: 1;
  overflow: hidden;
}
.observer-panel :deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto;
  padding: 10px 12px 14px;
}
.observer-empty {
  padding: 18px 8px;
  color: #9ca3af;
  font-size: 13px;
  text-align: center;
}
.timeline-list {
  display: grid;
  gap: 10px;
}
.timeline-item {
  display: grid;
  grid-template-columns: 12px minmax(0, 1fr);
  gap: 8px;
  align-items: flex-start;
}
.timeline-dot {
  width: 9px;
  height: 9px;
  margin-top: 5px;
  border-radius: 50%;
  background: #9ca3af;
}
.phase-turn .timeline-dot { background: #2563eb; }
.phase-step .timeline-dot { background: #7c3aed; }
.phase-llm .timeline-dot { background: #0891b2; }
.phase-tool .timeline-dot { background: #16a34a; }
.timeline-body {
  min-width: 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #f3f4f6;
}
.timeline-title {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  color: #111827;
}
.timeline-title small {
  flex-shrink: 0;
  color: #9ca3af;
  font-size: 11px;
}
.timeline-meta {
  margin-top: 3px;
  color: #6b7280;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  overflow-wrap: anywhere;
}
.trace-tree {
  display: grid;
  gap: 10px;
}
.trace-step {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}
.trace-step-title {
  display: flex;
  justify-content: space-between;
  padding: 8px 10px;
  background: #f9fafb;
  font-size: 13px;
  color: #111827;
}
.trace-step-title small {
  color: #6b7280;
}
.trace-children {
  display: grid;
  gap: 6px;
  padding: 8px 10px 10px;
}
.trace-child {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  font-size: 12px;
}
.trace-kind {
  color: #2563eb;
  font-weight: 600;
  text-transform: uppercase;
}
.trace-name {
  min-width: 0;
  color: #4b5563;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.debug-grid {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 8px 10px;
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  font-size: 12px;
}
.debug-grid span {
  color: #6b7280;
}
.debug-grid strong {
  min-width: 0;
  color: #111827;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 500;
  overflow-wrap: anywhere;
}
.debug-events {
  display: grid;
  gap: 6px;
  margin-top: 12px;
  color: #4b5563;
  font-size: 12px;
  line-height: 1.4;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}
.empty-state p {
  margin-top: 12px;
}
.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.message.user {
  flex-direction: row-reverse;
}
.message-avatar {
  flex-shrink: 0;
}
.ai-avatar {
  background: #409EFF;
  color: #fff;
}
.message-content {
  max-width: 70%;
}
.message.user .message-content {
  text-align: right;
}
.message-role {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
}
.msg-images {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
  justify-content: flex-end;
}
.msg-image {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid #e5e7eb;
}
.msg-files {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: flex-end;
  margin-bottom: 6px;
}
.msg-file {
  padding: 5px 9px;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  background: #eff6ff;
  color: #2563eb;
  text-decoration: none;
}
.message-text {
  background: #f3f4f6;
  color: #111827;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
}
.message.user .message-text {
  background: #409EFF;
  color: #fff;
}
.tool-calls-panel {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  font-size: 12px;
}
.tool-call-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
  color: #0369a1;
}
.tool-name {
  font-family: ui-monospace, monospace;
  font-size: 12px;
}
.tool-input {
  font-family: ui-monospace, monospace;
  font-size: 11px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}
.plan-panel {
  margin-bottom: 10px;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
}
.plan-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  color: #1f2937;
  font-size: 13px;
}
.plan-header strong {
  min-width: 0;
  overflow-wrap: anywhere;
}
.plan-steps {
  display: grid;
  gap: 6px;
}
.plan-step {
  display: grid;
  grid-template-columns: 8px 20px minmax(0, 1fr) auto;
  align-items: center;
  gap: 6px;
  min-height: 24px;
  color: #4b5563;
  font-size: 12px;
}
.plan-step-marker {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
}
.plan-step-marker.status-running { background: #2563eb; }
.plan-step-marker.status-completed { background: #16a34a; }
.plan-step-marker.status-failed { background: #dc2626; }
.plan-step-marker.status-skipped { background: #d97706; }
.plan-step-order,
.plan-step-status { color: #6b7280; }
.plan-step-title {
  min-width: 0;
  overflow-wrap: anywhere;
}
.thinking-panel {
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 8px;
  overflow: hidden;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  background: #f9fafb;
  transition: background 0.15s;
}
.panel-header:hover {
  background: #f3f4f6;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}
.thinking-icon {
  color: #8b5cf6;
}
.toggle-icon {
  transition: transform 0.2s;
  color: #9ca3af;
  font-size: 12px;
}
.toggle-icon.expanded {
  transform: rotate(180deg);
}
.thinking-content {
  padding: 10px 12px;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
  max-height: 300px;
  overflow-y: auto;
  border-top: 1px solid #f0f0f0;
}
.thinking-indicator {
  color: #9ca3af;
  font-size: 14px;
  padding: 8px 0;
}
.dots {
  animation: dots 1.4s infinite;
}
@keyframes dots {
  0%, 20% { opacity: 0.2; }
  50% { opacity: 1; }
  100% { opacity: 0.2; }
}
.markdown-body :deep(> :first-child) {
  margin-top: 0;
}
.markdown-body :deep(> :last-child) {
  margin-bottom: 0;
}
.markdown-body :deep(p) {
  margin: 0 0 10px;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}
.markdown-body :deep(blockquote) {
  margin: 10px 0;
  padding: 4px 12px;
  color: #6b7280;
  border-left: 4px solid #d1d5db;
}
.markdown-body :deep(code) {
  padding: 2px 5px;
  border-radius: 4px;
  background: #e5e7eb;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.markdown-body :deep(pre) {
  overflow-x: auto;
  margin: 10px 0;
  padding: 12px;
  border-radius: 8px;
  background: #1f2937;
  color: #f9fafb;
}
.markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
  color: inherit;
}
.markdown-body :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}
.markdown-body :deep(table) {
  display: block;
  overflow-x: auto;
  max-width: 100%;
  border-collapse: collapse;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
}
.streaming-content > span:first-child {
  display: inline;
}
.cursor {
  animation: blink 0.8s infinite;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
.stop-btn {
  margin-top: 8px;
}
.chat-input {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  background: #fff;
}
.image-preview-area {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.file-preview-area {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}
.file-preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border: 1px solid #dbeafe;
  border-radius: 6px;
  background: #eff6ff;
  font-size: 12px;
}
.image-preview-item {
  position: relative;
  width: 80px;
  height: 80px;
}
.preview-thumb {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.remove-image {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  min-height: 20px;
  padding: 0;
  z-index: 1;
}
.input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.input-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.input-hint {
  margin-top: 6px;
  font-size: 11px;
  color: #9ca3af;
}
.session-delete {
  flex-shrink: 0;
  margin: 0;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s;
}
.session-item:hover .session-delete,
.session-delete:focus {
  opacity: 1;
  pointer-events: auto;
}
</style>
