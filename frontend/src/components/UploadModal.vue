<template>
  <div v-if="show" class="upload-modal-overlay" @click="closeModal">
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
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import apiService from '../services/api.js'

const props = defineProps({
  show: { type: Boolean, default: false },
  refName: { type: String, required: true },
  treePath: { type: String, default: '' }
})

const emit = defineEmits(['close', 'upload-success'])

// Form state
const fileInput = ref(null)
const file = ref(null)
const name = ref('')
const tags = ref([])
const uploading = ref(false)
const uploadError = ref('')
const uploadSuccess = ref(false)
const uploadSuccessMessage = ref('')
const objectType = ref('file') // 'file' or 'collection'

// Form validation
const isFormValid = computed(() => {
  if (objectType.value === 'file') {
    return file.value !== null
  } else {
    return name.value.trim() !== ''
  }
})

// Methods
function closeModal() {
  emit('close')
  resetForm()
}

function resetForm() {
  file.value = null
  name.value = ''
  tags.value = []
  uploadError.value = ''
  uploadSuccess.value = false
  uploadSuccessMessage.value = ''
  objectType.value = 'file'
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function onFileChange(event) {
  const selectedFile = event.target.files[0]
  if (selectedFile) {
    file.value = selectedFile
    // Auto-fill name if empty
    if (!name.value) {
      name.value = selectedFile.name
    }
  }
}

function addTag() {
  tags.value.push({ key: '', value: '' })
}

function removeTag(index) {
  tags.value.splice(index, 1)
}

async function handleUpload() {
  if (!isFormValid.value) return

  uploading.value = true
  uploadError.value = ''
  uploadSuccess.value = false

  try {
    if (objectType.value === 'file') {
      await uploadFile()
    } else {
      await createCollection()
    }
  } catch (err) {
    console.error('Upload failed:', err)
    uploadError.value = 'Помилка завантаження: ' + err.message
  } finally {
    uploading.value = false
  }
}

async function uploadFile() {
  // Build tags object
  const tagsObj = {}
  tags.value.forEach(tag => {
    if (tag.key.trim() && tag.value.trim()) {
      tagsObj[tag.key.trim()] = tag.value.trim()
    }
  })

  const response = await apiService.uploadFile(
    file.value,
    tagsObj,
    props.refName,
    props.treePath,
    name.value.trim() || (file.value && file.value.name) || ''
  )
  
  uploadSuccess.value = true
  uploadSuccessMessage.value = 'Файл успішно завантажено!'
  
  // Emit success event
  emit('upload-success', response)
  
  // Close modal after a short delay
  setTimeout(() => {
    closeModal()
  }, 1500)
}

async function createCollection() {
  var collectionTags = {}
  
  // Add tags
  tags.value.forEach(tag => {
    if (tag.key.trim() && tag.value.trim()) {
      collectionTags[tag.key.trim()] = tag.value.trim()
    }
  })

  collectionTags['name'] = name.value.trim();
  console.log("coll", collectionTags)

  const response = await apiService.createCollection(name.value.trim(), props.refName, props.treePath, collectionTags)
  
  uploadSuccess.value = true
  uploadSuccessMessage.value = 'Колекцію успішно створено!'
  
  // Emit success event
  emit('upload-success', response)
  
  // Close modal after a short delay
  setTimeout(() => {
    closeModal()
  }, 1500)
}

// Reset form when modal opens/closes
watch(() => props.show, (newValue) => {
  if (!newValue) {
    resetForm()
  }
})
</script>

<style scoped>
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
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
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

.error {
  color: #dc3545;
  margin-top: 1rem;
  padding: 0.5rem;
  background: #f8d7da;
  border-radius: 4px;
}

.success {
  color: #28a745;
  margin-top: 1rem;
  padding: 0.5rem;
  background: #d4edda;
  border-radius: 4px;
}

/* Type selector styles */
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