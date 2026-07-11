import axios from 'axios'
import { useUserStore } from '@/stores/user'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 30000,
})

api.interceptors.request.use(config => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

api.interceptors.response.use(
  response => {
    const { code, message, data } = response.data
    if (code !== 0 && code !== undefined) {
      if (code === 'E1004') {
        useUserStore().logout()
        window.location.href = '/login'
      }
      return Promise.reject(new Error(message || '请求失败'))
    }
    return data
  },
  error => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('请求超时，请重试'))
    }
    if (!error.response) {
      return Promise.reject(new Error('网络异常，请检查网络连接'))
    }
    if (error.response.status === 401) {
      useUserStore().logout()
      window.location.href = '/login'
    }
    // 提取后端返回的错误详情
    const detail = error.response?.data?.detail
    return Promise.reject(detail ? new Error(detail) : error)
  }
)

export default api
