<template>
  <div class="file-editor">

    <!-- Header with back button -->
    <div class="editor-header">
      <button class="back-btn" @click="backButton()">
        <svg width="16" height="16" viewBox="0 0 16 16">
          <path d="M10 2L4 8L10 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Назад до списку
      </button>
      <div class="file-info" v-if="file">
        <div class="file-icon" v-html="fileIcon"></div>
        <div class="file-details">
          <h2 class="file-name">{{ file.value?.name }}</h2>
          <div class="file-meta">
            <span class="file-type">{{ fileTypeLabel }}</span>
            <span class="file-id">ID: {{ file.id }}</span>
          </div>
        </div>
      </div>
      <div v-else-if="loading" class="file-details">Завантаження...</div>
      <div v-else-if="error" class="file-details">Помилка: {{ error }}</div>
    </div>

    <!-- Main content area with editor and tags -->
    <div class="editor-content" v-if="file">
      <!-- Left panel: Tags editor -->
      <div class="left-panel" :class="{ 'collapsed': sidebarCollapsed }">
        <ObjectTypeSelector 
          v-model:selectedType="selectedType" 
          :currentFile="file.value"
          @menu-open="menuOpen = $event"
          @type-changed="handleTypeChange"
        />
        <TagList 
          v-if="!menuOpen" 
          :fields="selectedFields" 
          :currentFile="file"
          :selectedType="selectedType"
          :allFieldDefinitions="allFieldDefinitions"
          :change-tracker="changeTracker"
          @tags-updated="handleTagsUpdated"
        />
        
        <!-- File upload section moved to left panel -->
        <div class="upload-section">
          <div class="upload-header">
            <h3>Завантажити нову версію</h3>
            <p>Виберіть файл для заміни поточної версії</p>
          </div>
          
          <div class="upload-area" :class="{ 'drag-over': isDragOver }" @drop="handleDrop" @dragover="handleDragOver" @dragleave="handleDragLeave">
            <input 
              ref="fileInput" 
              type="file" 
              class="file-input" 
              @change="handleFileSelect"
              accept="*/*"
            />
            
            <div class="upload-content">
              <div class="upload-icon">
                <svg width="48" height="48" viewBox="0 0 48 48">
                  <path d="M24 8v20M12 20l12 12 12-12" stroke="#007bff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                  <rect x="8" y="32" width="32" height="8" rx="2" fill="#007bff"/>
                </svg>
              </div>
              <div class="upload-text">
                <p class="upload-title">Перетягніть файл сюди або натисніть для вибору</p>
                <p class="upload-subtitle">Підтримуються всі типи файлів</p>
              </div>
            </div>
          </div>

          <!-- Upload progress and status -->
          <div v-if="uploadStatus" class="upload-status">
            <div v-if="uploadStatus.state === 'uploading'" class="upload-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: uploadStatus.progress + '%' }"></div>
              </div>
              <span class="progress-text">{{ uploadStatus.progress }}%</span>
            </div>
            <div v-else-if="uploadStatus.state === 'success'" class="upload-success">
              <svg width="16" height="16" viewBox="0 0 16 16">
                <path d="M3 8l3 3 7-7" stroke="#28a745" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Файл успішно завантажено</span>
            </div>
            <div v-else-if="uploadStatus.state === 'error'" class="upload-error">
              <svg width="16" height="16" viewBox="0 0 16 16">
                <path d="M8 2L2 8l6 6 6-6-6-6z" fill="#dc3545"/>
                <path d="M8 6v4M8 12h0" stroke="#fff" stroke-width="1" fill="none"/>
              </svg>
              <span>{{ uploadStatus.error }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right panel: File editor -->
      <div class="right-panel">
        <!-- Right panel header with commit functionality -->
        <div class="right-panel-header">
          <div class="panel-actions">
            <div v-if="changeTracker.hasChanges.value" class="changes-info">
              <span class="changes-count">{{ changeTracker.changeCount.value }} change{{ changeTracker.changeCount.value !== 1 ? 's' : '' }} pending</span>
            </div>
            
            <button 
              v-if="changeTracker.hasChanges.value"
              class="pure-button pure-button-primary" 
              @click="handleCommit"
              :disabled="changeTracker.isCommitting.value"
            >
              <i v-if="changeTracker.isCommitting.value" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-check"></i>
              {{ changeTracker.isCommitting.value ? 'Committing...' : 'Commit Changes' }}
            </button>
            
            <div v-else class="no-changes">
              <span>No pending changes</span>
            </div>
          </div>
        </div>

        <div class="editor-main">
          <!-- Interactive Map for GeoTIFF files -->
          <InteractiveMap 
            v-if="isGeoTiff && file"
            :fileId="file.id"
            :filename="file.name"
            class="interactive-map-container"
          />
          
          <!-- Collection view -->
          <div v-else-if="isCollection && file" class="collection-view">
            <div class="collection-header">
              <div class="collection-icon" v-html="fileIcon"></div>
              <div class="collection-info">
                <h3>Колекція: {{ file.name }}</h3>
                <p>Кількість елементів: {{ file.entries?.length || 0 }}</p>
              </div>
            </div>
            <div class="collection-content">
              <p>Це колекція файлів. Ви можете редагувати теги колекції в панелі зліва.</p>
              <p class="collection-note">Для перегляду вмісту колекції використовуйте кнопку "Переглянути вміст" у списку файлів.</p>
              
              <!-- Add existing files to collection -->
              <div class="add-files-section">
                <h4>Додати існуючі файли до колекції</h4>
                <p>Виберіть файли з дерева файлів для додавання до цієї колекції:</p>
                
                <button @click="showFileChooser = true" class="open-chooser-btn">
                  <i class="fas fa-folder-open"></i>
                  Відкрити вибір файлів
                </button>
                
                <div v-if="addFileStatus" class="add-file-status">
                  <div v-if="addFileStatus.state === 'success'" class="add-file-success">
                    <svg width="16" height="16" viewBox="0 0 16 16">
                      <path d="M3 8l3 3 7-7" stroke="#28a745" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>{{ addFileStatus.message }}</span>
                  </div>
                  <div v-else-if="addFileStatus.state === 'error'" class="add-file-error">
                    <svg width="16" height="16" viewBox="0 0 16 16">
                      <path d="M8 2L2 8l6 6 6-6-6-6z" fill="#dc3545"/>
                      <path d="M8 6v4M8 12h0" stroke="#fff" stroke-width="1" fill="none"/>
                    </svg>
                    <span>{{ addFileStatus.error }}</span>
                  </div>
                </div>
              </div>
              
              <!-- File Chooser Modal -->
              <div v-if="showFileChooser" class="file-chooser-modal" @click="closeFileChooser">
                <div class="file-chooser-container" @click.stop>
                  <FileChooser 
                    :commit-id="props.commitId"
                    :current-path="fileChooserPath"
                    @close="closeFileChooser"
                    @files-added="handleFilesAdded"
                    @update:current-path="fileChooserPath = $event"
                  />
                </div>
              </div>
            </div>
          </div>
          
          <!-- Placeholder for other file types -->
          <div v-else class="editor-placeholder">
            <div class="placeholder-icon">
              <svg width="64" height="64" viewBox="0 0 64 64">
                <rect x="8" y="8" width="48" height="48" rx="8" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
                <path d="M20 24h24M20 32h16M20 40h12" stroke="#6c757d" stroke-width="2" fill="none"/>
              </svg>
            </div>
            <h3>Редактор файлу</h3>
            <p>Тут буде розміщено інлайн редактор для файлу {{ file.value?.name }}</p>
            <p class="placeholder-note">Функціональність редактора буде додана пізніше</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ObjectTypeSelector from './ObjectTypeSelector.vue'
import TagList from './TagList.vue'
import InteractiveMap from './InteractiveMap.vue'
import FileChooser from './FileChooser.vue'
import { matchTagsToPreset } from '../utils/tagMatcher.js'
import { loadFieldDefinitions, resolveFields } from '../utils/fieldResolver.js'
import apiService from '../services/api.js'
import { watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  changeTracker: {
    type: Object,
    required: true
  },
  commitId: {
    type: [String, Number],
    required: true
  },
  treePath: {
    type: [String, Number, Array],
    required: true
  }
})

