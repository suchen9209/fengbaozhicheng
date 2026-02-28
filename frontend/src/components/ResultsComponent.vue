<template>
  <div class="results-component">
    <div v-if="!recommendations || recommendations.length === 0" class="no-results">
      <el-empty description="暂无推荐结果" />
    </div>

    <div v-else class="results-container">
      <!-- Game State Display -->
      <el-card class="game-state-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>识别结果</span>
            <el-tag v-if="gameState?.confidence" type="info" size="small">
              置信度: {{ (gameState.confidence.blueprints * 100).toFixed(0) }}%
            </el-tag>
          </div>
        </template>
        <div class="game-state-content">
          <div class="state-item">
            <span class="label">种族:</span>
            <el-tag type="success">{{ gameState?.species }}</el-tag>
          </div>
          <div class="state-item">
            <span class="label">资源:</span>
            <div class="resources">
              <el-tag
                v-for="(amount, resource) in gameState?.resources"
                :key="resource"
                size="small"
              >
                {{ resource }}: {{ amount }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Recommendations List -->
      <div class="recommendations-list">
        <h3>蓝图推荐</h3>
        
        <el-card
          v-for="rec in recommendations"
          :key="rec.blueprint_name"
          class="recommendation-card"
          :class="getScoreClass(rec.score)"
          shadow="hover"
        >
          <div class="rec-header">
            <div class="rec-title">
              <span class="rank-badge">{{ rec.rank }}</span>
              <h4>{{ rec.blueprint_name }}</h4>
              <el-tag :type="getScoreTagType(rec.score)" size="large">
                {{ rec.score }} 分
              </el-tag>
              <el-tag
                :type="rec.buildable ? 'success' : 'danger'"
                size="small"
                effect="dark"
                class="buildable-tag"
              >
                {{ rec.buildable ? '✅ 可建造' : '❌ 资源不足' }}
              </el-tag>
            </div>
            <el-button
              text
              @click="toggleDetails(rec.blueprint_name)"
              :icon="expandedBlueprint === rec.blueprint_name ? 'ArrowUp' : 'ArrowDown'"
            >
              {{ expandedBlueprint === rec.blueprint_name ? '收起' : '详情' }}
            </el-button>
          </div>

          <div class="rec-reasoning">
            <pre>{{ rec.reasoning }}</pre>
          </div>

          <el-collapse-transition>
            <div v-show="expandedBlueprint === rec.blueprint_name" class="rec-details">
              <el-divider />
              <div class="details-grid">
                <div class="detail-item">
                  <span class="detail-label">类型:</span>
                  <span>{{ rec.details.type }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">DLC:</span>
                  <span>{{ rec.details.dlc }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">复杂度:</span>
                  <el-rate
                    v-model="rec.details.complexity"
                    disabled
                    show-score
                    text-color="#ff9900"
                  />
                </div>
              </div>

              <div class="io-section">
                <div class="io-group">
                  <h5>输入需求</h5>
                  <div
                    v-for="(amount, item) in rec.details.inputs"
                    :key="item"
                    class="resource-requirement"
                  >
                    <el-tag
                      size="small"
                      :type="getResourceTagType(item, amount, rec.missing_resources)"
                    >
                      {{ item }}: {{ amount }}
                    </el-tag>
                    <span
                      v-if="rec.missing_resources[item]"
                      class="resource-shortage"
                    >
                      (缺 {{ rec.missing_resources[item].missing }})
                    </span>
                    <span
                      v-else-if="gameState?.resources[item] !== undefined"
                      class="resource-sufficient"
                    >
                      (有 {{ gameState.resources[item] }})
                    </span>
                  </div>
                  <span v-if="Object.keys(rec.details.inputs).length === 0" class="empty-text">
                    无需输入
                  </span>
                </div>
                <div class="io-group">
                  <h5>输出</h5>
                  <el-tag
                    v-for="(amount, item) in rec.details.outputs"
                    :key="item"
                    size="small"
                    type="success"
                  >
                    {{ item }}: {{ amount }}
                  </el-tag>
                  <span v-if="Object.keys(rec.details.outputs).length === 0" class="empty-text">
                    无产出
                  </span>
                </div>
              </div>

              <div class="values-section">
                <h5>价值评分</h5>
                <div class="values-grid">
                  <div class="value-item">
                    <span>食物:</span>
                    <el-progress
                      :percentage="(rec.details.values.food / 5) * 100"
                      :format="() => rec.details.values.food"
                    />
                  </div>
                  <div class="value-item">
                    <span>燃料:</span>
                    <el-progress
                      :percentage="(rec.details.values.fuel / 5) * 100"
                      :format="() => rec.details.values.fuel"
                      color="#e6a23c"
                    />
                  </div>
                  <div class="value-item">
                    <span>决心:</span>
                    <el-progress
                      :percentage="(rec.details.values.resolve / 5) * 100"
                      :format="() => rec.details.values.resolve"
                      color="#f56c6c"
                    />
                  </div>
                </div>
              </div>

              <p v-if="rec.details.description" class="description">
                {{ rec.details.description }}
              </p>
            </div>
          </el-collapse-transition>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface GameState {
  available_blueprints: string[]
  resources: Record<string, number>
  species: string
  confidence?: Record<string, number>
}

interface BlueprintDetails {
  name: string
  name_en: string
  type: string
  dlc: string
  inputs: Record<string, number>
  outputs: Record<string, number>
  values: {
    food: number
    fuel: number
    resolve: number
  }
  complexity: number
  synergy: any
  description: string
}

interface MissingResource {
  required: number
  available: number
  missing: number
}

interface Recommendation {
  blueprint_name: string
  score: number
  rank: number
  reasoning: string
  details: BlueprintDetails
  buildable: boolean
  missing_resources: Record<string, MissingResource>
}

interface Props {
  recommendations?: Recommendation[]
  gameState?: GameState
}

const props = defineProps<Props>()

const expandedBlueprint = ref<string | null>(null)

const toggleDetails = (blueprintName: string) => {
  expandedBlueprint.value = expandedBlueprint.value === blueprintName ? null : blueprintName
}

const getScoreClass = (score: number): string => {
  if (score >= 80) return 'score-high'
  if (score >= 50) return 'score-medium'
  return 'score-low'
}

const getScoreTagType = (score: number): 'success' | 'warning' | 'info' => {
  if (score >= 80) return 'success'
  if (score >= 50) return 'warning'
  return 'info'
}

const getScoreColor = (score: number): string => {
  if (score >= 80) return '#67c23a'
  if (score >= 50) return '#e6a23c'
  return '#909399'
}

const getResourceTagType = (
  resourceName: string,
  required: number,
  missingResources: Record<string, MissingResource>
): 'success' | 'danger' | '' => {
  if (missingResources[resourceName]) {
    return 'danger'
  }
  if (props.gameState?.resources[resourceName] >= required) {
    return 'success'
  }
  return ''
}

defineExpose({
  getScoreColor
})
</script>

<style scoped>
.results-component {
  width: 100%;
}

.no-results {
  padding: 40px;
  text-align: center;
}

.results-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.game-state-card {
  background: #f5f7fa;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.game-state-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.state-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.state-item .label {
  font-weight: 500;
  color: #606266;
  min-width: 60px;
}

.resources {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recommendations-list {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 16px;
}

.recommendations-list h3 {
  width: 100%;
  margin-bottom: 16px;
  color: #303133;
}

.recommendation-card {
  flex: 1;
  min-width: 300px;
  max-width: 400px;
  transition: all 0.3s;
}

.recommendation-card.score-high {
  border-left: 4px solid #67c23a;
}

.recommendation-card.score-medium {
  border-left: 4px solid #e6a23c;
}

.recommendation-card.score-low {
  border-left: 4px solid #909399;
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.rec-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  font-weight: bold;
  font-size: 16px;
}

.rec-title h4 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.buildable-tag {
  margin-left: 4px;
}

.resource-requirement {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.resource-shortage {
  color: #f56c6c;
  font-size: 12px;
}

.resource-sufficient {
  color: #67c23a;
  font-size: 12px;
}

.rec-reasoning {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.rec-reasoning pre {
  margin: 0;
  font-family: inherit;
  white-space: pre-wrap;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.rec-details {
  padding-top: 12px;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-label {
  font-weight: 500;
  color: #909399;
}

.io-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.io-group h5 {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
}

.io-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.io-group .el-tag {
  width: fit-content;
}

.empty-text {
  color: #c0c4cc;
  font-size: 12px;
}

.values-section h5 {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
}

.values-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.value-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.value-item span {
  min-width: 50px;
  color: #606266;
}

.value-item .el-progress {
  flex: 1;
}

.description {
  margin-top: 16px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 4px;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

/* Mobile responsive styles */
@media (max-width: 768px) {
  .recommendations-list {
    flex-direction: column;
  }
  
  .recommendation-card {
    min-width: 100%;
    max-width: 100%;
  }
  
  .rec-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .rec-title {
    flex-wrap: wrap;
  }

  .rec-title h4 {
    font-size: 16px;
  }

  .details-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .io-section {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .value-item span {
    min-width: 40px;
    font-size: 13px;
  }

  .resources {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 480px) {
  .results-container {
    gap: 16px;
  }

  .recommendations-list h3 {
    font-size: 16px;
  }

  .rank-badge {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }

  .rec-title h4 {
    font-size: 14px;
  }

  .rec-reasoning {
    padding: 8px;
  }

  .rec-reasoning pre {
    font-size: 13px;
  }

  :deep(.el-card__body) {
    padding: 12px;
  }
}
</style>
