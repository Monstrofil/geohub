<template>
  <VueFinalModal
    :click-to-close="true"
    :esc-to-close="true"
    classes="upload-modal-wrapper"
    content-class="pure-g"
    overlay-transition="vfm-fade"
    content-transition="vfm-scale"
    @closed="handleClose"
  >
    <div class="pure-u-1 pure-u-md-1-4 pure-u-lg-1-3"></div>
    <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-1-3">
      <div class="upload-modal">
        <div class="modal-header">
          <h3>Додати новий об'єкт</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
      
      <form @submit.prevent="handleUpload" class="pure-form pure-form-stacked">
        <!-- Object Type Selection -->
        <div class="form-group">
          <label>Тип об'єкта:</label>
          <div class="type-selector">
            <label class="type-option">
              <input 
                type="radio" 
                v-model="objectType" 
                value="file" 
              />
              <span class="type-label">
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <path d="M3 2h6l2 2v8H3z" fill="none" stroke="currentColor" stroke-width="1.5"/>
                </svg>
                Файл
              </span>
            </label>
            <label class="type-option">
              <input 
                type="radio" 
                v-model="objectType" 
                value="collection" 
              />
              <span class="type-label">
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <path d="M2 4h12v8H2z" fill="#ffe082" stroke="#ffb300" stroke-width="1"/>
                  <path d="M2 4l2-2h4l2 2" fill="#ffe082" stroke="#ffb300" stroke-width="1"/>
                </svg>
                Колекція
              </span>
            </label>
            <label class="type-option">
              <input 
                type="radio" 
                v-model="objectType" 
                value="folder" 
              />
              <span class="type-label">
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <path d="M2 4h12v8H2z" fill="#e3f2fd" stroke="#2196f3" stroke-width="1"/>
                  <path d="M2 4l2-2h4l2 2" fill="#e3f2fd" stroke="#2196f3" stroke-width="1"/>
                  <path d="M6 7h4M6 9h3" stroke="#2196f3" stroke-width="1"/>
                </svg>
                Папка (масове завантаження)
              </span>
            </label>
          </div>
        </div>

        <!-- File Upload Section -->
        <div v-if="objectType === 'file'" class="form-group">
          <label>Виберіть файл для завантаження:</label>
          <input type="file" ref="fileInput" @change="onFileChange" required />
        </div>

        <!-- Folder Upload Section -->
        <div v-if="objectType === 'folder'" class="form-group">
          <label>Виберіть папку для завантаження:</label>
          <input 
            type="file" 
            ref="folderInput" 
            @change="onFolderChange" 
            webkitdirectory 
            directory 
            multiple 
            required 
          />
          <div v-if="selectedFiles.length > 0" class="folder-preview">
            <p><strong>Обрано файлів:</strong> {{ selectedFiles.length }}</p>
            <div class="folder-structure">
              <div v-for="folder in folderStructure" :key="folder.path" class="folder-item">
                <div class="folder-header">
                  <svg width="16" height="16" viewBox="0 0 16 16">
                    <path d="M2 4h12v8H2z" fill="#ffe082" stroke="#ffb300" stroke-width="1"/>
                    <path d="M2 4l2-2h4l2 2" fill="#ffe082" stroke="#ffb300" stroke-width="1"/>
                  </svg>
                  {{ folder.name }} ({{ folder.files.length }} файлів)
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Collection Name Section -->
        <div v-if="objectType === 'collection'" class="form-group">
          <label>Назва колекції:</label>
          <input v-model="name" type="text" placeholder="Введіть назву колекції" class="form-control" required />
        </div>

        <!-- Name Section (only for files) -->
        <div v-if="objectType === 'file'" class="form-group">
          <label>Назва файлу (необов'язково):</label>
          <input v-model="name" type="text" placeholder="Введіть назву файлу" class="form-control" />
        </div>


        <!-- Progress Section -->
        <div v-if="uploading && uploadProgress.length > 0" class="progress-section">
          <h4>Прогрес завантаження:</h4>
          <div class="progress-list">
            <div 
              v-for="item in uploadProgress" 
              :key="item.id"
              class="progress-item"
              :class="{ 
                'completed': item.status === 'completed',
                'error': item.status === 'error',
                'uploading': item.status === 'uploading'
              }"
            >
              <div class="progress-icon">
                <svg v-if="item.status === 'completed'" width="16" height="16" viewBox="0 0 16 16">
                  <path d="M6 12L2 8L3 7L6 10L13 3L14 4Z" fill="#4caf50"/>
                </svg>
                <svg v-else-if="item.status === 'error'" width="16" height="16" viewBox="0 0 16 16">
                  <path d="M8 2L14 14H2Z" fill="none" stroke="#f44336" stroke-width="1.5"/>
                  <path d="M8 6V9M8 11V12" stroke="#f44336" stroke-width="1.5"/>
                </svg>
                <div v-else class="spinner-small"></div>
              </div>
              <span class="progress-name">{{ item.name }}</span>
              <span class="progress-status">{{ item.statusText }}</span>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button type="button" @click="closeModal" class="cancel-btn">Скасувати</button>
          <button type="submit" :disabled="uploading || !isFormValid" class="upload-btn">
            {{ uploading ? 'Завантаження...' : getUploadButtonText() }}
          </button>
        </div>
        
        <div v-if="uploadError" class="error">{{ uploadError }}</div>
        <div v-if="uploadSuccess" class="success">{{ uploadSuccessMessage }}</div>
      </form>
      </div>
    </div>
  </VueFinalModal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { VueFinalModal } from 'vue-final-modal'
