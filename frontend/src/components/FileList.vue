<template>
  <div class="section section-feature-list">
    <h3>
      <span>Файли ({{ files.length }})</span>
      <div class="file-actions">
        <button @click="handleRefresh" class="action-btn refresh-btn" :disabled="loading" title="Оновити список файлів">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M3.5 10A6.5 6.5 0 0110 3.5c1.61 0 3.09.59 4.23 1.57M16.5 10A6.5 6.5 0 0110 16.5c-1.61 0-3.09-.59-4.23-1.57" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14.5 2.5v3.5h-3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M5.5 17.5v-3.5h3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Оновити
        </button>
        <button v-if="isAuthenticated" @click="startUpload" class="action-btn upload-btn" title="Завантажити новий файл або створити колекцію">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M10 15V5M10 5L6 9M10 5l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="4" y="15" width="12" height="2" rx="1" fill="currentColor"/>
          </svg>
          Додати
        </button>
        <router-link v-else :to="loginUrl" class="action-btn login-btn" title="Увійти щоб завантажувати файли">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="16,17 21,12 16,7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Увійти
        </router-link>
      </div>
    </h3>
    
    <!-- Breadcrumb navigation -->
    <div class="breadcrumb">
      <button 
        @click="navigateToRoot" 
        class="breadcrumb-item"
        :class="{ active: treePathString === '', 'drop-target': isRootDropTarget, 'moving': isMovingToRoot }"
        @dragover="handleRootDragOver"
        @drop="handleRootDrop"
        @dragenter="handleRootDragEnter"
        @dragleave="handleRootDragLeave"
      >
        <span v-if="isMovingToRoot" class="loading-text">
          <div class="spinner-small"></div>
          Moving to Root...
        </span>
        <span v-else>Корінь</span>
      </button>
      <template v-for="(segment, index) in pathSegments" :key="index">
        <span class="breadcrumb-separator">/</span>
        <button 
          @click="navigateToPath(segment.path)"
          class="breadcrumb-item"
          :class="{ active: index === pathSegments.length - 1 }"
        >
          {{ segment.name }}
        </button>
      </template>
    </div>
    
    <div v-if="loading" class="loading">Завантаження файлів...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="files.length === 0" class="empty-state">
      <div class="empty-icon">📁</div>
      <h3>Папка порожня</h3>
      <p v-if="treePathString === ''">
        У кореневій папці поки немає файлів або папок. 
        <br>Створіть нову колекцію або завантажте файл, щоб почати роботу.
      </p>
      <p v-else>
        У папці "" поки немає файлів.
        <br>Перейдіть до батьківської папки або створіть новий вміст.
      </p>
      <div class="empty-actions">
        <button v-if="isAuthenticated" @click="startUpload" class="action-btn upload-btn" title="Додати файл або колекцію">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M10 15V5M10 5L6 9M10 5l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="4" y="15" width="12" height="2" rx="1" fill="currentColor"/>
          </svg>
          Додати файл
        </button>
        <router-link v-else :to="loginUrl" class="action-btn login-btn" title="Увійти щоб завантажувати файли">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="16,17 21,12 16,7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Увійти щоб додати файли
        </router-link>
      </div>
    </div>
    <div v-else class="disclosure-wrap disclosure-wrap-feature_list">
      <div class="file-list-layout">
        <!-- Main content area -->
        <div 
          class="file-list-main"
          @dragover="handleMainDragOver"
          @drop="handleMainDrop"
          @dragenter="handleMainDragEnter"
          @dragleave="handleMainDragLeave"
          :class="{ 'drop-zone-active': isMainDropZone, 'moving': isMovingToMain }"
        >
          <div class="pure-g feature-list">
            <div 
              v-for="entry in files" 
              :key="entry.id"
              class="pure-u-1 pure-u-lg-1-2 pure-u-xl-1-3"
            >
              <Card
                :path="entry.path"
                :file="entry.object"
                :name="getDisplayName(entry.object)"
                :tree-path="treePathString"
                :ref-name="entry.object?.name || entry.id"
                :selected="selectedEntry && selectedEntry.object && selectedEntry.object.id === entry.object?.id"
                :move-blocked="isMoveInProgress"
                @click="selectFile(entry.object)"
                @file-selected="handleFileSelected"
                @removed="handleObjectRemoved"
                @cloned="handleObjectCloned"
                @move-start="handleMoveStart"
                @move-end="handleMoveEnd"
                @item-moved="handleItemMoved"
                @moved="handleModalMoved"
              />
            </div>
          </div>
        </div>
        
        <!-- Collection details sidebar -->
        <div class="file-list-sidebar">
          <CollectionDetails 
            :item="leaf"
            :files="files"
          />
        </div>
      </div>
    </div>

    <!-- Upload Modal -->
    <UploadModal 
      :show="showUploadModal"
      :tree-path="treePathString"
      @close="closeModal"
      @upload-success="handleUploadSuccess"
    />


  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Card from './Card.vue'
