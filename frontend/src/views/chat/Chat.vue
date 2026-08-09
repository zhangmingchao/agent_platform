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

            <div class="session-title">
              <div>{{ s.title || '新对话' }}</div>
              <div class="session-delete" @click.stop="deleteSession(s.id)"> 🗑️ 删除</div>
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
            <div class="message-text markdown-body streaming-content">
              <span v-html="renderMarkdown(streamingText)"></span><span class="cursor">|</span>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input" v-if="currentSessionId">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="3"
          placeholder="输入消息..."
          @keydown.enter.exact.prevent="sendMessage"
          :disabled="streaming"
        />
        <el-button type="primary" :loading="streaming" @click="sendMessage" style="margin-top: 8px">
          <el-icon><Promotion /></el-icon>
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'
import request from '../../utils/request'

// markdown-it 负责将 AI 返回的 Markdown 转为 HTML；禁止原始 HTML 避免直接注入。
const markdown = new MarkdownIt({
  breaks: true,
  html: false,
  linkify: true,
  typographer: true
})

// 用户消息不按 Markdown 解释，只转义为安全 HTML 并保留换行。
const escapeHtml = (content = '') => content
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#039;')
  .replaceAll('\n', '<br>')

// DOMPurify 在 v-html 渲染前清理危险标签和属性，防止 XSS。
const renderMarkdown = (content = '') => DOMPurify.sanitize(markdown.render(content))
const normalizeLegacyStreamMessage = (content = '') => {
  const fragments = content.split(/\n{2,}/).filter(Boolean)
  const shortFragments = fragments.filter(fragment => fragment.trim().length <= 8)

  // 兼容旧数据：旧后端曾将每段 SSE 的空行分隔符保存到数据库，
  // 导致 Markdown 把一个回答展示成很多很短的段落。
  if (fragments.length >= 5 && shortFragments.length / fragments.length >= 0.7) {
    return fragments.join('')
  }
  return content
}
const renderMessage = (message) => message.role === 'assistant'
  ? renderMarkdown(normalizeLegacyStreamMessage(message.content))
  : escapeHtml(message.content)

// 从 /agents/:id/chat 中取得当前要聊天的 Agent ID。
const route = useRoute()
const agentId = computed(() => route.params.id)

// 聊天页所有会变化的状态都放在 ref 中。
const agent = ref(null)
const sessions = ref([])
const currentSessionId = ref(null)
const messages = ref([])
const inputText = ref('')
const streaming = ref(false)
const streamingText = ref('')
const messagesContainer = ref(null)

const formatTime = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = async () => {
  // 等 Vue 先把新消息渲染到 DOM，再滚动到底部。
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const loadAgent = async () => {
  // 读取 Agent 信息，主要用于在侧边栏显示名称。
  agent.value = await request.get(`/api/agents/${agentId.value}`)
}

const loadSessions = async () => {
  // 当前接口返回当前登录用户的会话列表。
  sessions.value = await request.get('/api/sessions')
}

const selectSession = async (session) => {
  // 切换会话：记录会话 ID、获取历史消息并滚动到底部。
  currentSessionId.value = session.id
  messages.value = await request.get(`/api/sessions/${session.id}/messages`)
  scrollToBottom()
}

const createSession = async () => {
  // 创建的会话会绑定当前路由中的 Agent ID。
  const session = await request.post('/api/sessions', { agent_id: agentId.value })
  currentSessionId.value = session.session_id
  messages.value = []
  await loadSessions()
}

const sendMessage = async () => {
  // 空消息或正在生成回复时，不允许再次发送。
  const text = inputText.value.trim()
  if (!text || streaming.value) return

  if (!currentSessionId.value) {
    // 用户还没主动创建会话时，第一次发送消息会自动创建一个。
    await createSession()
  }

  // 先乐观地显示用户消息，不必等待后端响应。
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  streaming.value = true
  streamingText.value = ''

  try {
    // 流式接口使用 fetch，而不是 axios：fetch 可直接读取 response.body 的数据流。
    const token = localStorage.getItem('token')
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: text,
        session_id: currentSessionId.value
      })
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || `请求失败（${response.status}）`)
    }
    // reader 每次读取一小段服务端返回的 SSE 数据。
    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      // 网络分片可能截断在一行中间，因此保留最后一段不完整数据到下一轮。
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (line.startsWith('data:')) {
          const payload = line.slice(5)
          try {
            // 新协议将内容编码为单行 JSON，因此内容中的 \n 不会破坏 SSE 分帧。
            const event = JSON.parse(payload)
            if (event.type === 'done') {
              streaming.value = false
            } else if (event.type === 'chunk') {
              streamingText.value += event.content || ''
            }
          } catch (e) {
            // 兼容后端升级前的纯文本 SSE 格式。
            if (payload === '') streaming.value = false
            else streamingText.value += payload
          }
        }
      }
      scrollToBottom()
    }

    if (streamingText.value) {
      // 流结束后，将临时展示内容转成正式历史消息。
      messages.value.push({ role: 'assistant', content: streamingText.value })
    }
  } catch (e) {
    ElMessage.error(e.message || '对话请求失败')
  } finally {
    // 无论成功失败都恢复输入状态，并刷新会话标题和更新时间。
    streaming.value = false
    streamingText.value = ''
    loadSessions()
  }
}

// 进入聊天页：加载 Agent、会话列表，并默认打开第一条会话。
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
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
.chat-input {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  background: #fff;
}
/* 删除按钮默认隐藏，且不占空间 */
.session-delete {
  flex-shrink: 0;          /* 不被压缩 */
  margin-right: 8px;       /* 与内容保持间距 */
  opacity: 0;              /* 隐藏 */
  pointer-events: none;    /* 防止误触（但最好用 display:none） */
  transition: opacity 0.2s;
  color: #e74c3c;
  font-size: 14px;
}

/* hover 时显示删除按钮 */
.session-item:hover .session-delete {
  opacity: 1;
  pointer-events: auto;    /* 允许点击 */
}
</style>