import apiService from '../../../services/api.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  treePath: { type: String, default: '' }
})

const emit = defineEmits(['close', 'upload-success'])

// Form state
const fileInput = ref(null)
const folderInput = ref(null)
const file = ref(null)
const selectedFiles = ref([])
const name = ref('')
const uploading = ref(false)
const uploadError = ref('')
const uploadSuccess = ref(false)
const uploadSuccessMessage = ref('')
const objectType = ref('file') // 'file', 'collection', or 'folder'
const uploadProgress = ref([])

// Computed properties
const folderStructure = computed(() => {
  const folders = new Map()
  
  selectedFiles.value.forEach(file => {
    const pathParts = file.webkitRelativePath.split('/')
    const folderPath = pathParts.slice(0, -1).join('/')
    const folderName = pathParts.slice(0, -1).join('/') || 'Root'
    
    if (!folders.has(folderPath)) {
      folders.set(folderPath, {
        name: folderName,
        path: folderPath,
        files: []
      })
    }
    
    folders.get(folderPath).files.push(file)
  })
  
  return Array.from(folders.values()).sort((a, b) => a.path.localeCompare(b.path))
})

// Form validation
const isFormValid = computed(() => {
  if (objectType.value === 'file') {
    return file.value !== null
  } else if (objectType.value === 'folder') {
    return selectedFiles.value.length > 0
  } else {
    return name.value.trim() !== ''
  }
})

const getUploadButtonText = () => {
  switch (objectType.value) {
    case 'file':
      return 'Завантажити файл'
    case 'collection':
      return 'Створити колекцію'
    case 'folder':
      return `Завантажити папку (${selectedFiles.value.length} файлів)`
    default:
      return 'Завантажити'
  }
}

// Methods
function closeModal() {
  emit('close')
  resetForm()
}

function handleClose() {
  closeModal()
}

function resetForm() {
  file.value = null
  selectedFiles.value = []
  name.value = ''
  uploadError.value = ''
  uploadSuccess.value = false
  uploadSuccessMessage.value = ''
  uploadProgress.value = []
  objectType.value = 'file'
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  if (folderInput.value) {
    folderInput.value.value = ''
  }
}

function onFileChange(event) {
  const selectedFile = event.target.files[0]
  if (selectedFile) {
    file.value = selectedFile
    // Auto-fill name if empty
    if (!name.value) {
      name.value = selectedFile.name
    }
  }
}

function onFolderChange(event) {
  const files = Array.from(event.target.files)
  selectedFiles.value = files
  uploadProgress.value = []
}


