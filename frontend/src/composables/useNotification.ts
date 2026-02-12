/**
 * Composable for showing notifications
 */
import { ElMessage, ElNotification } from 'element-plus'

export const useNotification = () => {
  /**
   * Show success toast notification
   */
  const showSuccess = (message: string, duration: number = 3000) => {
    ElMessage({
      message,
      type: 'success',
      duration,
      showClose: true
    })
  }

  /**
   * Show error toast notification
   */
  const showError = (message: string, duration: number = 3000) => {
    ElMessage({
      message,
      type: 'error',
      duration,
      showClose: true
    })
  }

  /**
   * Show warning toast notification
   */
  const showWarning = (message: string, duration: number = 3000) => {
    ElMessage({
      message,
      type: 'warning',
      duration,
      showClose: true
    })
  }

  /**
   * Show info toast notification
   */
  const showInfo = (message: string, duration: number = 3000) => {
    ElMessage({
      message,
      type: 'info',
      duration,
      showClose: true
    })
  }

  /**
   * Show detailed notification with title
   */
  const showNotification = (
    title: string,
    message: string,
    type: 'success' | 'warning' | 'info' | 'error' = 'info',
    duration: number = 4500
  ) => {
    ElNotification({
      title,
      message,
      type,
      duration,
      position: 'top-right'
    })
  }

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showNotification
  }
}
