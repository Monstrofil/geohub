<template>
  <div class="image-preview">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading image...</p>
    </div>
    
    <div v-else-if="error" class="error">
      <div class="error-icon">
        <svg width="48" height="48" viewBox="0 0 48 48">
          <circle cx="24" cy="24" r="20" fill="#dc3545"/>
          <path d="M16 16l16 16M32 16l-16 16" stroke="white" stroke-width="3" fill="none" stroke-linecap="round"/>
        </svg>
      </div>
      <h3>Failed to Load Image</h3>
      <p>{{ error }}</p>
      <button @click="loadImage" class="retry-btn">Try Again</button>
    </div>
    
    <div v-else-if="imageUrl" class="image-container">
      <div class="image-toolbar">
        <div class="image-controls">
          <button @click="resetZoom" class="control-btn" title="Reset zoom">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            100%
          </button>
          <button @click="zoomIn" class="control-btn" title="Zoom in">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          <button @click="zoomOut" class="control-btn" title="Zoom out">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          <span class="zoom-info">{{ Math.round(zoomLevel * 100) }}%</span>
        </div>
        <div class="image-actions">
          <button @click="downloadImage" class="download-btn">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M14 10v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="8,14 8,4 8,4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="4" y1="8" x2="8" y2="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="4" x2="8" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Download
          </button>
        </div>
      </div>
      
      <div class="image-viewer" @wheel="onWheel" @mousedown="startPan" @mousemove="onPan" @mouseup="endPan" @mouseleave="endPan">
        <div class="image-wrapper" :style="imageWrapperStyle">
          <img 
            :src="imageUrl" 
            :style="imageStyle"
            @load="onImageLoad"
            @error="onImageError"
            class="preview-image"
            draggable="false"
          />
        </div>
      </div>
      
      <div v-if="imageInfo" class="image-info">
        <span class="image-dimensions">{{ imageInfo.width }} × {{ imageInfo.height }} pixels</span>
        <span v-if="imageInfo.size" class="image-size">{{ formatFileSize(imageInfo.size) }}</span>
        <span class="image-format">{{ getImageFormat() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import apiService from '../../services/api.js'
import { formatFileSize as formatSize } from '../../utils/fileHelpers.js'

const props = defineProps({
  fileId: {
    type: String,
    required: true
  },
  file: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['error', 'loaded'])

// State
const loading = ref(false)
const error = ref(null)
const imageUrl = ref(null)
const zoomLevel = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
const lastPanX = ref(0)
const lastPanY = ref(0)
const imageInfo = ref(null)

// Constants
const MIN_ZOOM = 0.1
const MAX_ZOOM = 5
const ZOOM_STEP = 0.1

// Computed
const downloadUrl = computed(() => {
  return `${apiService.baseUrl}/files/${props.fileId}/download`
})

const imageWrapperStyle = computed(() => {
  return {
    transform: `translate(${panX.value}px, ${panY.value}px) scale(${zoomLevel.value})`,
    transformOrigin: 'center center',
    transition: isPanning.value ? 'none' : 'transform 0.1s ease-out'
  }
})

const imageStyle = computed(() => {
  return {
    maxWidth: '100%',
    maxHeight: '100%',
    objectFit: 'contain'
  }
})

// Methods
async function loadImage() {
  if (!props.fileId) return
  
  loading.value = true
  error.value = null
  
  try {
    // Get the image URL for viewing
    imageUrl.value = `${apiService.baseUrl}/files/${props.fileId}/download`
    emit('loaded')
  } catch (err) {
    console.error('Failed to load image:', err)
    error.value = err.message || 'Failed to load image'
    emit('error', error.value)
  } finally {
    loading.value = false
  }
}

function onImageLoad(event) {
  const img = event.target
  imageInfo.value = {
    width: img.naturalWidth,
    height: img.naturalHeight,
    size: props.file?.size
  }
  loading.value = false
  emit('loaded')
}

function onImageError() {
  error.value = 'Failed to display image'
  loading.value = false
  emit('error', error.value)
}

function zoomIn() {
  zoomLevel.value = Math.min(zoomLevel.value + ZOOM_STEP, MAX_ZOOM)
}

function zoomOut() {
  zoomLevel.value = Math.max(zoomLevel.value - ZOOM_STEP, MIN_ZOOM)
}

function resetZoom() {
  zoomLevel.value = 1
  panX.value = 0
  panY.value = 0
}

function onWheel(event) {
  event.preventDefault()
  
  const delta = event.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP
  const newZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoomLevel.value + delta))
  
  // Zoom towards mouse position
  const rect = event.currentTarget.getBoundingClientRect()
  const mouseX = event.clientX - rect.left
  const mouseY = event.clientY - rect.top
  
  const zoomFactor = newZoom / zoomLevel.value
  panX.value = mouseX - (mouseX - panX.value) * zoomFactor
  panY.value = mouseY - (mouseY - panY.value) * zoomFactor
  
  zoomLevel.value = newZoom
}

function startPan(event) {
  if (event.button === 0) { // Left mouse button
    isPanning.value = true
    lastPanX.value = event.clientX
    lastPanY.value = event.clientY
    event.preventDefault()
  }
}

function onPan(event) {
  if (!isPanning.value) return
  
  const deltaX = event.clientX - lastPanX.value
  const deltaY = event.clientY - lastPanY.value
  
  panX.value += deltaX
  panY.value += deltaY
  
  lastPanX.value = event.clientX
  lastPanY.value = event.clientY
}

function endPan() {
  isPanning.value = false
}

function downloadImage() {
  const link = document.createElement('a')
  link.href = downloadUrl.value
  link.download = props.file?.name || 'image'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function formatFileSize(bytes) {
  return formatSize(bytes)
}

function getImageFormat() {
  const mimeType = props.file?.object_details?.mime_type || props.file?.type
  if (mimeType) {
    const format = mimeType.split('/')[1]?.toUpperCase()
    return format || 'IMAGE'
  }
  return 'IMAGE'
}

// Lifecycle
onMounted(() => {
  loadImage()
})

watch(() => props.fileId, () => {
  if (props.fileId) {
    resetZoom()
    loadImage()
  }
})
</script>

<style scoped>
.image-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

.loading, .error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  height: 100%;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  margin-bottom: 1rem;
}

.error h3 {
  color: #dc3545;
  margin-bottom: 0.5rem;
}

.error p {
  color: #6c757d;
  margin-bottom: 1rem;
}

.retry-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #0056b3;
}

.image-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.image-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.image-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: #fff;
  border: 1px solid #dee2e6;
  padding: 0.375rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.control-btn:hover {
  background: #e9ecef;
}

.zoom-info {
  font-weight: 500;
  color: #495057;
  margin-left: 0.5rem;
}

.image-actions {
  display: flex;
  gap: 0.5rem;
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: #28a745;
  color: white;
  border: none;
  padding: 0.375rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.download-btn:hover {
  background: #218838;
}

.image-viewer {
  flex: 1;
  overflow: hidden;
  position: relative;
  cursor: grab;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-viewer:active {
  cursor: grabbing;
}

.image-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.preview-image {
  user-select: none;
  -webkit-user-drag: none;
  -khtml-user-drag: none;
  -moz-user-drag: none;
  -o-user-drag: none;
  user-drag: none;
}

.image-info {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
  font-size: 0.875rem;
  color: #6c757d;
}

.image-dimensions {
  font-weight: 500;
}

.image-size {
  color: #6c757d;
}

.image-format {
  font-weight: 500;
  color: #007bff;
}
</style>

