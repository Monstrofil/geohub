<template>
  <div v-if="isOpen" class="upload-modal-overlay" @click="closeModal">
    <div class="upload-modal" @click.stop>
      <div class="modal-header">
        <h3>Завантажити новий файл</h3>
        <button class="close-btn" @click="closeModal">×</button>
      </div>
      
      <form @submit.prevent="handleUpload" class="pure-form pure-form-stacked">
        <div class="form-group">
          <label>Виберіть файл для завантаження:</label>
          <input type="file" ref="fileInput" @change="onFileChange" required />
        </div>

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
          <button type="submit" :disabled="uploading" class="upload-btn">
            {{ uploading ? 'Завантаження...' : 'Завантажити' }}
          </button>
        </div>
        
        <div v-if="error" class="error">{{ error }}</div>
        <div v-if="success" class="success">Файл завантажено!</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import apiService from '../services/api.js'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  commitId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['uploaded', 'close'])
const fileInput = ref(null)
const file = ref(null)
const tags = ref([])
const uploading = ref(false)
const error = ref('')
const success = ref(false)

function closeModal() {
  emit('close')
  resetForm()
}

function resetForm() {
  file.value = null
  tags.value = []
  error.value = ''
  success.value = false
  if (fileInput.value) {
    fileInput.value.value = ''
  }
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
  error.value = ''
  success.value = false
  if (!file.value) {
    error.value = 'Оберіть файл.'
    return
  }
  if (!props.commitId) {
    error.value = 'Commit ID is required.'
    return
  }
  uploading.value = true
  const tagObj = {}
  tags.value.forEach(t => {
    if (t.key && t.value) tagObj[t.key] = t.value
  })
  try {
    const uploaded = await apiService.uploadFile(file.value, tagObj, props.commitId)
    success.value = true
    emit('uploaded', uploaded)
    // Close modal after successful upload
    setTimeout(() => {
      closeModal()
    }, 1500)
  } catch (e) {
    error.value = e.message || 'Помилка завантаження.'
  } finally {
    uploading.value = false
  }
}

// Reset form when modal opens
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
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

form {
  padding: 1.5rem;
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
  color: #c00;
  margin-top: 1rem;
  padding: 0.5rem;
  background: #ffebee;
  border-radius: 4px;
}

.success {
  color: #28a745;
  margin-top: 1rem;
  padding: 0.5rem;
  background: #d4edda;
  border-radius: 4px;
}
</style> 