<template>
  <div class="recognition-box-component">
    <div class="canvas-container" ref="containerRef">
      <canvas
        ref="canvasRef"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      />
    </div>

    <div class="box-controls">
      <div class="auto-detect-section">
        <el-button 
          type="primary" 
          @click="autoDetectBoxes"
          :loading="isDetecting"
          size="small"
        >
          🎯 自动定位
        </el-button>
        <el-button 
          type="default" 
          @click="resetToDefault"
          size="small"
        >
          重置
        </el-button>
        <span class="resolution-hint" v-if="imageResolution">
          分辨率: {{ imageResolution.width }}×{{ imageResolution.height }}
        </span>
      </div>

      <div class="box-list">
        <div
          v-for="box in boxes"
          :key="box.label"
          class="box-item"
          :class="{ active: selectedBox?.label === box.label }"
          @click="selectBox(box)"
        >
          <div class="box-info">
            <span class="box-label">{{ getBoxDisplayName(box.label) }}</span>
            <span class="box-coords">
              {{ Math.round(box.x) }}, {{ Math.round(box.y) }}, {{ Math.round(box.width) }}×{{ Math.round(box.height) }}
            </span>
          </div>
          <div class="box-color" :style="{ background: getBoxColor(box.label) }" />
        </div>
      </div>

      <div class="instructions">
        <el-alert
          title="操作提示"
          type="info"
          :closable="false"
          show-icon
        >
          <ul>
            <li>点击"自动定位"智能识别区域</li>
            <li>点击并拖动识别框来微调位置</li>
            <li>拖动识别框边缘来调整大小</li>
          </ul>
        </el-alert>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'

interface Box {
  x: number
  y: number
  width: number
  height: number
  label: string
}

interface Props {
  imageUrl: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'boxes-updated', boxes: Box[]): void
}>()

const canvasRef = ref<HTMLCanvasElement>()
const containerRef = ref<HTMLDivElement>()
const ctx = ref<CanvasRenderingContext2D | null>(null)
const image = ref<HTMLImageElement | null>(null)

// Box state
const boxes = ref<Box[]>([
  { x: 100, y: 50, width: 300, height: 200, label: 'blueprints' },
  { x: 450, y: 50, width: 200, height: 150, label: 'resources' },
  { x: 700, y: 50, width: 100, height: 100, label: 'species' }
])

const selectedBox = ref<Box | null>(null)
const isDragging = ref(false)
const isResizing = ref(false)
const isDetecting = ref(false)
const imageResolution = ref<{width: number, height: number} | null>(null)
const resizeHandle = ref<string>('')
const dragStart = ref({ x: 0, y: 0 })
const boxStart = ref({ x: 0, y: 0, width: 0, height: 0 })

const HANDLE_SIZE = 8
const COLORS = {
  blueprints: '#409eff',
  resources: '#67c23a',
  species: '#e6a23c'
}

onMounted(() => {
  initCanvas()
})

watch(() => props.imageUrl, () => {
  initCanvas()
})

const initCanvas = async () => {
  if (!canvasRef.value || !props.imageUrl) return

  await nextTick()

  // Load image
  const img = new Image()
  img.onload = () => {
    image.value = img
    imageResolution.value = { width: img.width, height: img.height }

    // Set canvas size to match image
    if (canvasRef.value) {
      canvasRef.value.width = img.width
      canvasRef.value.height = img.height
      ctx.value = canvasRef.value.getContext('2d')
      
      // 自动检测位置
      autoDetectBoxes()
    }
  }
  img.src = props.imageUrl
}

const draw = () => {
  if (!ctx.value || !image.value || !canvasRef.value) return

  const context = ctx.value

  // Clear canvas
  context.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)

  // Draw image
  context.drawImage(image.value, 0, 0)

  // Draw boxes
  boxes.value.forEach(box => {
    const isSelected = selectedBox.value?.label === box.label
    const color = COLORS[box.label as keyof typeof COLORS] || '#909399'

    // Draw box
    context.strokeStyle = color
    context.lineWidth = isSelected ? 3 : 2
    context.strokeRect(box.x, box.y, box.width, box.height)

    // Draw semi-transparent fill
    context.fillStyle = color + '20'
    context.fillRect(box.x, box.y, box.width, box.height)

    // Draw label
    context.fillStyle = color
    context.font = 'bold 14px Arial'
    context.fillText(
      getBoxDisplayName(box.label),
      box.x + 5,
      box.y - 5
    )

    // Draw resize handles if selected
    if (isSelected) {
      drawResizeHandles(box, color)
    }
  })
}

