/**
 * API service for communicating with backend
 */
import axios, { AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add request ID or auth token here if needed
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError) => {
    // Handle errors globally
    console.error('API Error:', error)
    
    let errorMessage = '请求失败，请稍后重试'
    
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      const data = error.response.data as any
      
      if (status === 400) {
        errorMessage = data?.detail || '请求参数错误'
      } else if (status === 404) {
        errorMessage = '请求的资源不存在'
      } else if (status === 500) {
        errorMessage = data?.detail || '服务器内部错误'
      } else if (status === 413) {
        errorMessage = '文件太大，请上传小于10MB的图片'
      } else {
        errorMessage = data?.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      // Request was made but no response received
      if (error.code === 'ECONNABORTED') {
        errorMessage = '请求超时，请检查网络连接'
      } else {
        errorMessage = '网络错误，请检查您的网络连接'
      }
    } else {
      // Something else happened
      errorMessage = error.message || '未知错误'
    }
    
    // Show error message
    ElMessage.error(errorMessage)
    
    return Promise.reject(error)
  }
)

export default apiClient
