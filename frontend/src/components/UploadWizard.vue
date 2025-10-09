<template>
  <div v-if="show" class="upload-wizard-overlay" @click="closeWizard">
    <div class="upload-wizard" @click.stop>
      <!-- Header -->
      <div class="wizard-header">
        <h2>Upload Raster File</h2>
        <button class="close-btn" @click="closeWizard">×</button>
      </div>

      <!-- Progress indicator -->
      <div class="progress-indicator">
        <div class="progress-step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
          <div class="step-number">1</div>
          <div class="step-label">Upload</div>
        </div>
        <div class="progress-line" :class="{ completed: currentStep > 1 }"></div>
        <div class="progress-step" :class="{ active: currentStep >= 2, completed: currentStep > 2 }">
          <div class="step-number">2</div>
          <div class="step-label">Georeference</div>
        </div>
        <div class="progress-line" :class="{ completed: currentStep > 2 }"></div>
        <div class="progress-step" :class="{ active: currentStep >= 3, completed: currentStep > 3 }">
          <div class="step-number">3</div>
          <div class="step-label">Metadata</div>
        </div>
      </div>

      <!-- Step 1: File Upload -->
      <div v-if="currentStep === 1" class="wizard-step">
        <div class="step-content">
          <h3>Select Raster File</h3>
          <p>Choose a raster image file to upload. Supported formats: GeoTIFF, TIFF, PNG, JPEG, etc.</p>
          
          <div class="upload-area" 
               :class="{ 'drag-over': isDragOver, 'has-file': selectedFile }"
               @drop="handleDrop" 
               @dragover="handleDragOver" 
               @dragleave="handleDragLeave">
            
            <input ref="fileInput" 
                   type="file" 
                   class="file-input" 
                   @change="handleFileSelect"
                   accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg,.bmp">
            
            <div v-if="!selectedFile" class="upload-content">
              <div class="upload-icon">
                <svg width="64" height="64" viewBox="0 0 64 64">
                  <path d="M32 16v24M20 28l12 12 12-12" stroke="#007bff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                  <rect x="8" y="44" width="48" height="12" rx="4" fill="#007bff"/>
                </svg>
              </div>
              <div class="upload-text">
                <h4>Drop raster file here or click to browse</h4>
                <p>Maximum file size: 100MB</p>
              </div>
            </div>
            
            <div v-else class="file-selected">
              <div class="file-icon">
                <svg width="48" height="48" viewBox="0 0 48 48">
                  <rect x="6" y="6" width="36" height="36" rx="4" fill="#28a745" stroke="#1e7e34" stroke-width="2"/>
                  <path d="M18 24l6 6 12-12" stroke="white" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="file-info">
                <h4>{{ selectedFile.name }}</h4>
                <p>{{ formatFileSize(selectedFile.size) }} • {{ selectedFile.type || 'Unknown type' }}</p>
              </div>
            </div>
          </div>

          <!-- Upload Progress -->
          <div v-if="uploadProgress !== null" class="upload-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
            </div>
            <div class="progress-text">{{ uploadProgress }}% uploaded</div>
          </div>

          <!-- Upload Error -->
          <div v-if="uploadError" class="error-message">
            <svg width="20" height="20" viewBox="0 0 20 20">
              <circle cx="10" cy="10" r="9" fill="#dc3545"/>
              <path d="M10 6v4M10 14h0" stroke="white" stroke-width="2" fill="none" stroke-linecap="round"/>
            </svg>
            <span>{{ uploadError }}</span>
          </div>
        </div>

        <div class="step-actions">
          <button class="btn btn-secondary" @click="closeWizard">Cancel</button>
          <button class="btn btn-primary" 
                  @click="uploadFile" 
                  :disabled="!selectedFile || uploading">
            {{ uploading ? 'Uploading...' : 'Upload File' }}
          </button>
        </div>
      </div>

      <!-- Step 2: Georeferencing -->
      <div v-if="currentStep === 2" class="wizard-step">
        <div class="step-content">
          <div v-if="fileInfo && fileInfo.georeferenced" class="georeference-complete">
            <div class="success-icon">
              <svg width="64" height="64" viewBox="0 0 64 64">
                <circle cx="32" cy="32" r="30" fill="#28a745"/>
                <path d="M20 32l8 8 16-16" stroke="white" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>File is Already Georeferenced</h3>
            <p>This file contains geospatial information and is ready to use.</p>
            <div class="file-details">
              <div class="detail-item">
                <span class="label">Dimensions:</span>
                <span class="value">{{ fileInfo.image_width }} × {{ fileInfo.image_height }} pixels</span>
              </div>
              <div class="detail-item">
                <span class="label">Bands:</span>
                <span class="value">{{ fileInfo.image_bands }}</span>
              </div>
            </div>
          </div>

          <div v-else class="georeference-needed">
            <div class="warning-icon">
              <svg width="64" height="64" viewBox="0 0 64 64">
                <circle cx="32" cy="32" r="30" fill="#ffc107"/>
                <path d="M32 16v16M32 40h0" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>Georeferencing Required</h3>
            <p>This image doesn't contain geospatial coordinates. You'll need to add control points to georeference it.</p>
            
            <div class="file-details">
              <div class="detail-item">
                <span class="label">Dimensions:</span>
                <span class="value">{{ fileInfo?.image_width }} × {{ fileInfo?.image_height }} pixels</span>
              </div>
              <div class="detail-item">
                <span class="label">Bands:</span>
                <span class="value">{{ fileInfo?.image_bands }}</span>
              </div>
            </div>

            <div class="georeference-options">
              <div class="option-card" @click="startGeoreferencing">
                <div class="option-icon">
                  <svg width="32" height="32" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="14" fill="none" stroke="#007bff" stroke-width="2"/>
                    <circle cx="16" cy="16" r="2" fill="#007bff"/>
                    <path d="M16 2v4M16 26v4M2 16h4M26 16h4" stroke="#007bff" stroke-width="2"/>
                  </svg>
                </div>
                <h4>Manual Georeferencing</h4>
                <p>Add control points by matching image features to map coordinates</p>
              </div>
              
              <div class="option-card" @click="skipGeoreferencing">
                <div class="option-icon">
                  <svg width="32" height="32" viewBox="0 0 32 32">
                    <rect x="4" y="4" width="24" height="24" rx="4" fill="none" stroke="#6c757d" stroke-width="2"/>
                    <path d="M8 16h16M8 12h8M8 20h12" stroke="#6c757d" stroke-width="2"/>
                  </svg>
                </div>
                <h4>Skip for Now</h4>
                <p>Continue without georeferencing (can be done later)</p>
              </div>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <button class="btn btn-secondary" @click="goToStep(1)">Back</button>
          <button v-if="fileInfo && fileInfo.georeferenced" 
                  class="btn btn-primary" 
                  @click="goToStep(3)">
            Next: Add Metadata
          </button>
          <button v-else-if="skipGeoreferencingMode" 
                  class="btn btn-primary" 
                  @click="goToStep(3)">
            Continue Without Georeferencing
          </button>
        </div>
      </div>

      <!-- Step 3: Metadata -->
      <div v-if="currentStep === 3" class="wizard-step">
        <div class="step-content">
          <h3>Add Metadata</h3>
          <p>Provide information about your raster file to make it easier to find and use.</p>
          
          <div class="metadata-form">
            <div class="form-group">
              <label for="title">Title *</label>
              <input id="title" 
                     v-model="metadata.title" 
                     type="text" 
                     class="form-control" 
                     placeholder="Enter a descriptive title"
                     required>
            </div>
            
            <div class="form-group">
              <label for="description">Description</label>
              <textarea id="description" 
                        v-model="metadata.description" 
                        class="form-control" 
                        rows="3"
                        placeholder="Describe what this raster represents..."></textarea>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label for="year">Year</label>
                <input id="year" 
                       v-model="metadata.year" 
                       type="number" 
                       class="form-control" 
                       min="1900" 
                       :max="currentYear"
                       placeholder="YYYY">
              </div>
              
              <div class="form-group">
                <label for="source">Source</label>
                <input id="source" 
                       v-model="metadata.source" 
                       type="text" 
                       class="form-control" 
                       placeholder="Data source or organization">
              </div>
            </div>
            
            <div class="form-group">
              <label for="tags">Tags</label>
              <div class="tags-input">
                <div class="tag" v-for="(tag, index) in metadataTags" :key="index">
                  {{ tag }}
                  <button type="button" @click="removeTag(index)" class="tag-remove">×</button>
                </div>
                <input v-model="newTag" 
                       @keydown.enter.prevent="addTag"
                       @keydown.comma.prevent="addTag"
                       type="text" 
                       class="tag-input"
                       placeholder="Add tags...">
              </div>
              <small class="form-text">Press Enter or comma to add tags</small>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <button class="btn btn-secondary" @click="goToStep(2)">Back</button>
          <button class="btn btn-success" 
                  @click="completeUpload" 
                  :disabled="!metadata.title.trim() || completing">
            {{ completing ? 'Completing...' : 'Complete Upload' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Georeferencing Modal -->
    <GeoreferencingModal v-if="showGeoreferencingModal"
                        :file-id="uploadedFileId"
                        :file-info="fileInfo"
                        @close="closeGeoreferencing"
                        @completed="onGeoreferencingCompleted" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import apiService from '../services/api.js'
import GeoreferencingModal from './GeoreferencingModal.vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  parentPath: { type: String, default: 'root' }
})

