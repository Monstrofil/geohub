<template>
  <div class="pure-g app-grid">
    <!-- Branch Selector -->
    <BranchSelector v-model="currentBranch" @onBranchChange="handleBranchChange" />
    <!-- File List View -->
    <div v-if="!selectedEntry" class="pure-u-1">
      <FileList
        :commit-id="currentBranch && currentBranch.commit_id"
        :selected-entry="selectedEntry"
        @refresh="() => {}"
        @show-upload="showUploadModal = true"
        @select-file="selectFile"
        @file-selected="handleFileSelected"
        @files-loaded="files = $event"
      />
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
import FileList from './components/FileList.vue'
import { useChangeTracker } from './composables/useChangeTracker.js'
import { loadFieldDefinitions } from './utils/fieldResolver.js'
import apiService from './services/api.js'

const selectedEntry = ref(null)
const allFieldDefinitions = ref({})
const files = ref([])
const showUploadModal = ref(false)

// Branch selector state
const currentBranch = ref(null)
const currentCommit = ref(null)

// Initialize change tracker
const changeTracker = useChangeTracker()

onMounted(async () => {
  // Load all field definitions
  allFieldDefinitions.value = await loadFieldDefinitions()
})

function handleBranchChange(branch) {
  currentBranch.value = branch
  selectedEntry.value = null
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
  // FileList will reload files automatically on prop change, so just select the uploaded file
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