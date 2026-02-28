<template>
  <div class="analyze">
    <el-container>
      <el-header>
        <h1>蓝图分析</h1>
      </el-header>

      <el-main>
        <el-steps :active="currentStep" align-center finish-status="success">
          <el-step title="上传截图" />
          <el-step title="选择策略" />
          <el-step title="确认识别" />
          <el-step title="查看推荐" />
        </el-steps>

        <div class="content-area">
          <!-- Step 1: Upload -->
          <div v-show="currentStep === 0" class="step-content">
            <upload-component
              ref="uploadRef"
              @upload-success="handleUploadSuccess"
              @upload-error="handleUploadError"
            />
          </div>

          <!-- Step 2: Strategy Selection -->
          <div v-show="currentStep === 1" class="step-content">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>选择运营策略和事件</span>
                  <el-button type="text" @click="currentStep = 0">返回</el-button>
                </div>
              </template>
              
              <div class="strategy-section">
                <h4>📊 运营方向</h4>
                <p class="hint-text">选择你当前的发展重点（可选）</p>
                <el-radio-group v-model="selectedStrategy" size="large">
                  <el-radio-button 
                    v-for="strategy in strategies" 
                    :key="strategy.type"
                    :label="strategy.type"
                  >
                    {{ strategy.name }}
                  </el-radio-button>
                </el-radio-group>
                <p v-if="selectedStrategyDesc" class="strategy-desc">
                  {{ selectedStrategyDesc }}
                </p>
              </div>

              <el-divider />

              <div class="event-section">
                <h4>🚨 当前事件</h4>
                <p class="hint-text">是否面临紧急事件需要处理？（可选）</p>
                <el-radio-group v-model="selectedEvent" size="large">
                  <el-radio-button label="">无</el-radio-button>
                  <el-radio-button 
                    v-for="evt in events" 
                    :key="evt.type"
                    :label="evt.type"
                    :class="{ 'urgent-event': evt.urgent }"
                  >
                    {{ evt.name }}
                    <el-tag v-if="evt.urgent" type="danger" size="small" effect="dark">紧急</el-tag>
                  </el-radio-button>
                </el-radio-group>
                <p v-if="selectedEventDesc" class="event-desc" :class="{ urgent: selectedEventUrgent }">
                  {{ selectedEventDesc }}
                </p>
              </div>

              <el-divider />

              <div class="cornerstone-section">
                <h4>🏛️ 已选基石</h4>
                <p class="hint-text">选择你已拥有的基石（可多选，会影响推荐）</p>
                <el-checkbox-group v-model="selectedCornerstones" size="small">
                  <el-checkbox 
                    v-for="cs in cornerstones" 
                    :key="cs.id"
                    :label="cs.id"
                    border
                  >
                    {{ cs.name_zh || cs.name }}
                    <el-tag v-if="cs.rarity === 'Legendary'" type="warning" size="small" effect="dark">传说</el-tag>
                    <el-tag v-else-if="cs.rarity === 'Epic'" type="primary" size="small" effect="dark">史诗</el-tag>
                  </el-checkbox>
                </el-checkbox-group>
                <p v-if="selectedCornerstones.length > 0" class="cornerstone-desc">
                  已选择 {{ selectedCornerstones.length }} 个基石，相关建筑将获得加成
                </p>
              </div>

              <div class="actions">
                <el-button @click="currentStep = 0">返回</el-button>
                <el-button type="primary" @click="currentStep = 2">
                  下一步
                </el-button>
              </div>
            </el-card>
          </div>

          <!-- Step 3: Recognition -->
          <div v-show="currentStep === 1" class="step-content">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>识别区域确认</span>
                  <el-button type="text" @click="currentStep = 0">返回</el-button>
                </div>
              </template>
              <recognition-box-component
                v-if="uploadedImage"
                ref="recognitionBoxRef"
                :image-url="uploadedImage"
                @boxes-updated="handleBoxesUpdated"
              />
              <div class="actions">
                <el-button @click="currentStep = 1">返回</el-button>
                <el-button 
                  type="primary" 
                  @click="startAnalysis" 
                  :loading="analyzing"
                  :disabled="analyzing"
                >
                  {{ analyzing ? '分析中...' : '开始分析' }}
                </el-button>
              </div>
            </el-card>
          </div>

          <!-- Step 4: Results -->
          <div v-show="currentStep === 3" class="step-content">
            <results-component
              :recommendations="recommendations"
              :game-state="gameState"
            />
            <div class="actions">
              <el-button @click="resetAnalysis">重新分析</el-button>
              <el-button type="primary" @click="$router.push('/history')">
                查看历史
              </el-button>
            </div>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import UploadComponent from '@/components/UploadComponent.vue'
import RecognitionBoxComponent from '@/components/RecognitionBoxComponent.vue'
import ResultsComponent from '@/components/ResultsComponent.vue'
import apiClient from '@/services/api'
import { useNotification } from '@/composables/useNotification'

const { showSuccess, showWarning, showError } = useNotification()

const currentStep = ref(0)
const uploadedImage = ref<string>('')
const uploadedFile = ref<File | null>(null)
const analyzing = ref(false)
const recommendations = ref<any[]>([])
const gameState = ref<any>(null)
const uploadRef = ref()
const recognitionBoxRef = ref()
const currentBoxes = ref<any[]>([])

// Strategy, Event and Cornerstone selection
const strategies = ref<any[]>([])
const events = ref<any[]>([])
const cornerstones = ref<any[]>([])
const selectedStrategy = ref('balanced')
const selectedEvent = ref('')
const selectedCornerstones = ref<string[]>([])

