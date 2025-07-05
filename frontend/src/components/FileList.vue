<template>
  <div class="section section-feature-list">
    <h3>
      <span>Файли ({{ files.length }})</span>
      <div class="file-actions">
        <button @click="handleRefresh" class="action-btn refresh-btn" :disabled="loading">
          <i class="fas fa-sync-alt"></i> Refresh
        </button>
        <button @click="handleEdit" class="action-btn edit-btn" :disabled="!props.commitId">
          <i class="fas fa-edit"></i> Edit
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
          :path="entry.path"
          :file="entry.object"
          :name="entry.object?.tags.name || entry.object?.original_name || ''"
          :tree-path="treePathString"
          :selected="selectedEntry && selectedEntry.object && selectedEntry.object.id === entry.object?.id"
          @click="selectFile(entry.object)"
          @file-selected="handleFileSelected"
        />
      </div>
    </div>

    <!-- Upload Modal -->
    <div v-if="showUploadModal" class="upload-modal-overlay" @click="closeModal">
      <div class="upload-modal" @click.stop>
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
                  <i class="fas fa-file"></i>
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
                  <i class="fas fa-folder"></i>
                  Колекція
                </span>
              </label>
            </div>
          </div>

          <!-- File Upload Section -->
          <div v-if="objectType === 'file'" class="form-group">
            <label>Виберіть файл для завантаження:</label>
            <input type="file" ref="fileInput" @change="onFileChange" required />
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

          <!-- Tags Section -->
          <div class="tags-section">
            <label>Додаткові теґи (необов'язково):</label>
            <div v-for="(tag, idx) in tags" :key="idx" class="tag-row">
              <input v-model="tag.key" placeholder="Ключ" class="tag-key" />
              <input v-model="tag.value" placeholder="Значення" class="tag-value" />
              <button type="button" @click="removeTag(idx)" class="remove-tag">×</button>
            </div>
            <button type="button" @click="addTag" class="add-tag">Додати теґ</button>
          </div>

          <div class="modal-actions">
            <button type="button" @click="closeModal" class="cancel-btn">Скасувати</button>
            <button type="submit" :disabled="uploading || !isFormValid" class="upload-btn">
              {{ uploading ? 'Завантаження...' : (objectType === 'file' ? 'Завантажити файл' : 'Створити колекцію') }}
            </button>
          </div>
          
          <div v-if="uploadError" class="error">{{ uploadError }}</div>
          <div v-if="uploadSuccess" class="success">{{ uploadSuccessMessage }}</div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, defineProps, defineEmits, computed } from 'vue'
import FileCard from './FileCard.vue'
import TreeCard from './TreeCard.vue'
import apiService from '../services/api.js'

const props = defineProps({
  commitId: { type: [String, Number], required: true },
  treePath: {type: [String, Array], required: false},
  selectedEntry: { type: Object, default: null },
  currentBranchName: { type: String, required: false }
})

const emit = defineEmits(['refresh', 'select-file', 'file-selected', 'files-loaded', 'file-uploaded', 'branch-created'])

const files = ref([])
const loading = ref(false)
const error = ref(null)

// Upload modal state
const showUploadModal = ref(false)
const fileInput = ref(null)
const file = ref(null)
const name = ref('')
const tags = ref([])
const uploading = ref(false)
const uploadError = ref('')
const uploadSuccess = ref(false)
const objectType = ref('file') // 'file' or 'collection'

// Convert treePath array to string for API calls
const treePathString = computed(() => {
  if (Array.isArray(props.treePath)) {
    return props.treePath.join('/')
  }
  return props.treePath || ''
})

