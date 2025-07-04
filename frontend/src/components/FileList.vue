<template>
  <div class="section section-feature-list">
    <h3>
      <span>Файли ({{ files.length }})</span>
      <div class="file-actions">
        <button @click="handleRefresh" class="action-btn refresh-btn" :disabled="loading">
          <i class="fas fa-sync-alt"></i> Refresh
        </button>
        <button @click="$emit('show-upload')" class="action-btn upload-btn">
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
</template>

<script setup>
import { ref, watch, onMounted, defineProps, defineEmits } from 'vue'
import FileCard from './FileCard.vue'
import TreeCard from './TreeCard.vue'
import apiService from '../services/api.js'

const props = defineProps({
  commitId: { type: [String, Number], required: true },
  selectedEntry: { type: Object, default: null }
})

const emit = defineEmits(['refresh', 'show-upload', 'select-file', 'file-selected', 'files-loaded'])

const files = ref([])
const loading = ref(false)
const error = ref(null)

async function loadFiles() {
  loading.value = true
  error.value = null
  try {
    if (!props.commitId) {
      files.value = []
      return
    }
    const response = await apiService.getObjects(props.commitId, 0, 100)
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

function selectFile(file) {
  const entry = files.value.find(e => e.object && e.object.id === file.id)
  emit('select-file', entry?.object || file)
}

function handleFileSelected(file) {
  const entry = files.value.find(e => e.object && e.object.id === file.id)
  emit('file-selected', entry?.object || file)
}

onMounted(loadFiles)
watch(() => props.commitId, loadFiles)
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