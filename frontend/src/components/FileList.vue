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
        <button @click="showUploadChoice = true" class="action-btn upload-btn" title="Завантажити новий файл або створити колекцію">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M10 15V5M10 5L6 9M10 5l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="4" y="15" width="12" height="2" rx="1" fill="currentColor"/>
          </svg>
          Завантажити
        </button>
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
        У папці "{{ pathSegments[pathSegments.length - 1] }}" поки немає файлів.
        <br>Перейдіть до батьківської папки або створіть новий вміст.
      </p>
      <div class="empty-actions">
        <button @click="showUploadChoice = true" class="action-btn upload-btn" title="Додати файл або колекцію">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M10 15V5M10 5L6 9M10 5l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="4" y="15" width="12" height="2" rx="1" fill="currentColor"/>
          </svg>
          Додати файл
        </button>
      </div>
    </div>
    <div v-else class="disclosure-wrap disclosure-wrap-feature_list">
      <div class="feature-list">
        <component 
          :is="entry.object_type === 'file' ? FileCard : TreeCard"
          v-for="entry in files" 
          :key="entry.id"
          :path="entry.path"
          :file="entry.object"
          :name="getDisplayName(entry.object)"
          :tree-path="treePathString"
          :selected="selectedEntry && selectedEntry.object && selectedEntry.object.id === entry.object?.id"
          @click="selectFile(entry.object)"
          @file-selected="handleFileSelected"
          @removed="handleObjectRemoved"
          @cloned="handleObjectCloned"
        />
      </div>
    </div>

    <!-- Upload Modal -->
    <UploadModal 
      :show="showUploadModal && uploadMode === 'modal'"
      :tree-path="treePathString"
      @close="closeModal"
      @upload-success="handleUploadSuccess"
    />

    <!-- Upload Wizard for Raster Files -->
    <UploadWizard 
      :show="showUploadModal && uploadMode === 'wizard'"
      :parent-path="treePathString || 'root'"
      @close="closeModal"
      @upload-success="handleUploadSuccess"
    />

    <!-- Upload Choice Modal -->
    <div v-if="showUploadChoice" class="upload-choice-overlay" @click="closeUploadChoice">
      <div class="upload-choice-modal" @click.stop>
        <div class="choice-header">
          <h3>Choose Upload Type</h3>
          <button class="close-btn" @click="closeUploadChoice">×</button>
        </div>
        
        <div class="choice-content">
          <div class="choice-option" @click="startRasterUpload">
            <div class="option-icon">
              <svg width="48" height="48" viewBox="0 0 48 48">
                <rect x="6" y="6" width="36" height="36" rx="4" fill="#e0e7ef" stroke="#007bff" stroke-width="2"/>
                <circle cx="18" cy="30" r="4" fill="#007bff"/>
                <rect x="24" y="18" width="14" height="8" fill="#b3d1ff"/>
                <path d="M8 8l6 6M14 8l6 6M20 8l6 6" stroke="#007bff" stroke-width="1" fill="none"/>
              </svg>
            </div>
            <h4>Raster Image</h4>
            <p>Upload raster files with guided georeferencing</p>
            <div class="option-features">
              <span>✓ Automatic georeferencing detection</span>
              <span>✓ Interactive control point mapping</span>
              <span>✓ Preview and validation</span>
            </div>
          </div>
          
          <div class="choice-option" @click="startRegularUpload">
            <div class="option-icon">
              <svg width="48" height="48" viewBox="0 0 48 48">
                <rect x="8" y="8" width="32" height="32" rx="4" fill="#f7f7e7" stroke="#6c757d" stroke-width="2"/>
                <rect x="14" y="18" width="20" height="2" fill="#6c757d"/>
                <rect x="14" y="24" width="12" height="2" fill="#6c757d"/>
                <rect x="14" y="30" width="16" height="2" fill="#6c757d"/>
                <circle cx="36" cy="12" r="8" fill="#ffb300"/>
                <path d="M32 12h8M36 8v8" stroke="white" stroke-width="2"/>
              </svg>
            </div>
            <h4>Regular File or Collection</h4>
            <p>Upload any file type or create a collection</p>
            <div class="option-features">
              <span>✓ All file types supported</span>
              <span>✓ Create collections</span>
              <span>✓ Quick upload</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import FileCard from './FileCard.vue'
import TreeCard from './TreeCard.vue'
import UploadModal from './UploadModal.vue'
import UploadWizard from './UploadWizard.vue'
import apiService from '../services/api.js'
import { getDisplayName } from '../utils/fileHelpers.js'

const props = defineProps({
  treePath: {type: [String, Array], required: false},
  selectedEntry: { type: Object, default: null },
  changeTracker: { type: Object, required: false }
})

const emit = defineEmits(['refresh', 'select-file', 'file-selected', 'files-loaded', 'file-uploaded', 'branch-created', 'object-removed', 'object-cloned'])

const router = useRouter()
const route = useRoute()

const files = ref([])
const loading = ref(false)
const error = ref(null)

// Upload modal state
const showUploadModal = ref(false)
const showUploadChoice = ref(false)
const uploadMode = ref('modal') // 'modal' or 'wizard'

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
    let response
    
    if (!treePathString.value || treePathString.value === '' || treePathString.value === 'root') {
      // Load root contents
      response = await apiService.getRootContents(0, 100)
    } else {
      // We have a collection path - find the collection and get its contents
      const collection = await apiService.findCollectionByPath(treePathString.value)
      
      if (collection) {
        // Found the collection, get its contents
        response = await apiService.getCollectionContents(collection.id, 0, 100)
      } else {
        // Collection not found, show empty state with error
        console.warn('Collection not found for path:', treePathString.value)
        response = { files: [], collections: [], total_files: 0, total_collections: 0 }
        error.value = `Колекція за шляхом "${treePathString.value}" не знайдена`
      }
    }
    
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

function closeUploadChoice() {
  showUploadChoice.value = false
}

function startRasterUpload() {
  uploadMode.value = 'wizard'
  showUploadChoice.value = false
  showUploadModal.value = true
}

function startRegularUpload() {
  uploadMode.value = 'modal'
  showUploadChoice.value = false
  showUploadModal.value = true
}

function handleUploadSuccess(response) {
  // Reload files after successful upload
  loadFiles()
  emit('file-uploaded', response)
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
.action-btn svg {
  display: inline-block;
  vertical-align: middle;
  margin-right: 0.2em;
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

/* Upload Choice Modal */
.upload-choice-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1500;
  backdrop-filter: blur(4px);
}

.upload-choice-modal {
  background: white;
  border-radius: 12px;
  max-width: 700px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.choice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.choice-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
  font-weight: 600;
}

.choice-header .close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s;
}

.choice-header .close-btn:hover {
  background: #e9ecef;
  color: #333;
}

.choice-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
}

.choice-option {
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  border-right: 1px solid #eee;
  position: relative;
}

.choice-option:last-child {
  border-right: none;
}

.choice-option:hover {
  background: #f8f9ff;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 123, 255, 0.15);
}

.option-icon {
  margin-bottom: 1.5rem;
  transition: transform 0.3s;
}

.choice-option:hover .option-icon {
  transform: scale(1.1);
}

.choice-option h4 {
  margin: 0 0 0.75rem 0;
  color: #333;
  font-size: 1.1rem;
  font-weight: 600;
}

.choice-option p {
  margin: 0 0 1.5rem 0;
  color: #666;
  line-height: 1.5;
}

.option-features {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
}

.option-features span {
  color: #28a745;
  font-size: 0.9rem;
  font-weight: 500;
}
</style> 