import UploadModal from './UploadModal.vue'
import CollectionDetails from './CollectionDetails.vue'
import apiService from '../services/api.js'
import { getDisplayName } from '../utils/fileHelpers.js'
import { isAuthenticated } from '../stores/auth.js'

const props = defineProps({
  treePath: {type: [String, Array], required: false},
  selectedEntry: { type: Object, default: null },
  changeTracker: { type: Object, required: false }
})

const emit = defineEmits(['refresh', 'select-file', 'file-selected', 'files-loaded', 'file-uploaded', 'branch-created', 'object-removed', 'object-cloned'])

const router = useRouter()
const route = useRoute()

// Create login URL with current path as redirect
const loginUrl = computed(() => {
  const redirectParam = encodeURIComponent(route.fullPath)
  return `/login?redirect=${redirectParam}`
})

const files = ref([])
const leaf = ref({})
const loading = ref(false)
const error = ref(null)

// Upload modal state
const showUploadModal = ref(false)

// Drag and drop state
const isMainDropZone = ref(false)
const mainDragCounter = ref(0)
const isRootDropTarget = ref(false)
const rootDragCounter = ref(0)
const isMovingToMain = ref(false)
const isMovingToRoot = ref(false)
const isMoveInProgress = ref(false)

// Convert treePath array to string for API calls
const treePathString = computed(() => {
  if (Array.isArray(props.treePath)) {
    return props.treePath.join('/')
  }
  return props.treePath || ''
})

// Breadcrumb path segments
const pathSegments = computed(() => {
  if (!treePathString.value || treePathString.value === 'root') {
    return []
  }
  
  // Split LTREE path by dots and create breadcrumb segments
  const parts = treePathString.value.split('.').filter(Boolean)
  
  // Skip the 'root' part and create meaningful segments
  const segments = []
  if (parts.length > 1) {
    for (let i = 1; i < parts.length; i++) {
      segments.push({
        name: `Collection ${i}`, // You could look up actual collection names
        path: parts.slice(0, i + 1).join('.')
      })
    }
  }
  
  return segments
})

async function loadFiles() {
  loading.value = true
  error.value = null
  try {
    let response = await apiService.getCollectionContents(treePathString.value, 0, 100)
    
    // Transform response to match expected format
    const objects = []
    
    // Add collections as tree entries
    if (response.collections) {
      for (const collection of response.collections) {
        objects.push({
          id: collection.id,
          path: collection.path,
          object_type: 'tree',
          object: collection
        })
      }
    }
    
    // Add files as file entries
    if (response.files) {
      for (const file of response.files) {
        objects.push({
          id: file.id,
          path: file.path,
          object_type: 'file',
          object: file
        })
      }
    }
    
    files.value = objects
    leaf.value = response.leaf
    emit('files-loaded', files.value)
  } catch (err) {
    console.error('Failed to load files:', err)
    error.value = 'Помилка завантаження файлів: ' + err.message
  } finally {
    loading.value = false
  }
}

function handleRefresh() {
  loadFiles()
  emit('refresh')
}

function navigateToRoot() {
  router.push({
    name: 'FileList',
    query: { treePath: '' }
  })
}

function navigateToPath(ltreePath) {
  router.push({
    name: 'FileList',
    query: { treePath: ltreePath }
  })
}

function selectFile(file) {
  const entry = files.value.find(e => e.object && e.object.id === file.id)
  emit('select-file', entry?.object || file)
}

function handleFileSelected(file) {
  const entry = files.value.find(e => e.object && e.object.id === file.id)
  emit('file-selected', entry?.object || file)
}

function handleObjectRemoved(path) {
  // Remove the object from the local files array
  const index = files.value.findIndex(entry => entry.path === path)
  if (index !== -1) {
    files.value.splice(index, 1)
  }
  // Emit the removed event to parent components
  emit('object-removed', path)
}

function handleObjectCloned(cloneData) {
  // Emit the cloned event to parent components
  emit('object-cloned', cloneData)
  // Optionally refresh the file list to show the new clone
  // loadFiles()
}

// Drag and drop handlers
function handleMoveStart(item) {
  // Optionally provide visual feedback when drag starts
  console.log('Move started for:', item.name)
}

function handleMoveEnd(item) {
  // Optionally provide visual feedback when drag ends
  console.log('Move ended for:', item.name)
}

