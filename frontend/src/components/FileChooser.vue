<template>
  <div class="file-chooser">
    <div class="chooser-header">
      <h4>Виберіть файли для додавання до колекції</h4>
      <div class="header-actions">
        <span class="selected-count">{{ selectedFiles.length === 1 ? '1 файл обрано' : 'Файл не обрано' }}</span>
        <button @click="clearSelection" class="clear-btn" v-if="selectedFiles.length > 0">
          Очистити
        </button>
        <button @click="$emit('close')" class="close-btn">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <div class="chooser-content">
      <!-- Breadcrumb navigation -->
      <div class="breadcrumb">
        <button 
          @click="navigateToRoot" 
          class="breadcrumb-item"
          :class="{ active: currentPath === '' }"
        >
          Корінь
        </button>
        <span v-for="(segment, index) in pathSegments" :key="index" class="breadcrumb-separator">/</span>
        <button 
          v-for="(segment, index) in pathSegments" 
          :key="index"
          @click="navigateToPath(index)"
          class="breadcrumb-item"
          :class="{ active: index === pathSegments.length - 1 }"
        >
          {{ segment }}
        </button>
      </div>

      <!-- File list -->
      <div class="file-list">
        <div v-if="loading" class="loading">Завантаження...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else-if="files.length === 0" class="empty-state">
          <p>Ця папка порожня</p>
        </div>
        <div v-else class="files-grid">
          <div 
            v-for="entry in files" 
            :key="entry.id"
            class="file-item"
            :class="{ 
              selected: isFileSelected(entry),
              'is-file': entry.object_type === 'file',
              'is-folder': entry.object_type === 'tree'
            }"
            @click="handleItemClick(entry)"
          >
            <div class="file-icon" v-html="getFileIcon(entry)"></div>
            <div class="file-info">
              <div class="file-name">{{ entry.object?.tags?.name || entry.object?.original_name || 'Без назви' }}</div>
              <div class="file-meta">
                <span v-if="entry.object_type === 'file'">{{ formatFileSize(entry.object?.file_size) }}</span>
                <span v-else>{{ entry.object?.entries?.length || 0 }} елементів</span>
              </div>
            </div>
            <div v-if="entry.object_type === 'file'" class="selection-indicator">
              <i v-if="isFileSelected(entry)" class="fas fa-check"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="chooser-footer">
      <div class="selected-files-preview" v-if="selectedFiles.length > 0">
        <div class="preview-title">Обраний файл:</div>
        <div class="preview-list">
          <div 
            v-for="file in selectedFiles" 
            :key="file.entry.id"
            class="preview-item"
          >
            <div class="preview-icon" v-html="getFileIcon(file.entry)"></div>
            <span class="preview-name">{{ file.entry.object?.tags?.name || file.entry.object?.original_name }}</span>
            <button @click="removeFromSelection(file)" class="remove-preview-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>
      <div class="footer-actions">
        <button @click="$emit('close')" class="cancel-btn">Скасувати</button>
        <button 
          @click="addSelectedFiles" 
          class="add-btn"
          :disabled="selectedFiles.length === 0"
        >
          <i class="fas fa-plus"></i>
          Додати файл
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import apiService from '../services/api.js'

const props = defineProps({
  commitId: { type: String, required: true },
  currentPath: { type: String, default: '' }
})

const emit = defineEmits(['close', 'files-added'])

// State
const files = ref([])
const loading = ref(false)
const error = ref(null)
const selectedFiles = ref([])

// Computed
const pathSegments = computed(() => {
  return props.currentPath ? props.currentPath.split('/').filter(Boolean) : []
})

// Methods
async function loadFiles() {
  loading.value = true
  error.value = null
  try {
    const response = await apiService.getObjects(props.commitId, props.currentPath, 0, 100)
    files.value = response.files || []
  } catch (err) {
    console.error('Failed to load files:', err)
    error.value = 'Помилка завантаження файлів: ' + err.message
  } finally {
    loading.value = false
  }
}

function navigateToRoot() {
  emit('update:currentPath', '')
}

function navigateToPath(index) {
  const newPath = pathSegments.value.slice(0, index + 1).join('/')
  emit('update:currentPath', newPath)
}

function handleItemClick(entry) {
  if (entry.object_type === 'tree') {
    // Navigate into folder
    var newPath = `${props.currentPath}/${entry.path}`
    if (newPath.startsWith('/')) {
        newPath = newPath.substring(1);
    }
    console.log('newPath', newPath)
    emit('update:currentPath', newPath)
  } else if (entry.object_type === 'file') {
    // Toggle file selection
    toggleFileSelection(entry)
  }
}

function toggleFileSelection(entry) {
  const index = selectedFiles.value.findIndex(f => f.entry.id === entry.id)
  if (index > -1) {
    selectedFiles.value.splice(index, 1)
  } else {
    // Clear previous selection (only allow 1 file)
    selectedFiles.value = []
    
    // Construct the full path for the entry
    var fullPath = `${props.currentPath}/${entry.path}`
    if (fullPath.startsWith('/')) {
      fullPath = fullPath.substring(1)
    }
    
    // Store both entry and its full path
    selectedFiles.value.push({
      entry: entry,
      fullPath: fullPath
    })
  }
}