const emit = defineEmits(['close', 'upload-success'])

// State
const currentStep = ref(1)
const selectedFile = ref(null)
const uploadProgress = ref(null)
const uploading = ref(false)
const uploadError = ref('')
const uploadedFileId = ref(null)
const fileInfo = ref(null)
const skipGeoreferencingMode = ref(false)
const showGeoreferencingModal = ref(false)
const completing = ref(false)

// Drag and drop
const isDragOver = ref(false)
const fileInput = ref(null)

// Metadata
const metadata = ref({
  title: '',
  description: '',
  year: new Date().getFullYear(),
  source: ''
})
const metadataTags = ref([])
const newTag = ref('')

// Computed
const currentYear = computed(() => new Date().getFullYear())

// Methods
function closeWizard() {
  if (!uploading.value && !completing.value) {
    resetWizard()
    emit('close')
  }
}

function resetWizard() {
  currentStep.value = 1
  selectedFile.value = null
  uploadProgress.value = null
  uploading.value = false
  uploadError.value = ''
  uploadedFileId.value = null
  fileInfo.value = null
  skipGeoreferencingMode.value = false
  showGeoreferencingModal.value = false
  completing.value = false
  
  // Clear file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  
  metadata.value = {
    title: '',
    description: '',
    year: new Date().getFullYear(),
    source: ''
  }
  metadataTags.value = []
  newTag.value = ''
}