const emit = defineEmits(['back', 'file-uploaded', 'tags-updated', 'file-updated'])

const fileInput = ref(null)
const isDragOver = ref(false)
const uploadStatus = ref(null)
const file = ref(null)
const loading = ref(false)
const error = ref(null)

// Add existing file to collection state
const showFileChooser = ref(false)
const fileChooserPath = ref('')
const isAddingFile = ref(false)
const addFileStatus = ref(null)

// Tags editor state
const selectedType = ref(null)
const menuOpen = ref(false)
const allPresets = ref([])
const allFieldDefinitions = ref({})
const sidebarCollapsed = ref(false)


const router = useRouter()

// Convert treePath array to string for API calls
const treePathString = computed(() => {
  if (Array.isArray(props.treePath)) {
    return props.treePath.join('/')
  }
  return props.treePath || ''
})

// Dynamically import all presets
const presetModules = import.meta.glob('../data/presets/*/*.json', { eager: true })

function backButton() {
  router.go(-1); 
}

async function loadFile() {
  loading.value = true
  error.value = null
  try {
    const entry = await apiService.getTreeEntry(props.commitId, treePathString.value)
    if (!entry || !entry.object) throw new Error('File not found')
    file.value = entry.object
    // Store the object type for collection detection
    file.value.object_type = entry.object_type

    // Set initial type based on file tags
    if (file.value && file.value.tags) {
      const matchedPreset = matchTagsToPreset(file.value.tags, allPresets.value)
      selectedType.value = matchedPreset
    }
  } catch (e) {
    error.value = e.message || 'Failed to load file'
    file.value = null
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  allPresets.value = Object.values(presetModules)
  allFieldDefinitions.value = await loadFieldDefinitions()
  await loadFile()
})

