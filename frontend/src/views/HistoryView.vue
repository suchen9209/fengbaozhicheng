<template>
  <div class="history">
    <el-container>
      <el-header>
        <h1>历史记录</h1>
        <el-button @click="$router.push('/analyze')" type="primary">
          新建分析
        </el-button>
      </el-header>

      <el-main>
        <div v-if="loading" class="loading">
          <el-skeleton :rows="5" animated />
        </div>

        <div v-else-if="records.length === 0" class="no-records">
          <el-empty description="暂无历史记录">
            <el-button type="primary" @click="$router.push('/analyze')">
              开始分析
            </el-button>
          </el-empty>
        </div>

        <div v-else class="records-list">
          <el-card
            v-for="record in records"
            :key="record.id"
            class="record-card"
            shadow="hover"
            @click="viewRecord(record)"
          >
            <div class="record-header">
              <div class="record-info">
                <h3>{{ formatDate(record.timestamp) }}</h3>
                <el-tag size="small">{{ record.game_state.species }}</el-tag>
              </div>
              <el-icon class="arrow-icon"><arrow-right /></el-icon>
            </div>

            <div class="record-preview">
              <div class="preview-item">
                <span class="label">推荐蓝图:</span>
                <span class="value">{{ record.recommendations[0]?.blueprint_name }}</span>
              </div>
              <div class="preview-item">
                <span class="label">评分:</span>
                <el-tag :type="getScoreType(record.recommendations[0]?.score)">
                  {{ record.recommendations[0]?.score }} 分
                </el-tag>
              </div>
            </div>
          </el-card>

          <el-pagination
            v-if="total > limit"
            v-model:current-page="currentPage"
            v-model:page-size="limit"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="fetchHistory"
            @size-change="fetchHistory"
          />
        </div>
      </el-main>
    </el-container>

    <!-- Record Detail Dialog -->
    <el-dialog
      v-model="dialogVisible"
      title="分析详情"
      width="80%"
      :close-on-click-modal="true"
    >
      <results-component
        v-if="selectedRecord"
        :recommendations="selectedRecord.recommendations"
        :game-state="selectedRecord.game_state"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import ResultsComponent from '@/components/ResultsComponent.vue'
import apiClient from '@/services/api'
import { useNotification } from '@/composables/useNotification'

const { showError } = useNotification()

interface HistoryRecord {
  id: string
  timestamp: string
  screenshot_url: string
  game_state: any
  recommendations: any[]
}

const loading = ref(false)
const records = ref<HistoryRecord[]>([])
const total = ref(0)
const currentPage = ref(1)
const limit = ref(20)
const dialogVisible = ref(false)
const selectedRecord = ref<HistoryRecord | null>(null)

const fetchHistory = async () => {
  loading.value = true

  try {
    const sessionId = localStorage.getItem('session_id')
    const offset = (currentPage.value - 1) * limit.value

    const response = await apiClient.get('/api/v1/history', {
      params: {
        limit: limit.value,
        offset: offset,
        session_id: sessionId
      }
    })

    records.value = response.data.records
    total.value = response.data.total
  } catch (error: any) {
    console.error('Failed to fetch history:', error)
    // Error message already shown by API interceptor
  } finally {
    loading.value = false
  }
}

const viewRecord = (record: HistoryRecord) => {
  selectedRecord.value = record
  dialogVisible.value = true
}

const formatDate = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getScoreType = (score: number): 'success' | 'warning' | 'info' => {
  if (score >= 80) return 'success'
  if (score >= 50) return 'warning'
  return 'info'
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.history {
  min-height: 100vh;
  background: #f5f5f5;
}

.el-header {
  background: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.loading,
.no-records {
  padding: 40px;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.record-card {
  cursor: pointer;
  transition: all 0.3s;
}

.record-card:hover {
  transform: translateY(-2px);
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.record-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.record-info h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.arrow-icon {
  font-size: 20px;
  color: #909399;
}

.record-preview {
  display: flex;
  gap: 24px;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-item .label {
  color: #909399;
  font-size: 14px;
}

.preview-item .value {
  color: #303133;
  font-weight: 500;
}

.el-pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

/* Mobile responsive styles */
@media (max-width: 768px) {
  .el-header {
    padding: 0 12px;
  }

  .el-header h1 {
    font-size: 18px;
  }

  .el-main {
    padding: 20px 12px;
  }

  .record-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .record-info h3 {
    font-size: 14px;
  }

  .record-preview {
    flex-direction: column;
    gap: 12px;
  }

  .preview-item {
    font-size: 13px;
  }

  :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
  }

  :deep(.el-dialog) {
    width: 95% !important;
    margin: 0 auto;
  }
}

@media (max-width: 480px) {
  .el-header h1 {
    font-size: 16px;
  }

  .el-header .el-button {
    padding: 8px 12px;
    font-size: 13px;
  }

  .el-main {
    padding: 16px 8px;
  }

  .loading,
  .no-records {
    padding: 20px;
  }

  :deep(.el-card__body) {
    padding: 12px;
  }
}
</style>
