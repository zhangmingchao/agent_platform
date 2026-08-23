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
            <!-- 用户消息的图片附件 -->
            <div v-if="msg.role === 'user' && msg.attachments && msg.attachments.length" class="msg-images">
              <img
                v-for="(img, i) in msg.attachments"
                :key="i"
                :src="img"
                class="msg-image"
                @click="previewImage(img)"
              />
            </div>
            <div
              :class="['message-text', { 'markdown-body': msg.role === 'assistant' }]"
              v-html="renderMessage(msg)"
            ></div>
          </div>
        </div>
        <div v-if="streaming" class="message assistant">
          <div class="message-avatar">
            <el-avatar :icon="Robot" class="ai-avatar" />
          </div>
          <div class="message-content">
            <div v-if="toolCalls.length > 0" class="tool-calls-panel">
              <div v-for="(tc, i) in toolCalls" :key="i" class="tool-call-item">
                <el-icon v-if="tc.status === 'running'"><Loading /></el-icon>
                <el-icon v-else><Check /></el-icon>
                <span class="tool-name">{{ tc.name }}</span>
              </div>
            </div>
            <div v-if="streamingText" class="message-text markdown-body streaming-content">
              <span v-html="renderMarkdown(streamingText)"></span><span class="cursor">|</span>
            </div>
            <div v-else-if="toolCalls.length === 0" class="thinking-indicator">
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
            <el-button type="primary" :loading="streaming" @click="sendMessage">
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
          </div>
        </div>
        <div class="input-hint">支持粘贴图片，单次最多 3 张，单张不超过 2MB</div>
      </div>
    </div>

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
import { VideoPause } from '@element-plus/icons-vue'
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
const toolCalls = ref([])
const messagesContainer = ref(null)
const pendingImages = ref([])
const imageViewerVisible = ref(false)
const viewerImage = ref('')
const abortController = ref(null)

const formatTime = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit' })
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
  const msgs = await request.get(`/api/sessions/${session.id}/messages`)
  // 解析每条消息的 attachments
  messages.value = msgs.map(m => ({
    ...m,
    attachments: parseAttachments(m.attachments)
  }))
  messages.value.unshift({"role":"assistant","content":"你好啊！请说出你的问题！","attachments":null})
  scrollToBottom()
}

const createSession = async () => {
  const session = await request.post('/api/sessions', { agent_id: agentId.value })
  currentSessionId.value = session.session_id
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

// ── 发送消息 ─────────────────────────────────

const sendMessage = async () => {
  const text = inputText.value.trim()
  if ((!text && pendingImages.value.length === 0) || streaming.value) return

  if (!currentSessionId.value) {
    await createSession()
  }

  // 本地先展示用户消息（含图片）
  const userMsg = {
    role: 'user',
    content: text || '(图片)',
    attachments: pendingImages.value.length ? [...pendingImages.value] : undefined
  }
  messages.value.push(userMsg)
  inputText.value = ''
  const sentImages = [...pendingImages.value]
  pendingImages.value = []
  scrollToBottom()

  streaming.value = true
  streamingText.value = ''
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
        images: sentImages.length ? sentImages : undefined
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
            } else if (event.type === 'chunk') {
              streamingText.value += event.content || ''
            } else if (event.type === 'tool_start') {
              toolCalls.value.push({ name: event.content, status: 'running' })
              scrollToBottom()
            } else if (event.type === 'tool_end') {
              if (toolCalls.value.length > 0) {
                toolCalls.value[toolCalls.value.length - 1].status = 'done'
              }
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
      messages.value.push({ role: 'assistant', content: streamingText.value })
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      // 用户主动停止，保留已生成的内容
      if (streamingText.value) {
        messages.value.push({ role: 'assistant', content: streamingText.value })
      }
    } else {
      ElMessage.error(e.message || '对话请求失败')
    }
  } finally {
    streaming.value = false
    streamingText.value = ''
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
    messages.value.push({ role: 'assistant', content: streamingText.value })
  }
  streamingText.value = ''
  toolCalls.value = []
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
  background: #fff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
.message-text {
  background: #f3f4f6;
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
