<template>
  <div class="register-page">
    <div class="register-card">
      <h1>{{ t('register.title') }}</h1>
      <el-form ref="registerFormRef" :model="registerForm" :rules="rules" @submit.prevent="handleRegister">
        <el-form-item prop="username">
          <el-input v-model="registerForm.username" :placeholder="t('login.username')" :prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="registerForm.password" type="password" :placeholder="t('login.password')" :prefix-icon="Lock" size="large" show-password />
        </el-form-item>
        <el-button class="register-button" type="primary" @click="handleRegister" :loading="loading">
          注册
        </el-button>
      </el-form>
      <el-button link type="primary" @click="router.push('/login')">
        {{ t('register.backToLogin') }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {reactive, ref} from "vue";
import {ElMessage} from "element-plus";
import request from "../utils/request";

const router = useRouter()
const { t } = useI18n()

const registerForm = reactive({username:'',password:''})
const registerFormRef = ref()
const loading = ref(false)

const rules = {
  username: [
      { required: true, message: t('login.usernameRequired'), trigger: 'blur' }
  ],
  password: [
      { required: true, message: t('login.passwordRequired'), trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度必须为 6～20 位', trigger: 'blur' }
  ]
}

const handleRegister = async() => {
  loading.value = true
  try {
    await request.post('/api/auth/register', {
      username: registerForm.username,
      password: registerForm.password
    })
    ElMessage.success('注册成功！')
    router.push('/login')
  }catch (e) {

  }finally {
    loading.value = false
  }

}

</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 380px;
  padding: 40px;
  text-align: center;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.register-card h1 {
  margin: 0 0 20px;
  font-size: 24px;
}
</style>
