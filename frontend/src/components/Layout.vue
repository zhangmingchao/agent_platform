<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="layout-aside">
      <div class="logo">
        <el-icon :size="24"><Robot /></el-icon>
        <span>Agent Platform</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#1f2937"
        text-color="#9ca3af"
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
        <el-menu-item index="/crews">
          <el-icon><UserFilled /></el-icon>
          <span>Crew 管理</span>
        </el-menu-item>
        <el-menu-item index="/flows">
          <el-icon><Operation /></el-icon>
          <span>Flow 编排</span>
        </el-menu-item>
        <el-menu-item index="/skills">
          <el-icon><Document /></el-icon>
          <span>Skill 管理</span>
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
</template>

<script setup>
// 登录后页面的通用布局逻辑：菜单高亮、标题和退出登录。
import {computed, reactive, ref} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import request from '../utils/request'
import {ElMessage} from "element-plus";


// route 读取当前地址；router 用于代码主动跳转。
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 菜单根据当前 URL 自动高亮；页面标题来自路由 meta.title。
const activeMenu = computed(() => {
  const section = route.path.split('/')[1]
  return section ? `/${section}` : '/dashboard'
})
const currentTitle = computed(() => route.meta?.title || '')

const showUpdatePassword = ref(false)
const formLabelWidth = '140px'
const loading = ref(false)

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

// 清空登录状态后跳转登录页。
const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}



const submitPassword = async () => {
  // 先校验表单
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
    userStore.logout()
    ElMessage.success('密码修改成功，请重新登录')
    showUpdatePassword.value = false
    userStore.logout()
    router.push('/login')
  }catch (e) {
    // Error handled by request interceptor
  } finally {
    loading.value = false
  }

}

</script>

<style scoped>
.layout-container {
  height: 100vh;
}
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
</style>
