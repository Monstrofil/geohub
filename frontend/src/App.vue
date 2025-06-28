<template>
  <div class="pure-g app-grid">
    <!-- File List View -->
    <div v-if="!selectedFile" class="pure-u-1">
      <div class="section section-feature-list">
        <h3>
          <span>Файли ({{ files.length }})</span>
          <div class="file-actions">
            <button @click="loadFiles" class="action-btn refresh-btn" :disabled="loading">
              <i class="fas fa-sync-alt"></i> Refresh
            </button>
            <button @click="showUploadModal = true" class="action-btn upload-btn">
              <i class="fas fa-upload"></i> Upload
            </button>
          </div>
        </h3>
        <div v-if="loading" class="loading">Завантаження файлів...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <div v-else class="disclosure-wrap disclosure-wrap-feature_list">
          <div class="feature-list">
            <FileCard 
              v-for="file in files" 
              :key="file.id"
              :file="file"
              :type="getFileType(file)"
              :name="file.original_name"
              :selected="false"
              @click="selectFile(file)"
              @file-selected="handleFileSelected"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- File Editor View -->
    <div v-else class="pure-u-1">
      <FileEditor 
        :file="selectedFile"
        :change-tracker="changeTracker"
        @back="backToList"
        @file-uploaded="handleFileUploaded"
        @tags-updated="handleTagsUpdated"
        @file-updated="handleFileUpdated"
      />
    </div>

    <!-- Upload Modal -->
    <SimpleUpload 
      :is-open="showUploadModal"
      @uploaded="handleFileUploaded"
      @close="showUploadModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import FileCard from './components/FileCard.vue'
import FileEditor from './components/FileEditor.vue'
import SimpleUpload from './components/SimpleUpload.vue'
import { useChangeTracker } from './composables/useChangeTracker.js'
import { loadFieldDefinitions } from './utils/fieldResolver.js'
import apiService from './services/api.js'

const selectedFile = ref(null)
const allFieldDefinitions = ref({})
const files = ref([])
const loading = ref(false)
const error = ref(null)
const showUploadModal = ref(false)

// Initialize change tracker
const changeTracker = useChangeTracker()

onMounted(async () => {
  // Load all field definitions
  allFieldDefinitions.value = await loadFieldDefinitions()
  // Load files from API
  await loadFiles()
})

async function loadFiles() {
  loading.value = true
  error.value = null
  
  try {
    const response = await apiService.getFiles()
    files.value = response.files || []
  } catch (err) {
    console.error('Failed to load files:', err)
    error.value = 'Помилка завантаження файлів: ' + err.message
  } finally {
    loading.value = false
  }
}

function getFileType(file) {
  const tags = file.tags || {}
  if (tags.type === 'raster') return 'raster'
  if (tags.type === 'vector') return 'vector'
  if (tags.type === 'text') return 'text'
  return 'binary'
}

function selectFile(file) {
  selectedFile.value = file
}

function handleFileSelected(file) {
  selectedFile.value = file
}

function backToList() {
  selectedFile.value = null
}

async function handleFileUploaded(uploadData) {
  // Refresh the file list after upload
  await loadFiles()
  
  // If we have the uploaded file, select it
  if (uploadData && uploadData.id) {
    const uploadedFile = files.value.find(f => f.id === uploadData.id)
    if (uploadedFile) {
      selectedFile.value = uploadedFile
    }
  }
}

async function handleTagsUpdated(newTags, fromCommit = false) {
  if (selectedFile.value) {
    if (!fromCommit) {
      // Add change to tracker instead of immediately updating
      changeTracker.addChange({
        type: 'tags',
        fileId: selectedFile.value.id,
        data: newTags
      })
    }
  }
}

function handleFileUpdated(updatedFile) {
  // Update the file's tags in the files array
  const fileIndex = files.value.findIndex(f => f.id === updatedFile.id)
  if (fileIndex !== -1) {
    files.value[fileIndex].tags = { ...updatedFile.tags }
    // Update the selectedFile reference if it's the same file
    if (selectedFile.value && selectedFile.value.id === updatedFile.id) {
      selectedFile.value = files.value[fileIndex]
    }
  }
}
</script>

<style scoped>
.app-grid {
  min-height: 100vh;
  background: #fafbfc;
}

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

.upload-btn {
  color: #666;
}

.upload-btn:hover:not(:disabled) {
  border-color: #4caf50;
  color: #4caf50;
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
</style> 