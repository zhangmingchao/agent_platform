// Pinia Store：集中管理跨页面需要共享的当前用户状态。
import { defineStore } from 'pinia'
import request from '../utils/request'

export const useUserStore = defineStore('user', {
  // 刷新页面后从 localStorage 恢复状态，避免用户被意外登出。
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('user') || ''
  }),
  actions: {
    // 调用登录接口，并同时更新内存状态和浏览器本地存储。
    async login(username, password) {
      const data = await request.post('/api/auth/login', { username, password })
      this.token = data.token
      this.username = data.username
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', data.username)
      return data
    },
    // 退出不依赖后端状态：清空 token 后，后续请求自然无法通过鉴权。
    logout() {
      this.token = ''
      this.username = ''
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