async function handleUpload() {
  if (!isFormValid.value) return

  uploading.value = true
  uploadError.value = ''
  uploadSuccess.value = false

  try {
    if (objectType.value === 'file') {
      await uploadFile()
    } else if (objectType.value === 'folder') {
      await uploadFolder()
    } else {
      await createCollection()
    }
  } catch (err) {
    console.error('Upload failed:', err)
    uploadError.value = 'Помилка завантаження: ' + err.message
  } finally {
    uploading.value = false
  }
}

async function uploadFile() {
  // Build tags object
  const tagsObj = {}

  // Add name to tags if provided
  if (name.value.trim()) {
    tagsObj.name = name.value.trim()
  }

  // Convert tree path to parent path (for now, just use "root" since we need collection ID mapping)
  const parentPath = props.treePath || "root"

  const response = await apiService.uploadFile(
    file.value,
    tagsObj,
    parentPath
  )
  
  uploadSuccess.value = true
  uploadSuccessMessage.value = 'Файл успішно завантажено!'
  
  // Emit success event
  emit('upload-success', response)
  
  // Close modal after a short delay
  setTimeout(() => {
    closeModal()
  }, 1500)
}

async function createCollection() {
  var collectionTags = {}

  // Convert tree path to parent path (for now, just use "root" since we need collection ID mapping)
  const parentPath = props.treePath || "root"

  const response = await apiService.createCollection(
    name.value.trim(), 
    collectionTags, 
    parentPath
  )
  
  uploadSuccess.value = true
  uploadSuccessMessage.value = 'Колекцію успішно створено!'
  
  // Emit success event
  emit('upload-success', response)
  
  // Close modal after a short delay
  setTimeout(() => {
    closeModal()
  }, 1500)
}

async function uploadFolder() {
  const parentPath = props.treePath || "root"
  
  // Build folder structure - create collections for directories
  const folderMap = new Map() // path -> collection path
  const pathCollections = new Map() // collection path -> collection info
  
  // First, identify all unique folder paths
  const folderPaths = new Set()
  selectedFiles.value.forEach(file => {
    const pathParts = file.webkitRelativePath.split('/')
    for (let i = 1; i < pathParts.length; i++) {
      const folderPath = pathParts.slice(0, i).join('/')
      folderPaths.add(folderPath)
    }
  })
  
  // Sort paths by depth to create parent collections first
  const sortedFolderPaths = Array.from(folderPaths).sort((a, b) => {
    const depthA = a.split('/').length
    const depthB = b.split('/').length
    return depthA - depthB
  })
  
  uploadProgress.value = []
  let totalOperations = sortedFolderPaths.length + selectedFiles.value.length
  let completedOperations = 0
  
  // Create collections for each folder
  for (const folderPath of sortedFolderPaths) {
    const pathParts = folderPath.split('/')
    const folderName = pathParts[pathParts.length - 1]
    const parentFolderPath = pathParts.slice(0, -1).join('/')
    
    // Determine parent collection path
    let parentCollectionPath = parentPath
    if (parentFolderPath && folderMap.has(parentFolderPath)) {
      parentCollectionPath = folderMap.get(parentFolderPath)
    }
    
    const progressId = `folder-${folderPath}`
    uploadProgress.value.push({
      id: progressId,
      name: `Папка: ${folderName}`,
      status: 'uploading',
      statusText: 'Створення...'
    })
    
    try {
      const response = await apiService.createCollection(
        folderName,
        {name: folderName},
        parentCollectionPath
      )
      
      folderMap.set(folderPath, response.path)
      pathCollections.set(response.path, response)
      
      // Update progress
      const progressItem = uploadProgress.value.find(p => p.id === progressId)
      if (progressItem) {
        progressItem.status = 'completed'
        progressItem.statusText = 'Створено'
      }
      
      completedOperations++
      
    } catch (error) {
      console.error(`Failed to create collection for ${folderPath}:`, error)
      const progressItem = uploadProgress.value.find(p => p.id === progressId)
      if (progressItem) {
        progressItem.status = 'error'
        progressItem.statusText = 'Помилка'
      }
    }
  }
  
  // Upload files to their respective collections
  for (const file of selectedFiles.value) {
    const pathParts = file.webkitRelativePath.split('/')
    const fileName = pathParts[pathParts.length - 1]
    const fileFolderPath = pathParts.slice(0, -1).join('/')
    
    // Determine target collection path
    let targetCollectionPath = parentPath
    if (fileFolderPath && folderMap.has(fileFolderPath)) {
      targetCollectionPath = folderMap.get(fileFolderPath)
    }
    
    const progressId = `file-${file.webkitRelativePath}`
    uploadProgress.value.push({
      id: progressId,
      name: fileName,
      status: 'uploading',
      statusText: 'Завантаження...'
    })
    
    try {
      const tagsObj = { name: fileName }
      
      await apiService.uploadFile(
        file,
        tagsObj,
        targetCollectionPath
      )
      
      // Update progress
      const progressItem = uploadProgress.value.find(p => p.id === progressId)
      if (progressItem) {
        progressItem.status = 'completed'
        progressItem.statusText = 'Завантажено'
      }
      
      completedOperations++
      
    } catch (error) {
      console.error(`Failed to upload file ${fileName}:`, error)
      const progressItem = uploadProgress.value.find(p => p.id === progressId)
      if (progressItem) {
        progressItem.status = 'error'
        progressItem.statusText = 'Помилка'
      }
    }
  }
  
  uploadSuccess.value = true
  uploadSuccessMessage.value = `Папку завантажено! Створено ${sortedFolderPaths.length} колекцій та завантажено ${selectedFiles.value.length} файлів.`
  
  // Emit success event
  emit('upload-success', { type: 'folder', collections: pathCollections.size, files: selectedFiles.value.length })
  
  // Close modal after a delay
  setTimeout(() => {
    closeModal()
  }, 3000)
}