// Reload file when treePath or commitId changes
watch(() => [props.treePath, props.commitId], loadFile)

// Resolve field keys to full field definitions
const selectedFields = computed(() => {
  if (!selectedType.value || !selectedType.value.fields) {
    return []
  }
  return resolveFields(selectedType.value.fields, allFieldDefinitions.value)
})

// File type detection and icon
const fileType = computed(() => {
  // Check if this is a collection first
  if (file.value?.object_type === 'tree') {
    return 'collection'
  }
  return file.value?.base_file_type || 'raw'
})

const fileTypeLabel = computed(() => {
  const labels = {
    'raster': 'Геоприв\'язане растрове зображення',
    'vector': 'Геоприв\'язаний векторний файл', 
    'raw': 'Звичайний файл',
    'collection': 'Колекція файлів',
  }
  return labels[fileType.value] || 'Невідомий тип'
})

const fileIcon = computed(() => {
  switch (fileType.value) {
    case 'raster':
      return `<svg width="32" height="32" viewBox="0 0 32 32">
        <rect x="2" y="6" width="28" height="20" rx="3" fill="#e0e7ef" stroke="#7faaff" stroke-width="1.5"/>
        <circle cx="11" cy="19" r="3" fill="#7faaff"/>
        <rect x="16" y="13" width="10" height="6" fill="#b3d1ff"/>
        <path d="M4 4l4 4M8 4l4 4M12 4l4 4" stroke="#7faaff" stroke-width="1" fill="none"/>
      </svg>`
    case 'vector':
      return `<svg width="32" height="32" viewBox="0 0 32 32">
        <rect x="2" y="6" width="28" height="20" rx="3" fill="#e0f7e7" stroke="#2ecc71" stroke-width="1.5"/>
        <circle cx="10" cy="22" r="2.5" fill="#2ecc71"/>
        <circle cx="22" cy="11" r="2.5" fill="#2ecc71"/>
        <line x1="10" y1="22" x2="22" y2="11" stroke="#27ae60" stroke-width="1.5"/>
        <path d="M4 4l4 4M8 4l4 4M12 4l4 4" stroke="#2ecc71" stroke-width="1" fill="none"/>
      </svg>`
    case 'raw':
      return `<svg width="32" height="32" viewBox="0 0 32 32">
        <rect x="4" y="6" width="24" height="20" rx="3" fill="#f7f7e7" stroke="#6c757d" stroke-width="1.5"/>
        <rect x="9" y="13" width="14" height="1.5" fill="#6c757d"/>
        <rect x="9" y="18" width="8" height="1.5" fill="#6c757d"/>
        <rect x="9" y="23" width="12" height="1.5" fill="#6c757d"/>
      </svg>`
    case 'collection':
      return `<svg width="32" height="32" viewBox="0 0 32 32">
        <rect x="3" y="8" width="26" height="18" rx="3" fill="#ffe082" stroke="#ffb300" stroke-width="1.5"/>
        <path d="M3 8l4-6h12l4 6" fill="#ffe082" stroke="#ffb300" stroke-width="1.5"/>
        <rect x="8" y="14" width="4" height="2" fill="#ffb300"/>
        <rect x="14" y="14" width="4" height="2" fill="#ffb300"/>
        <rect x="20" y="14" width="4" height="2" fill="#ffb300"/>
        <rect x="8" y="18" width="4" height="2" fill="#ffb300"/>
        <rect x="14" y="18" width="4" height="2" fill="#ffb300"/>
        <rect x="20" y="18" width="4" height="2" fill="#ffb300"/>
      </svg>`
    default:
      return `<svg width="32" height="32" viewBox="0 0 32 32">
        <rect x="6" y="6" width="20" height="20" rx="5" fill="#f8f9fa" stroke="#dee2e6" stroke-width="1.5"/>
        <path d="M12 12h8M12 16h6M12 20h4" stroke="#6c757d" stroke-width="1.5" fill="none"/>
      </svg>`
  }
})