function isFileSelected(entry) {
  return selectedFiles.value.some(f => f.entry.id === entry.id)
}

function removeFromSelection(file) {
  const index = selectedFiles.value.findIndex(f => f.entry.id === file.entry.id)
  if (index > -1) {
    selectedFiles.value.splice(index, 1)
  }
}

function clearSelection() {
  selectedFiles.value = []
}

function getFileIcon(entry) {
  if (entry.object_type === 'tree') {
    return `<svg width="20" height="20" viewBox="0 0 20 20">
      <rect x="2" y="6" width="16" height="12" rx="2" fill="#ffe082" stroke="#ffb300" stroke-width="1"/>
      <path d="M2 6l3-4h8l3 4" fill="#ffe082" stroke="#ffb300" stroke-width="1"/>
    </svg>`
  }
  
  const fileType = entry.object?.base_file_type || 'raw'
  switch (fileType) {
    case 'raster':
      return `<svg width="20" height="20" viewBox="0 0 20 20">
        <rect x="2" y="4" width="16" height="12" rx="2" fill="#e0e7ef" stroke="#7faaff" stroke-width="1"/>
        <circle cx="7" cy="11" r="1.5" fill="#7faaff"/>
        <rect x="10" y="7" width="6" height="3" fill="#b3d1ff"/>
      </svg>`
    case 'vector':
      return `<svg width="20" height="20" viewBox="0 0 20 20">
        <rect x="2" y="4" width="16" height="12" rx="2" fill="#e0f7e7" stroke="#2ecc71" stroke-width="1"/>
        <circle cx="6" cy="12" r="1" fill="#2ecc71"/>
        <circle cx="14" cy="6" r="1" fill="#2ecc71"/>
        <line x1="6" y1="12" x2="14" y2="6" stroke="#27ae60" stroke-width="1"/>
      </svg>`
    default:
      return `<svg width="20" height="20" viewBox="0 0 20 20">
        <rect x="3" y="4" width="14" height="12" rx="2" fill="#f7f7e7" stroke="#6c757d" stroke-width="1"/>
        <rect x="6" y="8" width="8" height="0.5" fill="#6c757d"/>
        <rect x="6" y="10" width="5" height="0.5" fill="#6c757d"/>
        <rect x="6" y="12" width="7" height="0.5" fill="#6c757d"/>
      </svg>`
  }
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function addSelectedFiles() {
  if (selectedFiles.value.length === 0) return
  
  // Emit the selected files with their full paths
  emit('files-added', selectedFiles.value)
  clearSelection()
}

// Lifecycle
onMounted(() => {
  loadFiles()
})

watch(() => props.currentPath, () => {
  loadFiles()
})
</script>

<style scoped>
.file-chooser {
  display: flex;
  flex-direction: column;
  height: 500px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  overflow: hidden;
}

.chooser-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.chooser-header h4 {
  margin: 0;
  color: #333;
  font-size: 1rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.selected-count {
  font-size: 0.9rem;
  color: #666;
}

.clear-btn {
  background: none;
  border: 1px solid #dc3545;
  color: #dc3545;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s;
}

.clear-btn:hover {
  background: #dc3545;
  color: white;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: color 0.15s;
}

.close-btn:hover {
  color: #333;
}

.chooser-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.breadcrumb {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  overflow-x: auto;
}

.breadcrumb-item {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: all 0.15s;
  white-space: nowrap;
}

.breadcrumb-item:hover {
  background: #e3f2fd;
}

.breadcrumb-item.active {
  color: #333;
  font-weight: 500;
}

.breadcrumb-separator {
  color: #666;
  margin: 0 0.25rem;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  color: #dc3545;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
}

.file-item:hover {
  border-color: #007bff;
  background: #f8f9ff;
}

.file-item.selected {
  border-color: #007bff;
  background: #e3f2fd;
}

.file-item.is-folder {
  border-color: #ffb300;
}

.file-item.is-folder:hover {
  border-color: #ffb300;
  background: #fffbe6;
}

.file-icon {
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  font-size: 0.8rem;
  color: #666;
}

.selection-indicator {
  flex-shrink: 0;
  color: #007bff;
  font-size: 0.9rem;
}

.chooser-footer {
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
}

.selected-files-preview {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e9ecef;
  max-height: 120px;
  overflow-y: auto;
}

.preview-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: #333;
  margin-bottom: 0.5rem;
}

.preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.preview-icon {
  flex-shrink: 0;
}

.preview-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.remove-preview-btn {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 0.1rem;
  border-radius: 2px;
  font-size: 0.7rem;
}

.remove-preview-btn:hover {
  background: #dc3545;
  color: white;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem;
}

.cancel-btn {
  background: none;
  border: 1px solid #6c757d;
  color: #6c757d;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.cancel-btn:hover {
  background: #6c757d;
  color: white;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.add-btn:hover:not(:disabled) {
  background: #0056b3;
}

.add-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}
</style> 