const selectedStrategyDesc = computed(() => {
  const s = strategies.value.find(x => x.type === selectedStrategy.value)
  return s?.description
})

const selectedEventDesc = computed(() => {
  const e = events.value.find(x => x.type === selectedEvent.value)
  return e?.description
})

const selectedEventUrgent = computed(() => {
  const e = events.value.find(x => x.type === selectedEvent.value)
  return e?.urgent
})

// Load strategies, events and cornerstones on mount
onMounted(async () => {
  try {
    const [strategiesRes, eventsRes, cornerstonesRes] = await Promise.all([
      apiClient.get('/api/v1/strategies'),
      apiClient.get('/api/v1/events'),
      apiClient.get('/api/v1/cornerstones')
    ])
    strategies.value = strategiesRes.data.strategies
    events.value = eventsRes.data.events.filter((e: any) => e.type !== 'none')
    cornerstones.value = cornerstonesRes.data.cornerstones
  } catch (error) {
    console.error('Failed to load strategies/events/cornerstones:', error)
  }
})

const handleBoxesUpdated = (boxes: any[]) => {
  currentBoxes.value = boxes
}

const handleUploadSuccess = (imageUrl: string, file: File) => {
  uploadedImage.value = imageUrl
  uploadedFile.value = file
  currentStep.value = 1
  showSuccess('图片上传成功')
}

const handleUploadError = (error: Error) => {
  showError(`上传失败: ${error.message}`)
}

const startAnalysis = async () => {
  if (!uploadedFile.value) {
    showWarning('请先上传图片')
    return
  }

  analyzing.value = true

  try {
    // Prepare form data
    const formData = new FormData()
    formData.append('image', uploadedFile.value)
    
    // Get boxes from recognition component and convert to integers
    const rawBoxes = recognitionBoxRef.value?.getBoxCoordinates() || [
      { x: 100, y: 50, width: 300, height: 200, label: 'blueprints' },
      { x: 450, y: 50, width: 200, height: 150, label: 'resources' },
      { x: 700, y: 50, width: 100, height: 100, label: 'species' }
    ]
    // Convert coordinates to integers (backend requires integers)
    const boxes = rawBoxes.map((box: any) => ({
      x: Math.round(box.x),
      y: Math.round(box.y),
      width: Math.round(box.width),
      height: Math.round(box.height),
      label: box.label
    }))
    formData.append('boxes', JSON.stringify(boxes))
    
    // Get or create session ID
    let sessionId = localStorage.getItem('session_id')
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem('session_id', sessionId)
    }
    formData.append('session_id', sessionId)
    
    // 返回语言：根据浏览器语言或默认中文
    const responseLang = /^zh/i.test(navigator.language) ? 'zh' : 'en'
    formData.append('lang', responseLang)
    
    // Add strategy, event and cornerstones if selected
    if (selectedStrategy.value && selectedStrategy.value !== 'balanced') {
      formData.append('strategy', selectedStrategy.value)
    }
    if (selectedEvent.value) {
      formData.append('event', selectedEvent.value)
    }
    if (selectedCornerstones.value.length > 0) {
      formData.append('cornerstones', selectedCornerstones.value.join(','))
    }

    // Call API
    const response = await apiClient.post('/api/v1/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // Update state
    gameState.value = response.data.game_state
    recommendations.value = response.data.recommendations

    // Move to results step
    currentStep.value = 3
    showSuccess('分析完成')
  } catch (error: any) {
    console.error('Analysis failed:', error)
    // Error message already shown by API interceptor
  } finally {
    analyzing.value = false
  }
}

const resetAnalysis = () => {
  currentStep.value = 0
  uploadedImage.value = ''
  uploadedFile.value = null
  recommendations.value = []
  gameState.value = null
  selectedStrategy.value = 'balanced'
  selectedEvent.value = ''
  selectedCornerstones.value = []
  uploadRef.value?.clearImage()
}
</script>

<style scoped>
.analyze {
  min-height: 100vh;
  background: #f5f5f5;
}

.el-header {
  background: white;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.el-main {
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.content-area {
  margin-top: 40px;
}

.step-content {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recognition-area {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.recognition-area .el-image {
  max-width: 100%;
  max-height: 500px;
}

.hint {
  color: #909399;
  font-size: 14px;
  text-align: center;
}

.actions {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.strategy-section,
.event-section {
  margin-bottom: 24px;
}

.strategy-section h4,
.event-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.hint-text {
  color: #909399;
  font-size: 14px;
  margin: 0 0 16px 0;
}

.strategy-desc,
.event-desc,
.cornerstone-desc {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.event-desc.urgent {
  background: #fef0f0;
  color: #f56c6c;
  border-left: 4px solid #f56c6c;
}

.cornerstone-section {
  margin-bottom: 24px;
}

.cornerstone-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.el-checkbox) {
  margin-right: 0;
  margin-bottom: 8px;
}

:deep(.urgent-event .el-radio-button__inner) {
  color: #f56c6c;
}

:deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.el-radio-button) {
  margin-bottom: 8px;
}

/* Mobile responsive styles */
@media (max-width: 768px) {
  .el-header h1 {
    font-size: 18px;
  }

  .el-main {
    padding: 20px 12px;
  }

  .content-area {
    margin-top: 20px;
  }

  .actions {
    flex-direction: column;
    width: 100%;
  }

  .actions .el-button {
    width: 100%;
  }

  :deep(.el-steps) {
    padding: 0 10px;
  }

  :deep(.el-step__title) {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .el-header h1 {
    font-size: 16px;
  }

  .el-main {
    padding: 16px 8px;
  }

  :deep(.el-card__body) {
    padding: 12px;
  }
}
</style>