function handleItemMoved(moveData) {
  // Set global move block during Card operations
  isMoveInProgress.value = true
  
  // Refresh the file list to reflect the changes
  loadFiles().finally(() => {
    // Unblock operations after refresh completes
    isMoveInProgress.value = false
  })
  
  console.log('Item moved:', moveData)
}

function handleModalMoved(moveData) {
  // Handle moves from the move modal
  console.log('Item moved via modal:', moveData)
  // Refresh the file list to reflect the changes
  loadFiles()
}

// Main drop zone handlers
function handleMainDragOver(event) {
  if (!isAuthenticated.value || isMoveInProgress.value) return
  
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

function handleMainDragEnter(event) {
  if (!isAuthenticated.value || isMoveInProgress.value) return
  
  event.preventDefault()
  mainDragCounter.value++
  isMainDropZone.value = true
}

function handleMainDragLeave(event) {
  if (!isAuthenticated.value || isMoveInProgress.value) return
  
  event.preventDefault()
  mainDragCounter.value--
  if (mainDragCounter.value === 0) {
    isMainDropZone.value = false
  }
}

async function handleMainDrop(event) {
  if (!isAuthenticated.value || isMoveInProgress.value) return
  
  event.preventDefault()
  isMainDropZone.value = false
  mainDragCounter.value = 0
  
  try {
    const dragData = JSON.parse(event.dataTransfer.getData('application/json'))
    
    // Show loading state and block other operations
    isMovingToMain.value = true
    isMoveInProgress.value = true
    
    // Move the item to this collection (current collection)
    await apiService.updateTreeItem(dragData.id, {
      parent_path: treePathString.value || 'root'
    })
    
    // Refresh the file list to show the moved item
    loadFiles()
    
  } catch (error) {
    console.error('Failed to move item:', error)
    alert(`Failed to move item: ${error.message}`)
  } finally {
    // Hide loading state and unblock operations
    isMovingToMain.value = false
    isMoveInProgress.value = false
  }
}

// Root breadcrumb drop handlers
function handleRootDragOver(event) {
  if (!isAuthenticated.value || isMoveInProgress.value) return
  
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
}

function handleRootDragEnter(event) {
  if (!isAuthenticated.value || isMoveInProgress.value) return
  
  event.preventDefault()
  rootDragCounter.value++
  isRootDropTarget.value = true
}

function handleRootDragLeave(event) {
  if (!isAuthenticated.value || isMoveInProgress.value) return
  
  event.preventDefault()
  rootDragCounter.value--
  if (rootDragCounter.value === 0) {
    isRootDropTarget.value = false
  }
}

async function handleRootDrop(event) {
  if (!isAuthenticated.value || isMoveInProgress.value) return
  
  event.preventDefault()
  isRootDropTarget.value = false
  rootDragCounter.value = 0
  
  try {
    const dragData = JSON.parse(event.dataTransfer.getData('application/json'))
    
    // Show loading state and block other operations
    isMovingToRoot.value = true
    isMoveInProgress.value = true
    
    // Move the item to root
    await apiService.updateTreeItem(dragData.id, {
      parent_path: 'root'
    })
    
    // If we're currently in root, refresh the list
    if (!treePathString.value || treePathString.value === 'root') {
      loadFiles()
    }
    
  } catch (error) {
    console.error('Failed to move item to root:', error)
    alert(`Failed to move item to root: ${error.message}`)
  } finally {
    // Hide loading state and unblock operations
    isMovingToRoot.value = false
    isMoveInProgress.value = false
  }
}

// Upload modal functions
function closeModal() {
  showUploadModal.value = false
}

function startUpload() {
  showUploadModal.value = true
}

function handleUploadSuccess(response) {
  // Reload files after successful upload
  loadFiles()
  emit('file-uploaded', response)
  
  // Navigate to the uploaded file in the viewer
  if (response && response.id) {
    router.push({
      name: 'FileViewer',
      query: { id: response.id }
    })
  }
}

onMounted(loadFiles)
watch(() => props.refName, loadFiles)
watch(() => props.treePath, loadFiles)
</script>

<style scoped>
.section-feature-list {
  padding: 1rem;
  background: #f8f9fa;
}

.section-feature-list h3 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.file-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 50px;
  background: #f4f6fb;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s, box-shadow 0.15s, transform 0.1s;
  outline: none;
  position: relative;
  /* Better touch targets for mobile */
  min-height: 44px;
  min-width: 44px;
}
.action-btn:active {
  transform: scale(0.97);
}
.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.refresh-btn {
  background: #e0f7fa;
  color: #0097a7;
}
.refresh-btn:hover:not(:disabled) {
  background: #b2ebf2;
  color: #006064;
  box-shadow: 0 4px 16px rgba(0,151,167,0.08);
}
.upload-btn {
  background: #e3f0ff;
  color: #1976d2;
}
.upload-btn:hover:not(:disabled) {
  background: #bbdefb;
  color: #0d47a1;
  box-shadow: 0 4px 16px rgba(25,118,210,0.08);
}
.login-btn {
  background: #f3e5f5;
  color: #7b1fa2;
  text-decoration: none;
}
.login-btn:hover:not(:disabled) {
  background: #e1bee7;
  color: #4a148c;
  box-shadow: 0 4px 16px rgba(123,31,162,0.08);
}
.action-btn svg {
  display: inline-block;
  vertical-align: middle;
  margin-right: 0.2em;
}