function goToStep(step) {
  currentStep.value = step
}


function handleDragOver(event) {
  event.preventDefault()
  isDragOver.value = true
}

function handleDragLeave(event) {
  event.preventDefault()
  isDragOver.value = false
}

function handleDrop(event) {
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer.files
  if (files.length > 0) {
    selectFile(files[0])
  }
}

function handleFileSelect(event) {
  const files = event.target.files
  if (files.length > 0) {
    selectFile(files[0])
  }
  // Reset the input so the same file can be selected again if needed
  event.target.value = ''
}

function selectFile(file) {
  // Validate file type
  const validTypes = [
    'image/tiff', 'image/tif', 'image/geotiff',
    'image/png', 'image/jpeg', 'image/jpg', 'image/bmp',
    'application/pdf'
  ]
  
  const extension = file.name.split('.').pop().toLowerCase()
  const validExtensions = ['tif', 'tiff', 'geotiff', 'png', 'jpg', 'jpeg', 'bmp', 'pdf']
  
  if (!validTypes.includes(file.type) && !validExtensions.includes(extension)) {
    uploadError.value = 'Please select a valid raster image file (TIFF, PNG, JPEG, PDF, etc.)'
    return
  }
  
  // Validate file size (100MB limit)
  if (file.size > 100 * 1024 * 1024) {
    uploadError.value = 'File size must be less than 100MB'
    return
  }
  
  selectedFile.value = file
  uploadError.value = ''
  
  // Auto-fill title from filename
  if (!metadata.value.title) {
    metadata.value.title = file.name.replace(/\.[^/.]+$/, "")
  }
}

async function uploadFile() {
  if (!selectedFile.value) return
  
  uploading.value = true
  uploadProgress.value = 0
  uploadError.value = ''
  
  try {
    // Prepare tags for the new file
    const tags = {
      name: selectedFile.value.name,
    }
    
    // Upload with progress tracking (automatically uses chunked upload for large files)
    const response = await apiService.uploadFile(
      selectedFile.value,
      tags,
      props.parentPath,
      (progress) => {
        uploadProgress.value = Math.round(progress * 100)
      }
    )
    
    uploadedFileId.value = response.id
    fileInfo.value = response.tags
    
    // Auto-advance to next step
    setTimeout(() => {
      currentStep.value = 2
      uploadProgress.value = null
    }, 500)
    
  } catch (error) {
    console.error('Upload failed:', error)
    uploadError.value = error.message || 'Upload failed. Please try again.'
  } finally {
    uploading.value = false
  }
}

function startGeoreferencing() {
  showGeoreferencingModal.value = true
}

function skipGeoreferencing() {
  skipGeoreferencingMode.value = true
}

function closeGeoreferencing() {
  console.log('Closing georeferencing modal')
  showGeoreferencingModal.value = false
}

function onGeoreferencingCompleted(result) {
  showGeoreferencingModal.value = false
  fileInfo.value = { ...fileInfo.value, ...result.fileInfo }
  goToStep(3)
}

function addTag() {
  const tag = newTag.value.trim()
  if (tag && !metadataTags.value.includes(tag)) {
    metadataTags.value.push(tag)
    newTag.value = ''
  }
}

function removeTag(index) {
  metadataTags.value.splice(index, 1)
}

