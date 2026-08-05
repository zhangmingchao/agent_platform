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
            <div class="session-title">{{ s.title || '新对话' }}</div>
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
            <div class="message-text">{{ msg.content }}</div>
          </div>
        </div>
        <div v-if="streaming" class="message assistant">
          <div class="message-avatar">
            <el-avatar :icon="Robot" class="ai-avatar" />
          </div>
          <div class="message-content">
            <div class="message-text">{{ streamingText }}<span class="cursor">|</span></div>
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
import request from '../../utils/request'

const route = useRoute()
const agentId = computed(() => route.params.id)

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
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const loadAgent = async () => {
  agent.value = await request.get(`/api/agents/${agentId.value}`)
}

const loadSessions = async () => {
  sessions.value = await request.get('/api/sessions')
}

const selectSession = async (session) => {
  currentSessionId.value = session.id
  messages.value = await request.get(`/api/sessions/${session.id}/messages`)
  scrollToBottom()
}

const createSession = async () => {
  const session = await request.post('/api/sessions', { agent_id: agentId.value })
  currentSessionId.value = session.session_id
  messages.value = []
  await loadSessions()
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || streaming.value) return

  if (!currentSessionId.value) {
    await createSession()
  }

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  streaming.value = true
  streamingText.value = ''

  try {
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
          const chunk = line.slice(5)
          if (chunk === '') {
            streaming.value = false
          } else {
            streamingText.value += chunk
          }
        }
      }
      scrollToBottom()
    }

    if (streamingText.value) {
      messages.value.push({ role: 'assistant', content: streamingText.value })
    }
  } catch (e) {
    ElMessage.error(e.message || '对话请求失败')
  } finally {
    streaming.value = false
    streamingText.value = ''
    loadSessions()
  }
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
  white-space: pre-wrap;
  word-break: break-word;
}
.message.user .message-text {
  background: #409EFF;
  color: #fff;
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
</style>
