<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="40" color="#409EFF"><Robot /></el-icon>
        <h1>{{ t('login.title') }}</h1>
        <p>{{ t('login.subtitle') }}</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" :placeholder="t('login.username')" :prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" :placeholder="t('login.password')" :prefix-icon="Lock" size="large" show-password />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width: 100%">
          {{ t('login.loginBtn') }}
        </el-button>
        <el-button class="register-button" link type="primary" @click="router.push('/register')" >
          {{ t('login.registerBtn') }}
        </el-button>
        <div class="login-footer">
          <span>{{ t('login.defaultAccount') }}</span>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '../stores/user'

// t 用于通过语言包 key 获取当前语言的文案。
const { t } = useI18n()
const router = useRouter()
// Pinia store 统一封装登录、token 和用户信息的处理。
const userStore = useUserStore()

// 表单组件实例，用于调用 Element Plus 的 validate() 校验方法。
const formRef = ref()
const loading = ref(false)
// reactive 适合响应式对象；输入框通过 v-model 双向绑定这些字段。
const form = reactive({ username: '', password: '' })
// rules 会传给 el-form，在提交前进行必填校验。
const rules = {
  username: [{ required: true, message: t('login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('login.passwordRequired'), trigger: 'blur' }]
}

const handleLogin = async () => {
  // 没有通过校验时 validate 会抛错，后续登录请求不会执行。
  await formRef.value.validate()
  loading.value = true
  try {
    // Store 内部请求登录接口，并将返回 token 保存到 localStorage。
    await userStore.login(form.username, form.password)
    ElMessage.success(t('login.loginSuccess'))
    router.push('/')
  } catch (e) {
    // 错误提示由 request 响应拦截器统一处理。
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  width: 380px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
.login-header {
  text-align: center;
  margin-bottom: 30px;
}
.login-header h1 {
  margin: 10px 0 5px;
  font-size: 24px;
}
.login-header p {
  color: #9ca3af;
  margin: 0;
}
.login-footer {
  text-align: center;
  margin-top: 16px;
  color: #9ca3af;
  font-size: 12px;
}
.register-button {
  display: flex;
  margin: 12px auto 0;
}
</style>
