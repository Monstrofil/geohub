<template>
  <div class="section section-feature-list">
    <h3>
      <span>Файли ({{ files.length }})</span>
      <div class="file-actions">
        <button @click="handleRefresh" class="action-btn refresh-btn" :disabled="loading">
          <i class="fas fa-sync-alt"></i> Refresh
        </button>
        <button @click="showUploadModal = true" class="action-btn upload-btn">
          <i class="fas fa-upload"></i> Upload
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
          @click="navigateToPath(index)"
          class="breadcrumb-item"
          :class="{ active: index === pathSegments.length - 1 }"
        >
          {{ segment }}
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
        <button @click="showUploadModal = true" class="btn btn-primary">
          <i class="fas fa-plus"></i>
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
          :name="entry.object?.tags.name || entry.object?.original_name || ''"
          :tree-path="treePathString"
          :ref-name="props.refName"
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
      :show="showUploadModal"
      :ref-name="props.refName"
      :tree-path="treePathString"
      @close="closeModal"
      @upload-success="handleUploadSuccess"
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, defineProps, defineEmits, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import FileCard from './FileCard.vue'
import TreeCard from './TreeCard.vue'
import UploadModal from './UploadModal.vue'
import apiService from '../services/api.js'

const props = defineProps({
  refName: { type: String, required: true },
  treePath: {type: [String, Array], required: false},
  selectedEntry: { type: Object, default: null },
  currentBranchName: { type: String, required: false }
})

const emit = defineEmits(['refresh', 'select-file', 'file-selected', 'files-loaded', 'file-uploaded', 'branch-created', 'object-removed', 'object-cloned'])

const router = useRouter()
const route = useRoute()

const files = ref([])
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
  return treePathString.value ? treePathString.value.split('/').filter(Boolean) : []
})

async function loadFiles() {
  loading.value = true
  error.value = null
  try {
    if (!props.refName) {
      files.value = []
      return
    }
    const response = await apiService.getObjects(props.refName, treePathString.value, 0, 100)
    files.value = response.files || []
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
    params: { branch: props.refName },
    query: { treePath: '' }
  })
}

function navigateToPath(index) {
  const newPath = pathSegments.value.slice(0, index + 1).join('/')
  router.push({
    name: 'FileList',
    params: { branch: props.refName },
    query: { treePath: newPath }
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
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.15s;
}

.action-btn:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn {
  color: #666;
}

.refresh-btn:hover:not(:disabled) {
  border-color: #2196f3;
  color: #2196f3;
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