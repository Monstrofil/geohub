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
        :class="{ active: treePathString === '' }"
      >
        Корінь
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
        <div class="file-list-main">
          <div class="feature-list">
            <component 
              :is="entry.object_type === 'file' ? FileCard : TreeCard"
              v-for="entry in files" 
              :key="entry.id"
              :path="entry.path"
              :file="entry.object"
              :name="getDisplayName(entry.object)"
              :tree-path="treePathString"
              :ref-name="entry.object?.name || entry.id"
              :selected="selectedEntry && selectedEntry.object && selectedEntry.object.id === entry.object?.id"
              @click="selectFile(entry.object)"
              @file-selected="handleFileSelected"
              @removed="handleObjectRemoved"
              @cloned="handleObjectCloned"
            />
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
import FileCard from './FileCard.vue'
import TreeCard from './TreeCard.vue'
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
}

.file-actions {
  display: flex;
  gap: 0.5rem;
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

.feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-start;
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



/* Breadcrumb styles */
.breadcrumb {
  display: flex;
  align-items: center;
  padding: 0.75rem 0;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  overflow-x: auto;
  margin-bottom: 1rem;
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