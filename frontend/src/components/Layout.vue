<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="logo" @click="toggleCollapse" style="cursor: pointer;">
        <el-icon :size="24"><Robot /></el-icon>
        <span v-show="!isCollapse">Agent Platform</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#1f2937"
        text-color="#9ca3af"
        :collapse="isCollapse"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/agents">
          <el-icon><User /></el-icon>
          <span>Agent 管理</span>
        </el-menu-item>
        <el-menu-item index="/workflows">
          <el-icon><Operation /></el-icon>
          <span>多 Agent 工作流</span>
        </el-menu-item>
        <el-menu-item index="/models">
          <el-icon><Coin /></el-icon>
          <span>模型管理</span>
        </el-menu-item>
        <el-menu-item index="/skills">
          <el-icon><Document /></el-icon>
          <span>Skill 管理</span>
        </el-menu-item>
        <el-menu-item index="/plugins">
          <el-icon><Box /></el-icon>
          <span>插件管理</span>
        </el-menu-item>
        <el-menu-item index="/mcps">
          <el-icon><Connection /></el-icon>
          <span>MCP 配置</span>
        </el-menu-item>
        <el-menu-item index="/traces">
          <el-icon><Share /></el-icon>
          <span>Trace 调用链</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="layout-header">
        <div class="header-title">{{ currentTitle }}</div>
        <div class="header-user">
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span class="username">{{ userStore.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
                <el-dropdown-item @click="showUpdatePassword = true">
                  <el-icon><Lock /></el-icon>
                  修改密码
                </el-dropdown-item>
                <el-dropdown-item @click="openApiKeyDialog">
                  <el-icon><Key /></el-icon>
                  API Key
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
  <el-dialog v-model="showUpdatePassword" title="修改密码" width="500">
    <el-form :model="updatePasswordForm" ref="updatePasswordFormRef" :rules="rules">
      <el-form-item label="旧密码" :label-width="formLabelWidth" prop="currentPassword">
        <el-input v-model="updatePasswordForm.currentPassword"  autocomplete="off" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码" :label-width="formLabelWidth" prop="newPassword">
        <el-input v-model="updatePasswordForm.newPassword"  autocomplete="off" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认密码" :label-width="formLabelWidth" prop="confirmPassword">
        <el-input v-model="updatePasswordForm.confirmPassword"  autocomplete="off" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="showUpdatePassword = false">取消</el-button>
        <el-button type="primary" @click="submitPassword" :loading="loading">
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>

  <el-dialog v-model="showApiKey" title="API Key" width="560px" @closed="issuedApiKey = ''">
    <div v-loading="apiKeyLoading" class="api-key-dialog">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="状态">
          <el-tag v-if="apiKeyStatus.configured" :type="apiKeyStatus.status === 'active' ? 'success' : 'info'">
            {{ apiKeyStatus.status === 'active' ? '有效' : '已吊销' }}
          </el-tag>
          <span v-else>尚未创建</span>
        </el-descriptions-item>
        <el-descriptions-item label="密钥标识">
          {{ apiKeyStatus.key_prefix ? `${apiKeyStatus.key_prefix}...` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="最后使用">
          {{ formatDate(apiKeyStatus.last_used_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="issuedApiKey" class="issued-key">
        <el-alert
          title="完整密钥只显示一次，请立即保存"
          type="warning"
          :closable="false"
          show-icon
        />
        <el-input :model-value="issuedApiKey" readonly>
          <template #append>
            <el-button title="复制 API Key" @click="copyApiKey">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer api-key-actions">
        <el-button
          v-if="apiKeyStatus.status === 'active'"
          type="danger"
          plain
          :loading="apiKeyLoading"
          @click="revokeCurrentApiKey"
        >
          吊销
        </el-button>
        <el-button type="primary" :loading="apiKeyLoading" @click="issueCurrentApiKey">
          <el-icon><Refresh /></el-icon>
          {{ apiKeyStatus.status === 'active' ? '重新生成' : '生成密钥' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import {computed, reactive, ref} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import request from '../utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => {
  if (route.path.startsWith('/workflows')) return '/workflows'
  if (route.path.startsWith('/agents')) return '/agents'
  return route.path
})
const currentTitle = computed(() => route.meta?.title || '')

const showUpdatePassword = ref(false)
const showApiKey = ref(false)
const formLabelWidth = '140px'
const loading = ref(false)
const apiKeyLoading = ref(false)
const issuedApiKey = ref('')
const apiKeyStatus = ref({ configured: false })
const isCollapse = ref(window.innerWidth < 768)
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const updatePasswordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const updatePasswordFormRef = ref()

const rules = {
  currentPassword:[
    {required: true,message:'请输入当前密码',trigger: 'blur'}
  ],
  newPassword:[
    {required: true,message:'请输入新密码',trigger: 'blur'},
    { min: 6, max: 20, message: '新密码长度必须为 6～20 位', trigger: 'blur' }
  ],
  confirmPassword:[
    {required: true,message:'请输入确认密码',trigger: 'blur'}
  ]
}

const formatDate = (value) => value ? new Date(value).toLocaleString('zh-CN') : '-'

const loadApiKeyStatus = async () => {
  apiKeyStatus.value = await request.get('/api/api-key')
}

const openApiKeyDialog = async () => {
  showApiKey.value = true
  issuedApiKey.value = ''
  apiKeyLoading.value = true
  try {
    await loadApiKeyStatus()
  } finally {
    apiKeyLoading.value = false
  }
}

const issueCurrentApiKey = async () => {
  if (apiKeyStatus.value.status === 'active') {
    try {
      await ElMessageBox.confirm(
        '重新生成后，旧 API Key 会立即失效。确认继续吗？',
        '重新生成 API Key',
        { type: 'warning', confirmButtonText: '确认生成', cancelButtonText: '取消' }
      )
    } catch (error) {
      return
    }
  }
  apiKeyLoading.value = true
  try {
    const result = await request.post('/api/api-key')
    issuedApiKey.value = result.api_key
    await loadApiKeyStatus()
    ElMessage.success('API Key 已生成')
  } finally {
    apiKeyLoading.value = false
  }
}

const copyApiKey = async () => {
  try {
    await navigator.clipboard.writeText(issuedApiKey.value)
    ElMessage.success('API Key 已复制')
  } catch (error) {
    ElMessage.error('复制失败，请手动选择密钥文本')
  }
}

const revokeCurrentApiKey = async () => {
  try {
    await ElMessageBox.confirm(
      '吊销后，使用当前 API Key 的后端请求会立即失败。',
      '吊销 API Key',
      { type: 'warning', confirmButtonText: '确认吊销', cancelButtonText: '取消' }
    )
  } catch (error) {
    return
  }
  apiKeyLoading.value = true
  try {
    await request.delete('/api/api-key')
    issuedApiKey.value = ''
    await loadApiKeyStatus()
    ElMessage.success('API Key 已吊销')
  } finally {
    apiKeyLoading.value = false
  }
}

const handleLogout = async () => {
  try {
    await request.post('/api/auth/logout')
  } catch (e) {
    // token 可能已过期，忽略
  }
  userStore.logout()
  router.push('/login')
}

const submitPassword = async () => {
  const valid = await updatePasswordFormRef.value.validate().catch(() => false)
  if (!valid) return

  if (updatePasswordForm.newPassword === updatePasswordForm.currentPassword) {
    ElMessage.warning('新密码不能与旧密码相同')
    return
  }
  if (updatePasswordForm.newPassword != updatePasswordForm.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  loading.value = true
  try {
    await request.put('/api/auth/password', {
      current_password: updatePasswordForm.currentPassword,
      new_password: updatePasswordForm.newPassword
    })
    // 从 Redis 删除 token
    try { await request.post('/api/auth/logout') } catch (e) {}
    userStore.logout()
    ElMessage.success('密码修改成功，请重新登录')
    showUpdatePassword.value = false
    router.push('/login')
  }catch (e) {
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.layout-container > .el-container { min-width: 0; }
.layout-aside {
  background-color: #1f2937;
  display: flex;
  flex-direction: column;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid #374151;
}
.layout-aside .el-menu {
  flex: 1;
  border-right: none;
}
.layout-header {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.header-title {
  font-size: 18px;
  font-weight: 600;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.username {
  font-size: 14px;
}
.layout-main {
  min-width: 0;
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.api-key-dialog {
  min-height: 150px;
}
.issued-key {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}
.api-key-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
@media (max-width: 760px) {
  .layout-main { padding: 12px; }
  .layout-header { padding: 0 12px; }
  .username { display: none; }
}
</style>