async function completeUpload() {
  if (!metadata.value.title.trim()) return
  
  completing.value = true
  
  try {
    // Update file with metadata
    const updatedTags = {
      ...fileInfo.value,
      title: metadata.value.title,
      description: metadata.value.description,
      year: metadata.value.year,
      source: metadata.value.source,
      tags: metadataTags.value
    }
    
    const updatedFile = await apiService.updateTreeItem(uploadedFileId.value, {
      tags: updatedTags
    })
    
    emit('upload-success', updatedFile)
    closeWizard()
    
  } catch (error) {
    console.error('Failed to complete upload:', error)
    uploadError.value = 'Failed to save metadata. Please try again.'
  } finally {
    completing.value = false
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Initialize
onMounted(() => {
  resetWizard()
})
</script>

<style scoped>
.upload-wizard-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.upload-wizard {
  background: white;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.wizard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem 2rem 1rem;
  border-bottom: 1px solid #eee;
}

.wizard-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f8f9fa;
  color: #333;
}

/* Progress Indicator */
.progress-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #f8f9fa;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e9ecef;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-bottom: 0.5rem;
  transition: all 0.3s;
}

.step-label {
  font-size: 0.875rem;
  color: #6c757d;
  font-weight: 500;
}

.progress-step.active .step-number {
  background: #007bff;
  color: white;
}

.progress-step.active .step-label {
  color: #007bff;
}

.progress-step.completed .step-number {
  background: #28a745;
  color: white;
}

.progress-step.completed .step-label {
  color: #28a745;
}

.progress-line {
  width: 80px;
  height: 2px;
  background: #e9ecef;
  margin: 0 1rem;
  transition: all 0.3s;
}

.progress-line.completed {
  background: #28a745;
}

/* Wizard Steps */
.wizard-step {
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.step-content {
  flex: 1;
  padding: 2rem;
}

.step-content h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.25rem;
  font-weight: 600;
}

.step-content p {
  margin: 0 0 2rem 0;
  color: #666;
  line-height: 1.6;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  padding: 1.5rem 2rem;
  border-top: 1px solid #eee;
  background: #f8f9fa;
}

/* Upload Area */
.upload-area {
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  padding: 3rem 2rem;
  text-align: center;
  transition: all 0.3s;
  cursor: pointer;
  position: relative;
  background: #fafbfc;
}

.upload-area:hover {
  border-color: #007bff;
  background: #f8f9ff;
}

.upload-area.drag-over {
  border-color: #007bff;
  background: #e3f2fd;
  transform: scale(1.02);
}

.upload-area.has-file {
  border-color: #28a745;
  background: #f8fff9;
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.upload-content, .file-selected {
  pointer-events: none;
}

.upload-icon {
  margin-bottom: 1rem;
}

.upload-text h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-weight: 600;
}

.upload-text p {
  margin: 0;
  color: #666;
  font-size: 0.875rem;
}

.file-selected {
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
}

.file-info h4 {
  margin: 0 0 0.25rem 0;
  color: #333;
  font-weight: 600;
}

.file-info p {
  margin: 0;
  color: #666;
  font-size: 0.875rem;
}

/* Upload Progress */
.upload-progress {
  margin-top: 1.5rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #0056b3);
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  font-size: 0.875rem;
  color: #666;
  font-weight: 500;
}

/* Georeferencing Status */
.georeference-complete, .georeference-needed {
  text-align: center;
  padding: 2rem 0;
}

.success-icon, .warning-icon {
  margin-bottom: 1.5rem;
}

.file-details {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 2rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
}

.detail-item:not(:last-child) {
  border-bottom: 1px solid #e9ecef;
}

.label {
  font-weight: 500;
  color: #495057;
}

.value {
  color: #212529;
  font-weight: 600;
}

.georeference-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 2rem;
}

.option-card {
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.option-card:hover {
  border-color: #007bff;
  background: #f8f9ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.15);
}

.option-icon {
  margin-bottom: 1rem;
}

.option-card h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1rem;
  font-weight: 600;
}

.option-card p {
  margin: 0;
  color: #666;
  font-size: 0.875rem;
  line-height: 1.4;
}

/* Metadata Form */
.metadata-form {
  max-width: 500px;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.tags-input {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 6px;
  min-height: 44px;
  align-items: center;
}

.tags-input:focus-within {
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.tag {
  background: #007bff;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.tag-remove {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 0;
  font-weight: bold;
}

.tag-input {
  border: none;
  outline: none;
  flex: 1;
  min-width: 120px;
  padding: 0.25rem;
}

.form-text {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

/* Buttons */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #1e7e34;
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: #f8d7da;
  color: #721c24;
  border-radius: 6px;
  margin-top: 1rem;
}
</style>
