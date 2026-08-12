// request 是所有“非流式”后端 API 的统一入口。
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建独立 Axios 实例，避免影响项目外的 Axios 默认配置。
const request = axios.create({
  baseURL: '',
  timeout: 30000
})

// 请求发出前自动携带登录 token，页面无需重复写 Authorization。
request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 统一拆出后端响应体，并集中处理接口错误。
request.interceptors.response.use(
  response => response.data, // 页面拿到的直接是后端 JSON 数据，而不是 Axios 完整响应对象。
  error => {
    const isLoginRequest = error.config?.url === '/api/auth/login'

    if (error.response?.status === 401 && !isLoginRequest) {
      // token 无效或过期：清理本地登录信息并跳回登录页。
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      ElMessage.error('登录已过期，请重新登录')
      window.location.href = '/login'
    } else {
      ElMessage.error(error.response?.data?.detail || '请求失败')
    }
    // 继续抛出错误，页面可以按需 catch 后做自己的补充处理。
    return Promise.reject(error)
  }
)

export default request