// Reset form when modal opens/closes
watch(() => props.show, (newValue) => {
  if (!newValue) {
    resetForm()
  }
})
</script>

<style scoped>
.upload-modal-wrapper {
  align-items: center;
}

.upload-modal {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 1rem;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

/* File input styling */
input[type="file"] {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 1rem;
  background: white;
  cursor: pointer;
}

input[type="file"]:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}


.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  font-weight: 500;
  font-size: 1rem;
  transition: all 0.15s;
}

.cancel-btn:hover {
  background: #5a6268;
}

.upload-btn {
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  font-weight: 500;
  font-size: 1rem;
  transition: all 0.15s;
}

.upload-btn:hover:not(:disabled) {
  background: #0056b3;
}

.upload-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  color: #dc3545;
  margin-top: 1rem;
  padding: 0.75rem;
  background: #f8d7da;
  border-radius: 6px;
  border: 1px solid #f5c6cb;
}

.success {
  color: #155724;
  margin-top: 1rem;
  padding: 0.75rem;
  background: #d4edda;
  border-radius: 6px;
  border: 1px solid #c3e6cb;
}

/* Type selector styles */
.type-selector {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.type-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.75rem 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  transition: all 0.15s;
  background: white;
}

.type-option:hover {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

.type-option input[type="radio"] {
  display: none;
}

.type-option input[type="radio"]:checked + .type-label {
  color: #007bff;
  font-weight: 600;
}

.type-option:has(input[type="radio"]:checked) {
  border-color: #007bff;
  background: #f8f9ff;
}

.type-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #333;
  transition: all 0.15s;
}

/* Folder upload styles */
.folder-preview {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
}

.folder-structure {
  margin-top: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
}

.folder-item {
  margin-bottom: 0.5rem;
}

.folder-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #666;
  padding: 0.25rem 0;
}

/* Progress styles */
.progress-section {
  margin: 1.5rem 0;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  max-height: 300px;
  overflow-y: auto;
}

.progress-section h4 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1rem;
}

.progress-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: 4px;
  background: white;
  border: 1px solid #dee2e6;
  transition: all 0.2s;
}

.progress-item.completed {
  border-color: #4caf50;
  background: #f1f8e9;
}

.progress-item.error {
  border-color: #f44336;
  background: #ffebee;
}

.progress-item.uploading {
  border-color: #2196f3;
  background: #e3f2fd;
}

.progress-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
}

.progress-name {
  flex: 1;
  font-weight: 500;
  color: #333;
}

.progress-status {
  font-size: 0.85rem;
  color: #666;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(33, 150, 243, 0.3);
  border-top: 2px solid #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 