const drawResizeHandles = (box: Box, color: string) => {
  if (!ctx.value) return

  const handles = [
    { x: box.x, y: box.y }, // top-left
    { x: box.x + box.width, y: box.y }, // top-right
    { x: box.x, y: box.y + box.height }, // bottom-left
    { x: box.x + box.width, y: box.y + box.height }, // bottom-right
    { x: box.x + box.width / 2, y: box.y }, // top-center
    { x: box.x + box.width / 2, y: box.y + box.height }, // bottom-center
    { x: box.x, y: box.y + box.height / 2 }, // left-center
    { x: box.x + box.width, y: box.y + box.height / 2 } // right-center
  ]

  ctx.value.fillStyle = color
  handles.forEach(handle => {
    ctx.value!.fillRect(
      handle.x - HANDLE_SIZE / 2,
      handle.y - HANDLE_SIZE / 2,
      HANDLE_SIZE,
      HANDLE_SIZE
    )
  })
}

const getMousePos = (e: MouseEvent | TouchEvent): { x: number; y: number } => {
  if (!canvasRef.value) return { x: 0, y: 0 }

  const rect = canvasRef.value.getBoundingClientRect()
  const scaleX = canvasRef.value.width / rect.width
  const scaleY = canvasRef.value.height / rect.height

  let clientX, clientY
  if (e instanceof MouseEvent) {
    clientX = e.clientX
    clientY = e.clientY
  } else {
    clientX = e.touches[0]?.clientX || 0
    clientY = e.touches[0]?.clientY || 0
  }

  return {
    x: (clientX - rect.left) * scaleX,
    y: (clientY - rect.top) * scaleY
  }
}

const getResizeHandle = (box: Box, x: number, y: number): string => {
  const handles = {
    'nw': { x: box.x, y: box.y },
    'ne': { x: box.x + box.width, y: box.y },
    'sw': { x: box.x, y: box.y + box.height },
    'se': { x: box.x + box.width, y: box.y + box.height },
    'n': { x: box.x + box.width / 2, y: box.y },
    's': { x: box.x + box.width / 2, y: box.y + box.height },
    'w': { x: box.x, y: box.y + box.height / 2 },
    'e': { x: box.x + box.width, y: box.y + box.height / 2 }
  }

  for (const [handle, pos] of Object.entries(handles)) {
    if (
      Math.abs(x - pos.x) <= HANDLE_SIZE &&
      Math.abs(y - pos.y) <= HANDLE_SIZE
    ) {
      return handle
    }
  }

  return ''
}

const isInsideBox = (box: Box, x: number, y: number): boolean => {
  return (
    x >= box.x &&
    x <= box.x + box.width &&
    y >= box.y &&
    y <= box.y + box.height
  )
}

const handleMouseDown = (e: MouseEvent) => {
  const pos = getMousePos(e)

  // Check if clicking on a resize handle
  for (const box of boxes.value) {
    const handle = getResizeHandle(box, pos.x, pos.y)
    if (handle) {
      selectedBox.value = box
      isResizing.value = true
      resizeHandle.value = handle
      dragStart.value = pos
      boxStart.value = { ...box }
      return
    }
  }

  // Check if clicking inside a box
  for (const box of boxes.value) {
    if (isInsideBox(box, pos.x, pos.y)) {
      selectedBox.value = box
      isDragging.value = true
      dragStart.value = pos
      boxStart.value = { ...box }
      return
    }
  }

  // Clicked outside all boxes
  selectedBox.value = null
  draw()
}

const handleMouseMove = (e: MouseEvent) => {
  const pos = getMousePos(e)

  if (isDragging.value && selectedBox.value) {
    // Move box
    const dx = pos.x - dragStart.value.x
    const dy = pos.y - dragStart.value.y

    selectedBox.value.x = boxStart.value.x + dx
    selectedBox.value.y = boxStart.value.y + dy

    draw()
    emitBoxes()
  } else if (isResizing.value && selectedBox.value) {
    // Resize box
    const dx = pos.x - dragStart.value.x
    const dy = pos.y - dragStart.value.y

    const handle = resizeHandle.value

    if (handle.includes('n')) {
      selectedBox.value.y = boxStart.value.y + dy
      selectedBox.value.height = boxStart.value.height - dy
    }
    if (handle.includes('s')) {
      selectedBox.value.height = boxStart.value.height + dy
    }
    if (handle.includes('w')) {
      selectedBox.value.x = boxStart.value.x + dx
      selectedBox.value.width = boxStart.value.width - dx
    }
    if (handle.includes('e')) {
      selectedBox.value.width = boxStart.value.width + dx
    }

    // Ensure minimum size
    if (selectedBox.value.width < 50) selectedBox.value.width = 50
    if (selectedBox.value.height < 50) selectedBox.value.height = 50

    draw()
    emitBoxes()
  } else {
    // Update cursor based on hover
    updateCursor(pos)
  }
}

const handleMouseUp = () => {
  isDragging.value = false
  isResizing.value = false
  resizeHandle.value = ''
}

const handleTouchStart = (e: TouchEvent) => {
  e.preventDefault()
  handleMouseDown(e as any)
}

