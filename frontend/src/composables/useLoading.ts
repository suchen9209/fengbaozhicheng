/**
 * Composable for managing loading states
 */
import { ref } from 'vue'
import { ElLoading } from 'element-plus'

export const useLoading = () => {
  const isLoading = ref(false)
  let loadingInstance: any = null

  /**
   * Show full-screen loading overlay
   */
  const showLoading = (text: string = '加载中...') => {
    isLoading.value = true
    loadingInstance = ElLoading.service({
      lock: true,
      text,
      background: 'rgba(0, 0, 0, 0.7)'
    })
  }

  /**
   * Hide loading overlay
   */
  const hideLoading = () => {
    isLoading.value = false
    if (loadingInstance) {
      loadingInstance.close()
      loadingInstance = null
    }
  }

  /**
   * Execute async function with loading state
   */
  const withLoading = async <T>(
    fn: () => Promise<T>,
    loadingText?: string
  ): Promise<T> => {
    try {
      showLoading(loadingText)
      return await fn()
    } finally {
      hideLoading()
    }
  }

  return {
    isLoading,
    showLoading,
    hideLoading,
    withLoading
  }
}