async function loadFiles() {
  loading.value = true
  error.value = null
  try {
    if (!props.commitId) {
      files.value = []
      return
    }
    const response = await apiService.getObjects(props.commitId, treePathString.value, 0, 100)
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

async function handleEdit() {
  if (!props.commitId) {
    error.value = 'Commit ID is required for editing'
    return
  }
  
  if (!props.currentBranchName) {
    error.value = 'Current branch name is required for editing'
    return
  }
  
  try {
    // Generate a UUID for the new branch
    const uuid = crypto.randomUUID()
    const branchName = `refs/changes/${uuid}`
    const newBranch = await apiService.createBranch(branchName, props.currentBranchName)
    emit('branch-created', newBranch)
    // You might want to navigate to the new branch or show a success message
    console.log('Created new branch:', newBranch)
  } catch (err) {
    console.error('Failed to create edit branch:', err)
    error.value = 'Помилка створення гілки для редагування: ' + err.message
  }
}

// Upload modal functions
function closeModal() {
  showUploadModal.value = false
  resetFormAndType()
}

function resetForm() {
  file.value = null
  name.value = ''
  tags.value = []
  uploadError.value = ''
  uploadSuccess.value = false
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function resetFormAndType() {
  resetForm()
  objectType.value = 'file' // Reset object type
}

function onFileChange(e) {
  file.value = e.target.files[0]
}

function addTag() {
  tags.value.push({ key: '', value: '' })
}

function removeTag(idx) {
  tags.value.splice(idx, 1)
}

async function handleUpload() {
  uploadError.value = ''
  uploadSuccess.value = false
  if (!props.commitId) {
    uploadError.value = 'Commit ID is required.'
    return
  }

  if (objectType.value === 'file') {
    if (!file.value) {
      uploadError.value = 'Оберіть файл.'
      return
    }
    uploading.value = true
    const tagObj = {}
    tags.value.forEach(t => {
      if (t.key && t.value) tagObj[t.key] = t.value
    })
    try {
      const uploaded = await apiService.uploadFile(file.value, tagObj, props.commitId, treePathString.value, name.value)
      uploadSuccess.value = true
      emit('file-uploaded', uploaded)
      // Reload files and close modal after successful upload
      await loadFiles()
      setTimeout(() => {
        closeModal()
      }, 1500)
    } catch (e) {
      uploadError.value = e.message || 'Помилка завантаження.'
    } finally {
      uploading.value = false
    }
  } else if (objectType.value === 'collection') {
    if (!name.value) {
      uploadError.value = 'Назва колекції є обов\'язковою.'
      return
    }
    uploading.value = true
    const tagObj = {}
    tags.value.forEach(t => {
      if (t.key && t.value) tagObj[t.key] = t.value
    })
    try {
      const collection = await apiService.createCollection(name.value, props.commitId, treePathString.value, tagObj)
      uploadSuccess.value = true
      emit('file-uploaded', collection)
      // Reload files and close modal after successful upload
      await loadFiles()
      setTimeout(() => {
        closeModal()
      }, 1500)
    } catch (e) {
      uploadError.value = e.message || 'Помилка створення колекції.'
    } finally {
      uploading.value = false
    }
  }
}

const isFormValid = computed(() => {
  if (objectType.value === 'file') {
    return file.value && props.commitId
  } else if (objectType.value === 'collection') {
    return name.value && props.commitId
  }
  return false
})

const uploadSuccessMessage = computed(() => {
  if (objectType.value === 'file') {
    return 'Файл успішно завантажено!'
  } else if (objectType.value === 'collection') {
    return 'Колекцію успішно створено!'
  }
  return 'Об\'єкт успішно додано!'
})

onMounted(loadFiles)
watch(() => props.commitId, loadFiles)
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

.edit-btn {
  color: #666;
}

.edit-btn:hover:not(:disabled) {
  border-color: #ff9800;
  color: #ff9800;
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

/* Upload Modal Styles */
.upload-modal-overlay {
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

.upload-modal {
  background: white;
  border-radius: 8px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
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
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.9rem;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
}

.form-help {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: #666;
  font-style: italic;
}

.tags-section {
  margin: 1rem 0;
}

.tags-section label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.tag-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.tag-key, .tag-value {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.9rem;
}

.tag-key:focus, .tag-value:focus {
  outline: none;
  border-color: #007bff;
}

.add-tag, .remove-tag {
  background: #eee;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 0.7rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.add-tag {
  margin-top: 0.5rem;
}

.add-tag:hover {
  background: #ddd;
}

.remove-tag {
  color: #c00;
  padding: 0.5rem;
  width: 40px;
}

.remove-tag:hover {
  background: #ffebee;
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
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.cancel-btn:hover {
  background: #5a6268;
}

.upload-btn {
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.upload-btn:hover:not(:disabled) {
  background: #0056b3;
}

.upload-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.success {
  color: #28a745;
  margin-top: 1rem;
  padding: 0.5rem;
  background: #d4edda;
  border-radius: 4px;
}

/* New styles for type selector */
.type-selector {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.type-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  transition: all 0.15s;
  background: white;
  flex: 1;
}

.type-option:hover {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

.type-option input[type="radio"] {
  transform: scale(1.2);
  margin-right: 0.5rem;
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
</style> 