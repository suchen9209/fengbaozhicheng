<template>
  <div class="upload-component">
    <el-upload
      ref="uploadRef"
      class="upload-area"
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      :before-upload="validateFile"
      :show-file-list="false"
      accept=".png,.jpg,.jpeg"
    >
      <el-icon class="upload-icon"><upload-filled /></el-icon>
      <div class="upload-text">
        <p>点击或拖拽截图到此处上传</p>
        <p class="upload-hint">支持 PNG、JPG、JPEG 格式，最大 10MB</p>
      </div>
    </el-upload>

    <div v-if="imagePreview" class="preview-section">
      <el-image :src="imagePreview" fit="contain" class="preview-image" />
      <div class="preview-actions">
        <el-button @click="clearImage" size="small">清除</el-button>
        <el-button type="primary" @click="confirmImage" size="small">
          确认并继续
        </el-button>
      </div>
    </div>

    <el-progress
      v-if="uploading"
      :percentage="uploadProgress"
      :status="uploadStatus"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import type { UploadFile, UploadInstance } from 'element-plus'

const emit = defineEmits<{
  (e: 'upload-success', imageUrl: string, file: File): void
  (e: 'upload-error', error: Error): void
}>()

const uploadRef = ref<UploadInstance>()
const imagePreview = ref<string>('')
const currentFile = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'success' | 'exception' | 'warning' | ''>('')

const acceptedFormats = ['image/png', 'image/jpeg', 'image/jpg']
const maxFileSize = 10 * 1024 * 1024 // 10MB

const validateFile = (file: File): boolean => {
  // Validate format
  if (!acceptedFormats.includes(file.type)) {
    ElMessage.error('仅支持PNG、JPG、JPEG格式')
    return false
  }

  // Validate size
  if (file.size > maxFileSize) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }

  return true
}

const handleFileChange = (uploadFile: UploadFile) => {
  if (!uploadFile.raw) return

  const file = uploadFile.raw

  if (!validateFile(file)) {
    return
  }

  // Create preview
  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target?.result as string
    currentFile.value = file
  }
  reader.readAsDataURL(file)
}

const clearImage = () => {
  imagePreview.value = ''
  currentFile.value = null
  uploadRef.value?.clearFiles()
}

const confirmImage = () => {
  if (!currentFile.value || !imagePreview.value) {
    ElMessage.warning('请先选择图片')
    return
  }

  emit('upload-success', imagePreview.value, currentFile.value)
}

const simulateUpload = () => {
  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = ''

  const interval = setInterval(() => {
    uploadProgress.value += 10
    if (uploadProgress.value >= 100) {
      clearInterval(interval)
      uploadStatus.value = 'success'
      setTimeout(() => {
        uploading.value = false
      }, 500)
    }
  }, 100)
}

defineExpose({
  clearImage,
  simulateUpload
})
</script>

<style scoped>
.upload-component {
  width: 100%;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-icon {
  font-size: 67px;
  color: #409eff;
  margin-bottom: 16px;
}

.upload-text {
  text-align: center;
}

.upload-text p {
  margin: 8px 0;
  color: #606266;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.preview-section {
  margin-top: 20px;
}

.preview-image {
  width: 100%;
  max-height: 400px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.preview-actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
