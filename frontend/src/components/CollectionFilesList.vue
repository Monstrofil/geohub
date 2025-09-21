<template>
  <div class="collection-files-section">
    <h4>Файли в колекції ({{ collectionFiles.length }})</h4>
    <div v-if="loading" class="loading-files">
      <svg width="16" height="16" viewBox="0 0 16 16" class="spinner">
        <circle cx="8" cy="8" r="7" stroke="#007bff" stroke-width="2" fill="none" stroke-dasharray="32" stroke-dashoffset="32">
          <animate attributeName="stroke-dashoffset" values="32;0;32" dur="1.5s" repeatCount="indefinite"/>
        </circle>
      </svg>
      Завантаження файлів...
    </div>
    <div v-else-if="error" class="files-error">
      <svg width="16" height="16" viewBox="0 0 16 16">
        <path d="M8 2L2 8l6 6 6-6-6-6z" fill="#dc3545"/>
        <path d="M8 6v4M8 12h0" stroke="#fff" stroke-width="1" fill="none"/>
      </svg>
      {{ error }}
    </div>
    <div v-else-if="collectionFiles.length === 0" class="empty-collection">
      <svg width="48" height="48" viewBox="0 0 48 48">
        <rect x="8" y="8" width="32" height="32" rx="4" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
        <path d="M16 20h16M16 28h12M16 36h8" stroke="#6c757d" stroke-width="2" fill="none"/>
      </svg>
      <p>Колекція порожня</p>
      <p class="empty-note">Додайте файли до цієї колекції, використовуючи секцію нижче</p>
    </div>
    <div v-else class="files-list">
      <div 
        v-for="entry in collectionFiles" 
        :key="entry.id"
        class="file-item"
        @click="openFile(entry)"
      >
        <div class="file-icon" v-html="getFileIcon(entry)"></div>
        <div class="file-info">
          <div class="file-name">{{ entry.object?.tags?.name || entry.object?.original_name || entry.path }}</div>
          <div class="file-meta">
            <span class="file-type">{{ getFileTypeLabel(entry) }}</span>
            <span class="file-id">ID: {{ entry.object?.id }}</span>
          </div>
        </div>
        <div class="file-actions">
          <button 
            class="view-btn" 
            @click.stop="openFile(entry)"
            title="Переглянути файл"
          >
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M1 8s3-7 7-7 7 7 7 7-3 7-7 7-7-7-7-7z" stroke="currentColor" stroke-width="1.5" fill="none"/>
              <circle cx="8" cy="8" r="2" fill="currentColor"/>
            </svg>
          </button>
          <button 
            class="edit-btn" 
            @click.stop="editFile(entry)"
            title="Редагувати файл"
          >
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M11 1L15 5L5 15H1V11L11 1Z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M8 4L12 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button 
            class="delete-btn" 
            @click.stop="deleteFile(entry)"
            title="Видалити файл"
          >
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M2 2l12 12M14 2l-12 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '../services/api.js'