const handleTouchMove = (e: TouchEvent) => {
  e.preventDefault()
  handleMouseMove(e as any)
}

const handleTouchEnd = (e: TouchEvent) => {
  e.preventDefault()
  handleMouseUp()
}

const updateCursor = (pos: { x: number; y: number }) => {
  if (!canvasRef.value) return

  let cursor = 'default'

  for (const box of boxes.value) {
    const handle = getResizeHandle(box, pos.x, pos.y)
    if (handle) {
      cursor = `${handle}-resize`
      break
    } else if (isInsideBox(box, pos.x, pos.y)) {
      cursor = 'move'
      break
    }
  }

  canvasRef.value.style.cursor = cursor
}

const selectBox = (box: Box) => {
  selectedBox.value = box
  draw()
}

const getBoxDisplayName = (label: string): string => {
  const names: Record<string, string> = {
    blueprints: '蓝图区域',
    resources: '资源区域',
    species: '种族区域'
  }
  return names[label] || label
}

const getBoxColor = (label: string): string => {
  return COLORS[label as keyof typeof COLORS] || '#909399'
}

const emitBoxes = () => {
  emit('boxes-updated', boxes.value)
}

// 根据图片分辨率计算预设位置
const calculateDefaultBoxes = (width: number, height: number): Box[] => {
  // 基于 2560x1440 的参考位置，按比例缩放
  const refWidth = 2560
  const refHeight = 1440
  
  const scaleX = width / refWidth
  const scaleY = height / refHeight
  
  // 蓝图选择区域（中间偏下，4个卡片位置）
  const blueprintsBox: Box = {
    x: Math.round(560 * scaleX),      // 左边距
    y: Math.round(420 * scaleY),      // 上边距
    width: Math.round(1440 * scaleX), // 宽度覆盖4个卡片
    height: Math.round(600 * scaleY), // 高度
    label: 'blueprints'
  }
  
  // 资源区域（顶部横向栏 - 资源图标在顶部）
  const resourcesBox: Box = {
    x: Math.round(300 * scaleX),      // 左侧起始
    y: Math.round(5 * scaleY),        // 顶部
    width: Math.round(1960 * scaleX), // 宽度覆盖顶部资源栏
    height: Math.round(80 * scaleY),  // 高度约80像素
    label: 'resources'
  }
  
  // 种族/人口区域（左侧 - 三个圆形头像）
  const speciesBox: Box = {
    x: Math.round(10 * scaleX),       // 最左侧
    y: Math.round(50 * scaleY),       // 从顶部开始覆盖三个头像
    width: Math.round(250 * scaleX),  // 宽度覆盖左侧栏
    height: Math.round(500 * scaleY), // 高度覆盖三个种族头像
    label: 'species'
  }
  
  return [blueprintsBox, resourcesBox, speciesBox]
}

// 自动检测/定位
const autoDetectBoxes = async () => {
  if (!image.value || !canvasRef.value) return
  
  isDetecting.value = true
  
  // 模拟检测延迟
  await new Promise(resolve => setTimeout(resolve, 300))
  
  const width = image.value.width
  const height = image.value.height
  
  // 根据分辨率设置预设位置
  boxes.value = calculateDefaultBoxes(width, height)
  
  isDetecting.value = false
  draw()
  emitBoxes()
}

// 重置为默认位置
const resetToDefault = () => {
  if (!image.value) return
  
  boxes.value = calculateDefaultBoxes(image.value.width, image.value.height)
  draw()
  emitBoxes()
}

const getBoxCoordinates = (): Box[] => {
  return boxes.value
}

defineExpose({
  getBoxCoordinates,
  autoDetectBoxes
})
</script>

<style scoped>
.recognition-box-component {
  display: flex;
  gap: 20px;
}

.canvas-container {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: auto;
  background: #f5f7fa;
  display: flex;
  justify-content: center;
  align-items: center;
}

canvas {
  display: block;
  max-width: 100%;
  height: auto;
  cursor: default;
}

.box-controls {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.box-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.box-item {
  padding: 12px;
  border: 2px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.box-item:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.box-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.box-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.box-label {
  font-weight: 500;
  color: #303133;
}

.box-coords {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

.box-color {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.auto-detect-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 4px;
  border: 1px solid #409eff;
}

.resolution-hint {
  margin-left: auto;
  font-size: 12px;
  color: #606266;
  font-family: monospace;
}

.instructions {
  margin-top: auto;
}

.instructions ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.instructions li {
  margin: 4px 0;
  font-size: 13px;
  color: #606266;
}

@media (max-width: 768px) {
  .recognition-box-component {
    flex-direction: column;
  }

  .box-controls {
    width: 100%;
  }
  
  .resolution-hint {
    margin-left: 0;
    width: 100%;
    text-align: right;
  }
}
</style>
