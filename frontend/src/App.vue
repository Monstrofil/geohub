<template>
  <div class="pure-g app-grid">
    <!-- Branch Selector -->
    <BranchSelector v-model="currentBranch" @onBranchChange="handleBranchChange" />
    <!-- File List View -->
    <div v-if="!selectedEntry" class="pure-u-1">
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
            <component 
              :is="entry.object_type === 'file' ? FileCard : TreeCard"
              v-for="entry in files" 
              :key="entry.id"
              :file="entry.object"
              :name="entry.object?.original_name || ''"
              :selected="selectedEntry && selectedEntry.object && selectedEntry.object.id === entry.object?.id"
              @click="selectFile(entry.object)"
              @file-selected="handleFileSelected"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- File Editor View -->
    <div v-else class="pure-u-1">
      <FileEditor 
        v-if="selectedEntry"
        :file="selectedEntry.object"
        :change-tracker="changeTracker"
        :commit-id="currentBranch && currentBranch.commit_id"
        :tree-entry-id="selectedEntry.id"
        @back="backToList"
        @file-uploaded="handleFileUploaded"
        @tags-updated="handleTagsUpdated"
        @file-updated="handleFileUpdated"
      />
    </div>

    <!-- Upload Modal -->
    <SimpleUpload 
      :is-open="showUploadModal"
      :commit-id="currentBranch && currentBranch.commit_id"
      @uploaded="handleFileUploaded"
      @close="showUploadModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import FileCard from './components/FileCard.vue'
import TreeCard from './components/TreeCard.vue'
import FileEditor from './components/FileEditor.vue'
import SimpleUpload from './components/SimpleUpload.vue'
import BranchSelector from './components/BranchSelector.vue'
import { useChangeTracker } from './composables/useChangeTracker.js'
import { loadFieldDefinitions } from './utils/fieldResolver.js'
import apiService from './services/api.js'

const selectedEntry = ref(null)
const allFieldDefinitions = ref({})
const files = ref([])
const loading = ref(false)
const error = ref(null)
const showUploadModal = ref(false)

// Branch selector state
const currentBranch = ref(null)
const currentCommit = ref(null)

// Initialize change tracker
const changeTracker = useChangeTracker()

onMounted(async () => {
  // Load all field definitions
  allFieldDefinitions.value = await loadFieldDefinitions()
  // Load files from API
  await loadFiles()
})

function handleBranchChange(branch) {
  currentBranch.value = branch
  loadFiles()
}

async function loadFiles() {
  loading.value = true
  error.value = null
  try {
    if (!currentBranch.value || !currentBranch.value.commit_id) {
      files.value = []
      return
    }
    const response = await apiService.getObjects(currentBranch.value.commit_id, 0, 100)
    files.value = response.files || []
  } catch (err) {
    console.error('Failed to load files:', err)
    error.value = 'Помилка завантаження файлів: ' + err.message
  } finally {
    loading.value = false
  }
}

function selectFile(file) {
  // Find the entry that matches this file
  const entry = files.value.find(e => e.object && e.object.id === file.id)
  selectedEntry.value = entry
}

function handleFileSelected(file) {
  // Find the entry that matches this file
  const entry = files.value.find(e => e.object && e.object.id === file.id)
  selectedEntry.value = entry
}

function backToList() {
  selectedEntry.value = null
}

async function handleFileUploaded(uploadData) {
  // Refresh the file list after upload
  await loadFiles()
  
  // If we have the uploaded file, select it
  if (uploadData && uploadData.id) {
    const uploadedFile = files.value.find(f => f.id === uploadData.id)
    if (uploadedFile) {
      selectedEntry.value = uploadedFile
    }
  }
}

async function handleTagsUpdated(newTags, fromCommit = false) {
  if (selectedEntry.value) {
    if (!fromCommit) {
      // Add change to tracker instead of immediately updating
      changeTracker.addChange({
        type: 'tags',
        fileId: selectedEntry.value.id,
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
    // Update the selectedEntry reference if it's the same file
    if (selectedEntry.value && selectedEntry.value.id === updatedFile.id) {
      selectedEntry.value = files.value[fileIndex]
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

.section-branch-selector {
  padding: 1rem;
  background: #e9f5ff;
  border-bottom: 1px solid #b3d8fd;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.current-branch {
  font-weight: bold;
  color: #1976d2;
}
</style> 