/* File list layout */
.file-list-layout {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
}

.file-list-main {
  flex: 1;
  min-width: 0;
}

.file-list-sidebar {
  flex-shrink: 0;
}

/* Mobile responsive layout */
@media (max-width: 768px) {
  .section-feature-list {
    padding: 0.75rem;
  }
  
  .section-feature-list h3 {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .file-actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .action-btn {
    flex: 1;
    min-width: auto;
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
  
  .file-list-layout {
    flex-direction: column;
    gap: 1rem;
  }
  
  .file-list-sidebar {
    order: -1; /* Show sidebar first on mobile */
    width: 100%;
  }
}

.feature-list {
  /* Pure CSS grid - no additional spacing needed */
}

/* Mobile file card layout */
@media (max-width: 768px) {
  .feature-list {
    /* Mobile spacing handled by Pure CSS */
  }
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  text-align: center;
  padding: 1rem;
  color: #d32f2f;
  background: #ffebee;
  border-radius: 4px;
  margin: 1rem 0;
}

/* Mobile loading and error states */
@media (max-width: 768px) {
  .loading {
    padding: 1.5rem 1rem;
    font-size: 0.9rem;
  }
  
  .error {
    padding: 0.75rem;
    font-size: 0.9rem;
    margin: 0.5rem 0;
  }
}



/* Breadcrumb styles */
.breadcrumb {
  display: flex;
  align-items: center;
  padding: 0.75rem 0;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  overflow-x: auto;
  margin-bottom: 1rem;
  /* Enable smooth scrolling on mobile */
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.breadcrumb::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
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
  /* Better touch targets on mobile */
  min-height: 44px;
  display: flex;
  align-items: center;
}

.breadcrumb-item:hover {
  background: #e3f2fd;
}

.breadcrumb-item.active {
  color: #333;
  font-weight: 500;
}

.breadcrumb-item.drop-target {
  background: #e8f5e8;
  border: 2px dashed #4caf50;
  border-radius: 4px;
  color: #4caf50;
}

.breadcrumb-item.moving {
  background: #e3f2fd;
  color: #2196f3;
  pointer-events: none;
}

.loading-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
}

.spinner-small {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(33, 150, 243, 0.3);
  border-top: 2px solid #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.file-list-main.moving {
  background: linear-gradient(135deg, #e3f2fd 0%, #f1f8e9 100%);
  border: 2px dashed #2196f3;
  border-radius: 12px;
  opacity: 0.8;
  pointer-events: none;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.breadcrumb-separator {
  color: #666;
  margin: 0 0.25rem;
}

/* Empty state styles */
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #666;
  background: #f8f9fa;
  border-radius: 8px;
  margin: 1rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* Mobile empty state */
@media (max-width: 768px) {
  .empty-state {
    padding: 2rem 1rem;
    margin: 0.5rem 0;
  }
  
  .empty-state h3 {
    font-size: 1.25rem;
  }
  
  .empty-state p {
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
  }
  
  .empty-actions {
    flex-direction: column;
    width: 100%;
    max-width: 280px;
  }
  
  .empty-actions .action-btn {
    width: 100%;
  }
}

/* Drag and drop styles */
.file-list-main {
  position: relative;
  transition: all 0.2s ease;
}

.file-list-main.drop-zone-active {
  background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
  border: 2px dashed #4caf50;
  border-radius: 12px;
}

/* Mobile drag and drop improvements */
@media (max-width: 768px) {
  .file-list-main {
    min-height: 200px;
  }
  
  .file-list-main.drop-zone-active {
    border-width: 3px;
    border-radius: 16px;
    padding: 1rem;
  }
  
  .breadcrumb-item.drop-target {
    border-width: 3px;
    padding: 0.5rem;
  }
  
  /* Better visual feedback for mobile drag operations */
  .file-list-main.moving {
    border-width: 3px;
    border-radius: 16px;
  }
}


.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.empty-state p {
  margin: 0 0 2rem 0;
  font-size: 1rem;
  line-height: 1.5;
  color: #666;
}

.empty-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

</style> 