const props = defineProps({
  refName: {
    type: [String, Number],
    required: true
  },
  collectionPath: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['files-updated'])

const router = useRouter()

const collectionFiles = ref([])
const loading = ref(false)
const error = ref(null)

async function loadCollectionFiles() {
  loading.value = true
  error.value = null
  try {
    const response = await apiService.getRootContents(0, 1000)
    collectionFiles.value = response.files || []
    emit('files-updated', collectionFiles.value)
  } catch (e) {
    console.error('Failed to load collection files:', e)
    error.value = e.message || 'Помилка завантаження файлів колекції'
  } finally {
    loading.value = false
  }
}

// Helper functions for collection files display
function getFileIcon(entry) {
  const fileType = entry.object?.object_type || 'raw'
  const isTree = entry.object_type === 'tree'
  
  if (isTree) {
    return `<svg width="24" height="24" viewBox="0 0 24 24">
      <rect x="3" y="5" width="18" height="14" rx="2" fill="#ffe082" stroke="#ffb300" stroke-width="1.5"/>
      <path d="M3 5l3-3h12l3 3" fill="#ffe082" stroke="#ffb300" stroke-width="1.5"/>
      <rect x="6" y="9" width="3" height="1.5" fill="#ffb300"/>
      <rect x="11" y="9" width="3" height="1.5" fill="#ffb300"/>
      <rect x="16" y="9" width="3" height="1.5" fill="#ffb300"/>
      <rect x="6" y="12" width="3" height="1.5" fill="#ffb300"/>
      <rect x="11" y="12" width="3" height="1.5" fill="#ffb300"/>
      <rect x="16" y="12" width="3" height="1.5" fill="#ffb300"/>
    </svg>`
  }
  
  switch (fileType) {
    case 'raster':
      return `<svg width="24" height="24" viewBox="0 0 24 24">
        <rect x="2" y="4" width="20" height="16" rx="2" fill="#e0e7ef" stroke="#7faaff" stroke-width="1.5"/>
        <circle cx="8" cy="14" r="2" fill="#7faaff"/>
        <rect x="12" y="10" width="8" height="4" fill="#b3d1ff"/>
        <path d="M3 3l3 3M6 3l3 3M9 3l3 3" stroke="#7faaff" stroke-width="1" fill="none"/>
      </svg>`
    case 'vector':
      return `<svg width="24" height="24" viewBox="0 0 24 24">
        <rect x="2" y="4" width="20" height="16" rx="2" fill="#e0f7e7" stroke="#2ecc71" stroke-width="1.5"/>
        <circle cx="8" cy="16" r="2" fill="#2ecc71"/>
        <circle cx="16" cy="8" r="2" fill="#2ecc71"/>
        <line x1="8" y1="16" x2="16" y2="8" stroke="#27ae60" stroke-width="1.5"/>
        <path d="M3 3l3 3M6 3l3 3M9 3l3 3" stroke="#2ecc71" stroke-width="1" fill="none"/>
      </svg>`
    default:
      return `<svg width="24" height="24" viewBox="0 0 24 24">
        <rect x="3" y="4" width="18" height="16" rx="2" fill="#f7f7e7" stroke="#6c757d" stroke-width="1.5"/>
        <rect x="7" y="10" width="10" height="1" fill="#6c757d"/>
        <rect x="7" y="14" width="6" height="1" fill="#6c757d"/>
        <rect x="7" y="18" width="8" height="1" fill="#6c757d"/>
      </svg>`
  }
}

function getFileTypeLabel(entry) {
  if (entry.object_type === 'tree') {
    return 'Колекція'
  }
  
  const fileType = entry.object?.object_type || 'raw'
  const labels = {
    'raster': 'Геоприв\'язане растрове зображення',
    'vector': 'Геоприв\'язаний векторний файл', 
    'raw': 'Звичайний файл',
  }
  return labels[fileType] || 'Невідомий тип'
}

function openFile(entry) {
  // Navigate to the file in the file list view
  const filePath = props.collectionPath + '/' + entry.path
  router.push({ 
    name: 'FileList', 
    params: { treePath: filePath }
  })
}

function editFile(entry) {
  // Navigate to the file editor
  const filePath = props.collectionPath + '/' + entry.path
  router.push({ 
    name: 'FileEditor', 
    params: { treePath: filePath }
  })
}

async function deleteFile(entry) {
  if (!confirm(`Ви впевнені, що хочете видалити файл "${entry.object?.tags?.name || entry.object?.original_name || entry.path}"?`)) {
    return
  }
  
  try {
    const filePath = props.collectionPath + '/' + entry.path
          await apiService.deleteTreeItem(entry.object.id)
    
    // Reload collection files to update the list
    await loadCollectionFiles()
    
    // Show success message (you could add a toast notification here)
    console.log('File deleted successfully')
  } catch (error) {
    console.error('Failed to delete file:', error)
    alert(`Помилка видалення файлу: ${error.message}`)
  }
}

// Expose reload function for parent component
defineExpose({
  reload: loadCollectionFiles
})

onMounted(() => {
  loadCollectionFiles()
})

// Watch for changes in props
watch(() => [props.refName, props.collectionPath], loadCollectionFiles)
</script>

<style scoped>
/* Collection files section styles */
.collection-files-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.collection-files-section h4 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.1rem;
  font-weight: 600;
}

.loading-files {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  color: #666;
  font-size: 0.9rem;
}

.spinner {
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.files-error {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 6px;
  font-size: 0.9rem;
}

.empty-collection {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
  color: #666;
}

.empty-collection svg {
  margin-bottom: 1rem;
  opacity: 0.6;
}

.empty-collection p {
  margin: 0.5rem 0;
}

.empty-note {
  font-size: 0.9rem;
  color: #888;
  font-style: italic;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: white;
  border: 1px solid #eee;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.file-item:hover {
  border-color: #007bff;
  background: #f8f9ff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
  font-size: 0.9rem;
}

.file-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #666;
}

.file-type {
  font-weight: 500;
}

.file-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.view-btn,
.edit-btn,
.delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  color: #666;
  transition: all 0.15s;
}

.view-btn:hover {
  border-color: #007bff;
  color: #007bff;
  background: #f8f9ff;
}

.edit-btn:hover {
  border-color: #28a745;
  color: #28a745;
  background: #f8fff9;
}

.delete-btn:hover {
  border-color: #dc3545;
  color: #dc3545;
  background: #fff8f8;
}

/* Mobile responsive styles */
@media (max-width: 768px) {
  .collection-files-section {
    margin-top: 1rem;
    padding-top: 1rem;
    width: 100%;
  }
  
  .file-item {
    padding: 0.5rem;
    gap: 0.75rem;
    width: 100%;
    box-sizing: border-box;
  }
  
  .file-name {
    white-space: normal;
    word-break: break-word;
    font-size: 0.85rem;
  }
  
  .file-meta {
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.75rem;
  }
  
  .file-actions {
    gap: 0.25rem;
  }
  
  .view-btn,
  .edit-btn,
  .delete-btn {
    width: 36px;
    height: 36px;
    min-width: 36px;
    min-height: 36px;
  }
}
</style> 