// Check if file is a GeoTIFF (raster type)
const isGeoTiff = computed(() => {
  return fileType.value === 'raster'
})

// Check if object is a collection
const isCollection = computed(() => {
  return fileType.value === 'collection'
})

// Tags editor functions
function handleTypeChange(newType) {
  if (file.value && newType) {
    // Create new tags based on the selected type
    const newTags = { ...newType.tags }
    // Preserve the name tag if it exists
    if (file.value.tags && file.value.tags.name) {
      newTags.name = file.value.tags.name
    }
    // Add change to tracker
    props.changeTracker.addChange({
      type: 'tags',
      fileId: file.value.id,
      data: newTags
    })
    // Update the local file object to reflect changes immediately
    file.value.tags = { ...newTags }
  }
}

function handleTagsUpdated(newTags) {
  if (!file.value) return
  props.changeTracker.addChange({
    type: 'tags',
    fileId: file.value.id,
    data: newTags
  })
  file.value.tags = { ...newTags }
}

// File upload handlers
function handleDragOver(event) {
  event.preventDefault()
  isDragOver.value = true
}

function handleDragLeave(event) {
  event.preventDefault()
  isDragOver.value = false
}

function handleDrop(event) {
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer.files
  if (files.length > 0) {
    processFile(files[0])
  }
}

function handleFileSelect(event) {
  const files = event.target.files
  if (files.length > 0) {
    processFile(files[0])
  }
}

async function processFile(uploadFileObj) {
  uploadStatus.value = { state: 'uploading', progress: 0 }
  try {
    // Prepare tags for the new file
    const tags = {
      name: uploadFileObj.name,
    }
    // Upload file via API
    const uploadedFile = await apiService.uploadFile(uploadFileObj, tags, props.commitId, '', uploadFileObj.name)
    uploadStatus.value = { state: 'success' }
    emit('file-uploaded', uploadedFile)
    setTimeout(() => {
      uploadStatus.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }, 3000)
  } catch (error) {
    console.error('Upload failed:', error)
    uploadStatus.value = { 
      state: 'error', 
      error: error.message || 'Помилка завантаження файлу'
    }
    setTimeout(() => {
      uploadStatus.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }, 5000)
  }
}

function triggerFileSelect() {
  fileInput.value?.click()
}

async function handleCommit() {
  const result = await props.changeTracker.commitChanges(async (change) => {
    if (change.type === 'tags') {
      const updatedEntry = await apiService.updateObjectInTree(props.commitId, treePathString.value, change.data)
      // Update the local file object with the response
      if (updatedEntry && updatedEntry.object && file.value) {
        Object.assign(file.value, updatedEntry.object)
      }
    }
  })
  if (result.success) {
    emit('tags-updated', file.value?.tags, true)
    emit('file-updated', file.value)
  } else {
    console.error('Commit failed:', result.error)
    // You might want to show an error message to the user
  }
}

function closeFileChooser() {
  showFileChooser.value = false
  fileChooserPath.value = ''
}

async function handleFilesAdded(selectedFiles) {
  isAddingFile.value = true
  addFileStatus.value = null
  
  try {
    // Clone each selected file to the current collection
    for (const selectedFile of selectedFiles) {
      const sourcePath = selectedFile.fullPath
      
      await apiService.cloneObjectInTree(props.commitId, sourcePath, treePathString.value)
    }
    
    addFileStatus.value = {
      state: 'success',
      message: `${selectedFiles.length} файл(ів) успішно додано до колекції "${file.value.name}"`
    }
    
    // Reload the file to update the entries count
    await loadFile()
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      addFileStatus.value = null
    }, 3000)
    
  } catch (error) {
    console.error('Failed to add files to collection:', error)
    addFileStatus.value = {
      state: 'error',
      error: error.message || 'Помилка додавання файлів до колекції'
    }
    
    // Clear error message after 5 seconds
    setTimeout(() => {
      addFileStatus.value = null
    }, 5000)
  } finally {
    isAddingFile.value = false
  }
}
</script>

