<template>
  <div class="file-viewer">
    <div class="viewer-header">
      <div class="header-content">
        <div class="file-info">
          <div class="file-icon" v-html="fileIcon"></div>
          <div class="file-details">
            <h1 class="file-name">{{ file?.tags?.name || file?.original_name || 'Untitled File' }}</h1>
            <div class="file-meta">
              <span class="file-type">{{ file?.base_file_type || 'Unknown' }}</span>
              <span class="file-size" v-if="file?.file_size">{{ formatFileSize(file.file_size) }}</span>
              <span class="file-date" v-if="file?.created_at">{{ formatDate(file.created_at) }}</span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <router-link :to="{name: 'FileEditor', params: { treePath: $route.params.treePath }}" class="edit-btn">
            <i class="fas fa-edit"></i>
            Edit
          </router-link>
          <button @click="goBack" class="back-btn">
            <i class="fas fa-arrow-left"></i>
            Back
          </button>
        </div>
      </div>
    </div>

    <div class="viewer-content">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading file...</p>
      </div>
      
      <div v-else-if="error" class="error">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading File</h3>
        <p>{{ error }}</p>
        <button @click="loadFile" class="retry-btn">Try Again</button>
      </div>
      
      <div v-else-if="!file" class="not-found">
        <i class="fas fa-file-excel"></i>
        <h3>File Not Found</h3>
        <p>The requested file could not be found.</p>
        <button @click="goBack" class="back-btn">Go Back</button>
      </div>
      
      <div v-else class="file-content">
        <!-- File type specific viewers -->
        <div v-if="file.base_file_type === 'raster'" class="raster-viewer">
          <h3>Raster File Viewer</h3>
          <p>This is a raster file ({{ file.mime_type }}).</p>
          <div class="preview-placeholder">
            <i class="fas fa-image"></i>
            <p>Raster preview would be displayed here</p>
          </div>
        </div>
        
        <div v-else-if="file.base_file_type === 'vector'" class="vector-viewer">
          <h3>Vector File Viewer</h3>
          <p>This is a vector file ({{ file.mime_type }}).</p>
          <div class="preview-placeholder">
            <i class="fas fa-draw-polygon"></i>
            <p>Vector preview would be displayed here</p>
          </div>
        </div>
        
        <div v-else class="generic-viewer">
          <h3>File Viewer</h3>
          <p>File type: {{ file.mime_type }}</p>
          <div class="preview-placeholder">
            <i class="fas fa-file"></i>
            <p>File preview would be displayed here</p>
          </div>
        </div>

        <!-- File tags -->
        <div v-if="file.tags && Object.keys(file.tags).length > 0" class="file-tags">
          <h3>File Properties</h3>
          <div class="tags-grid">
            <div v-for="(value, key) in file.tags" :key="key" class="tag-item">
              <span class="tag-key">{{ key }}:</span>
              <span class="tag-value">{{ value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiService from '../services/api.js'

const route = useRoute()
const router = useRouter()

// State
const file = ref(null)
const loading = ref(false)
const error = ref(null)

const props = defineProps({
  commitId: {
    type: [String, Number],
    required: true
  },
  treePath: {
    type: [String, Number, Array],
    required: true
  }
})


// Computed
const fileIcon = computed(() => {
  if (!file.value) return ''
  
  const fileType = file.value.base_file_type || 'raw'
  switch (fileType) {
    case 'raster':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="4" y="8" width="32" height="24" rx="4" fill="#e0e7ef" stroke="#7faaff" stroke-width="2"/>
        <circle cx="14" cy="24" r="4" fill="#7faaff"/>
        <rect x="20" y="16" width="12" height="8" fill="#b3d1ff"/>
        <path d="M6 6l4 4M10 6l4 4M14 6l4 4" stroke="#7faaff" stroke-width="1" fill="none"/>
      </svg>`
    case 'vector':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="4" y="8" width="32" height="24" rx="4" fill="#e0f7e7" stroke="#2ecc71" stroke-width="2"/>
        <circle cx="12" cy="28" r="3" fill="#2ecc71"/>
        <circle cx="28" cy="14" r="3" fill="#2ecc71"/>
        <line x1="12" y1="28" x2="28" y2="14" stroke="#27ae60" stroke-width="2"/>
        <path d="M6 6l4 4M10 6l4 4M14 6l4 4" stroke="#2ecc71" stroke-width="1" fill="none"/>
      </svg>`
    default:
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="6" y="8" width="28" height="24" rx="4" fill="#f7f7e7" stroke="#6c757d" stroke-width="2"/>
        <rect x="12" y="16" width="16" height="2" fill="#6c757d"/>
        <rect x="12" y="22" width="10" height="2" fill="#6c757d"/>
        <rect x="12" y="28" width="14" height="2" fill="#6c757d"/>
      </svg>`
  }
})

// Methods
async function loadFile() {
  if (!route.params.treePath) {
    error.value = 'No file path provided'
    return
  }

  loading.value = true
  error.value = null
  
  try {
    // This is a dummy implementation - in real app you'd fetch the file data
    // const response = await apiService.getTreeEntry(route.params.commitId, route.params.treePath)
    // file.value = response.object
    
    // For now, create a dummy file object
    file.value = {
      id: 'dummy-id',
      name: 'dummy-file',
      original_name: 'Sample File',
      file_size: 1024 * 1024, // 1MB
      mime_type: 'application/octet-stream',
      base_file_type: 'raw',
      tags: {
        name: 'Sample File',
        description: 'This is a sample file for demonstration purposes',
        author: 'Demo User',
        version: '1.0'
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
  } catch (err) {
    console.error('Failed to load file:', err)
    error.value = err.message || 'Failed to load file'
  } finally {
    loading.value = false
  }
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}

function goBack() {
  router.back()
}

// Lifecycle
onMounted(() => {
  loadFile()
})
</script>

<style scoped>
.file-viewer {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

.viewer-header {
  background: white;
  border-bottom: 1px solid #e9ecef;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  flex-shrink: 0;
}

.file-details {
  min-width: 0;
}

.file-name {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  word-break: break-word;
}

.file-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #666;
}

.file-type {
  text-transform: uppercase;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.edit-btn, .back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s;
}

.edit-btn {
  background: #007bff;
  color: white;
  border: none;
}

.edit-btn:hover {
  background: #0056b3;
}

.back-btn {
  background: none;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.back-btn:hover {
  background: #6c757d;
  color: white;
}

.viewer-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.loading, .error, .not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error i, .not-found i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #dc3545;
}

.not-found i {
  color: #6c757d;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #0056b3;
}

.file-content {
  max-width: 1000px;
  margin: 0 auto;
}

.raster-viewer, .vector-viewer, .generic-viewer {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: #f8f9fa;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  margin-top: 1rem;
  color: #6c757d;
}

.preview-placeholder i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.file-tags {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.tag-item {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.tag-key {
  font-weight: 500;
  color: #495057;
  min-width: 80px;
}

.tag-value {
  color: #333;
  word-break: break-word;
}
</style> 