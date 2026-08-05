import { defineStore } from 'pinia'
import request from '../utils/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('user') || ''
  }),
  actions: {
    async login(username, password) {
      const data = await request.post('/api/auth/login', { username, password })
      this.token = data.token
      this.username = data.username
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', data.username)
      return data
    },
    logout() {
      this.token = ''
      this.username = ''
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})