<style scoped>
.file-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fafbfc;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #eee;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  color: #666;
  transition: all 0.15s;
}

.back-btn:hover {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-name {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.file-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #666;
}

.file-type {
  font-weight: 500;
}

.editor-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 320px;
  background: #f8f9fa;
  border-right: 1px solid #eee;
  overflow-y: auto;
  transition: width 0.3s ease;
}

.left-panel.collapsed {
  width: 60px;
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-main {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.editor-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.placeholder-icon {
  margin-bottom: 1rem;
  opacity: 0.6;
}

.editor-placeholder h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.editor-placeholder p {
  margin: 0.25rem 0;
}

.placeholder-note {
  font-size: 0.9rem;
  font-style: italic;
  color: #999;
}

.upload-section {
  background: white;
  border-top: 1px solid #eee;
  padding: 1rem;
  margin-top: 1rem;
}

.upload-header {
  margin-bottom: 0.75rem;
}

.upload-header h3 {
  margin: 0 0 0.25rem 0;
  color: #333;
  font-size: 1rem;
}

.upload-header p {
  margin: 0;
  color: #666;
  font-size: 0.8rem;
}

.upload-area {
  position: relative;
  border: 2px dashed #ddd;
  border-radius: 6px;
  padding: 1rem;
  text-align: center;
  transition: all 0.15s;
  cursor: pointer;
  min-height: 80px;
}

.upload-area:hover {
  border-color: #007bff;
  background: #f8f9ff;
}

.upload-area.drag-over {
  border-color: #007bff;
  background: #f0f8ff;
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.upload-content {
  pointer-events: none;
}

.upload-icon {
  margin-bottom: 0.5rem;
}

.upload-icon svg {
  width: 32px;
  height: 32px;
}

.upload-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: #333;
  margin: 0 0 0.25rem 0;
}

.upload-subtitle {
  color: #666;
  margin: 0;
  font-size: 0.75rem;
}

.upload-status {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.2s;
}

.progress-text {
  font-size: 0.8rem;
  color: #666;
  min-width: 35px;
}

.upload-success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.upload-error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.upload-success svg,
.upload-error svg {
  flex-shrink: 0;
}

.right-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #eee;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.panel-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.changes-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.changes-count {
  font-size: 0.9rem;
  color: #666;
}

.pure-button {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: #666;
  transition: all 0.15s;
}

.pure-button:hover {
  color: #007bff;
}

.pure-button-primary {
  background: #007bff;
  color: white;
  border-radius: 6px;
  padding: 0.5rem 1rem;
}

.pure-button-primary:hover {
  background: #0056b3;
}

.no-changes {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.no-changes span {
  font-size: 0.9rem;
  color: #666;
}

.interactive-map-container {
  margin: 1rem;
  border-radius: 8px;
  overflow: hidden;
  height: 600px;
}

/* Collection view styles */
.collection-view {
  padding: 2rem;
  background: white;
  border-radius: 8px;
  margin: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.collection-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #eee;
}

.collection-icon {
  flex-shrink: 0;
}

.collection-icon svg {
  width: 48px;
  height: 48px;
}

.collection-info h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.collection-info p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.collection-content {
  color: #555;
  line-height: 1.6;
}

.collection-content p {
  margin: 0 0 1rem 0;
}

.collection-note {
  font-size: 0.9rem;
  color: #888;
  font-style: italic;
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  border-left: 4px solid #ffb300;
}

/* Add files section styles */
.add-files-section {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.add-files-section h4 {
  margin: 0 0 0.75rem 0;
  color: #333;
  font-size: 1.1rem;
  font-weight: 600;
}

.add-files-section p {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 0.9rem;
}

.open-chooser-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.15s;
  white-space: nowrap;
  margin-bottom: 1rem;
}

.open-chooser-btn:hover {
  background: #0056b3;
}

.file-chooser-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.file-chooser-container {
  max-width: 90vw;
  max-height: 90vh;
}

.add-file-status {
  padding: 0.75rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.add-file-success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.add-file-error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.add-file-success svg,
.add-file-error svg {
  flex-shrink: 0;
}
</style> 