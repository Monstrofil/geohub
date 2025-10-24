<template>
  <div class="file-editor">

    <!-- Header with back button -->
    <div class="editor-header">
      <button class="back-btn" @click="backButton()">
        <svg width="16" height="16" viewBox="0 0 16 16">
          <path d="M10 2L4 8L10 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ $t('fileEditor.backButton') }}
      </button>
    </div>

    <!-- Main content area with editor and tags -->
    <div class="editor-content" v-if="file">
      <!-- Left panel: Tags editor -->
      <div class="left-panel" :class="{ 'collapsed': sidebarCollapsed }">
        <ObjectTypeSelector 
          v-model:selectedType="selectedType" 
          :currentFile="file"
          @menu-open="menuOpen = $event"
          @type-changed="handleTypeChange"
        />
        <TagList 
          v-if="!menuOpen" 
          :fields="selectedFields" 
          :currentFile="file"
          :selectedType="selectedType"
          :allFieldDefinitions="allFieldDefinitions"
          :change-tracker="changeTracker"
          @tags-updated="handleTagsUpdated"
        />

        <!-- Permissions Editor -->
        <div v-if="!menuOpen && file" class="permissions-editor-section">
          <h3>{{ $t('fileEditor.permissions.title') }}</h3>
          <div class="permissions-editor">
            <table class="permissions-edit-table">
              <thead>
                <tr>
                  <th>{{ $t('fileEditor.permissions.role') }}</th>
                  <th>{{ $t('fileEditor.permissions.read') }}</th>
                  <th>{{ $t('fileEditor.permissions.write') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="role-label">{{ $t('fileEditor.permissions.owner') }}</td>
                  <td>
                    <input 
                      type="checkbox" 
                      :checked="hasPermission(file.permissions, 'owner', 'read')"
                      @change="togglePermission('owner', 'read', $event.target.checked)"
                      class="permission-checkbox"
                    />
                  </td>
                  <td>
                    <input 
                      type="checkbox" 
                      :checked="hasPermission(file.permissions, 'owner', 'write')"
                      @change="togglePermission('owner', 'write', $event.target.checked)"
                      class="permission-checkbox"
                    />
                  </td>
                </tr>
                <tr>
                  <td class="role-label">{{ $t('fileEditor.permissions.group') }}</td>
                  <td>
                    <input 
                      type="checkbox" 
                      :checked="hasPermission(file.permissions, 'group', 'read')"
                      @change="togglePermission('group', 'read', $event.target.checked)"
                      class="permission-checkbox"
                    />
                  </td>
                  <td>
                    <input 
                      type="checkbox" 
                      :checked="hasPermission(file.permissions, 'group', 'write')"
                      @change="togglePermission('group', 'write', $event.target.checked)"
                      class="permission-checkbox"
                    />
                  </td>
                </tr>
                <tr>
                  <td class="role-label">{{ $t('fileEditor.permissions.others') }}</td>
                  <td>
                    <input 
                      type="checkbox" 
                      :checked="hasPermission(file.permissions, 'others', 'read')"
                      @change="togglePermission('others', 'read', $event.target.checked)"
                      class="permission-checkbox"
                    />
                  </td>
                  <td>
                    <input 
                      type="checkbox" 
                      :checked="hasPermission(file.permissions, 'others', 'write')"
                      @change="togglePermission('others', 'write', $event.target.checked)"
                      class="permission-checkbox"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- File upload section moved to left panel -->
        <!-- TODO: Add file upload section back in -->
        <div class="upload-section" v-if="!isCollection && false">
          <div class="upload-header">
            <h3>Завантажити нову версію</h3>
            <p>Виберіть файл для заміни поточної версії</p>
          </div>
          
          <div class="upload-area" :class="{ 'drag-over': isDragOver }" @drop="handleDrop" @dragover="handleDragOver" @dragleave="handleDragLeave">
            <input 
              ref="fileInput" 
              type="file" 
              class="file-input" 
              @change="handleFileSelect"
              accept="*/*"
            />
            
            <div class="upload-content">
              <div class="upload-icon">
                <svg width="48" height="48" viewBox="0 0 48 48">
                  <path d="M24 8v20M12 20l12 12 12-12" stroke="#007bff" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                  <rect x="8" y="32" width="32" height="8" rx="2" fill="#007bff"/>
                </svg>
              </div>
              <div class="upload-text">
                <p class="upload-title">Перетягніть файл сюди або натисніть для вибору</p>
                <p class="upload-subtitle">Підтримуються всі типи файлів</p>
              </div>
            </div>
          </div>

          <!-- Upload progress and status -->
          <div v-if="uploadStatus" class="upload-status">
            <div v-if="uploadStatus.state === 'uploading'" class="upload-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: uploadStatus.progress + '%' }"></div>
              </div>
              <span class="progress-text">{{ uploadStatus.progress }}%</span>
            </div>
            <div v-else-if="uploadStatus.state === 'success'" class="upload-success">
              <svg width="16" height="16" viewBox="0 0 16 16">
                <path d="M3 8l3 3 7-7" stroke="#28a745" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Файл успішно завантажено</span>
            </div>
            <div v-else-if="uploadStatus.state === 'error'" class="upload-error">
              <svg width="16" height="16" viewBox="0 0 16 16">
                <path d="M8 2L2 8l6 6 6-6-6-6z" fill="#dc3545"/>
                <path d="M8 6v4M8 12h0" stroke="#fff" stroke-width="1" fill="none"/>
              </svg>
              <span>{{ uploadStatus.error }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right panel: File editor -->
      <div class="right-panel">
        <!-- Right panel header with commit functionality -->
        <div class="right-panel-header">
          <div class="panel-actions">
            <div v-if="changeTracker.hasChanges.value" class="changes-info">
              <span class="changes-count">{{ $t('fileEditor.changes.pending', { count: changeTracker.changeCount.value, plural: changeTracker.changeCount.value !== 1 ? 's' : '' }) }}</span>
            </div>
            
            <button 
              v-if="changeTracker.hasChanges.value"
              class="pure-button pure-button-primary" 
              @click="handleCommit"
              :disabled="changeTracker.isCommitting.value"
            >
              <i v-if="changeTracker.isCommitting.value" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-check"></i>
              {{ changeTracker.isCommitting.value ? $t('fileEditor.changes.committing') : $t('fileEditor.changes.commitButton') }}
            </button>
            
            <div v-else class="no-changes">
              <span>{{ $t('fileEditor.changes.noChanges') }}</span>
            </div>
          </div>
        </div>

        <div class="editor-main">
          <!-- Interactive Map for GeoTIFF files -->
          <InteractiveMap 
            v-if="file && file.object_type === 'geo_raster_file'"
            :fileId="file.id"
            :filename="file.name"
            class="interactive-map-container"
          />
                    
          <!-- Collection view -->
          <div v-else-if="isCollection && file" class="collection-view">
            <div class="collection-header">
              <div class="collection-icon" v-html="selectedType?.icon || ''"></div>
              <div class="collection-info">
                <h3>{{ $t('fileEditor.collection.title', { name: file.name }) }}</h3>
                <p>{{ $t('fileEditor.collection.itemCount', { count: file.entries?.length || 0 }) }}</p>
              </div>
            </div>
            <div class="collection-content">
              <div class="collection-description">
                <h4>{{ $t('fileEditor.collection.aboutTitle') }}</h4>
                <p>{{ $t('fileEditor.collection.aboutDescription', { count: file.entries?.length || 0 }) }}</p>
              </div>
              
              <div class="collection-info-sections">
                <div class="info-section">
                  <div class="info-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" fill="none"/>
                      <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" fill="none"/>
                      <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
                      <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/>
                      <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <div class="info-content">
                    <h5>{{ $t('fileEditor.collection.propertiesTitle') }}</h5>
                    <p>{{ $t('fileEditor.collection.propertiesDescription') }}</p>
                  </div>
                </div>
                
                <div class="info-section">
                  <div class="info-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" fill="none"/>
                      <polyline points="7,10 12,15 17,10" stroke="currentColor" stroke-width="2" fill="none"/>
                      <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <div class="info-content">
                    <h5>{{ $t('fileEditor.collection.browseTitle') }}</h5>
                    <p>{{ $t('fileEditor.collection.browseDescription') }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Placeholder for other file types -->
          <div v-else class="editor-placeholder">
            <div class="placeholder-icon">
              <svg width="64" height="64" viewBox="0 0 64 64">
                <rect x="8" y="8" width="48" height="48" rx="8" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
                <path d="M20 24h24M20 32h16M20 40h12" stroke="#6c757d" stroke-width="2" fill="none"/>
              </svg>
            </div>
            <h3>{{ $t('fileEditor.title') }}</h3>
            <p>{{ $t('fileEditor.file.editTitle', { name: file?.name || 'this file' }) }}</p>
            <div class="placeholder-info">
              <div class="info-item">
                <div class="info-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" fill="none"/>
                    <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" fill="none"/>
                    <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
                    <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <span>{{ $t('fileEditor.file.editTagsDescription') }}</span>
              </div>
              <div class="info-item">
                <div class="info-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24">
                    <path d="M12 15l-3-3h6l-3 3z" stroke="currentColor" stroke-width="2" fill="none"/>
                    <path d="M12 9l3 3h-6l3-3z" stroke="currentColor" stroke-width="2" fill="none"/>
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/>
                  </svg>
                </div>
                <span>{{ $t('fileEditor.file.permissionsDescription') }}</span>
              </div>
            </div>
            <p class="placeholder-note">{{ $t('fileEditor.file.contentNote') }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ObjectTypeSelector from '../../components/ObjectTypeSelector.vue'
import TagList from '../../components/TagList.vue'
import InteractiveMap from '../../components/InteractiveMap.vue'
import { matchTagsToPreset, getAllPresets } from '../../utils/tagMatcher.js'
import { loadFieldDefinitions, resolveFields } from '../../utils/fieldResolver.js'
import apiService from '../../services/api.js'
import { watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  changeTracker: {
    type: Object,
    required: true
  },
  treeItemId: {
    type: String,
    required: true // Tree item ID for direct API access
  }
})

const emit = defineEmits(['back', 'file-uploaded', 'tags-updated', 'file-updated'])

const fileInput = ref(null)
const isDragOver = ref(false)
const uploadStatus = ref(null)
const file = ref(null)
const loading = ref(false)
const error = ref(null)



// Tags editor state
const selectedType = ref(null)
const previousType = ref(null)
const menuOpen = ref(false)
const allPresets = ref([])
const allFieldDefinitions = ref({})
const sidebarCollapsed = ref(false)


const router = useRouter()



function backButton() {
  router.go(-1); 
}

async function loadFile() {
  if (!props.treeItemId) {
    error.value = 'No tree item ID provided'
    return
  }

  loading.value = true
  error.value = null
  
  try {
    // Use direct API call with tree item ID
    const entry = await apiService.getTreeItem(props.treeItemId)
    
    file.value = entry
    // Store the object type for collection detection
    file.value.object_type = entry.object_type

    const matchedPreset = matchTagsToPreset(file.value.tags, allPresets.value, file.value.object_type)
    selectedType.value = matchedPreset
    // Initialize previousType to avoid removing tags on first type change
    previousType.value = matchedPreset
  
    
    // Collection files will be loaded by the CollectionFilesList component
  } catch (e) {
    error.value = e.message || 'Failed to load file'
    file.value = null
  } finally {
    loading.value = false
  }
}



onMounted(async () => {
  allPresets.value = getAllPresets()
  allFieldDefinitions.value = await loadFieldDefinitions()
  await loadFile()
})

// Reload file when treeItemId changes
watch(() => props.treeItemId, loadFile)

// Resolve field keys to full field definitions
const selectedFields = computed(() => {
  if (!selectedType.value || !selectedType.value.fields) {
    return []
  }
  return resolveFields(selectedType.value.fields, allFieldDefinitions.value)
})

// File type detection and icon
const fileType = computed(() => {

  return file.value?.object_type
})




// Check if object is a collection
const isCollection = computed(() => {
  return fileType.value === 'collection'
})

// Tags editor functions
function handleTypeChange(newType) {
  if (file.value && newType) {
    // Start with existing tags to preserve user-added tags
    const newTags = { ...file.value.tags }
    
    // Remove tags that were specific to the previous type (if any)
    if (previousType.value && previousType.value.tags) {
      Object.keys(previousType.value.tags).forEach(key => {
        // Only remove the tag if the new type doesn't also define it
        if (!newType.tags || !(key in newType.tags)) {
          delete newTags[key]
        }
      })
    }
    
    // Add/update tags that are specified by the new type
    if (newType.tags) {
      Object.entries(newType.tags).forEach(([key, value]) => {
        newTags[key] = value
      })
    }
    
    // Update the previous type reference for next time
    previousType.value = selectedType.value
    
    // Add change to tracker
    props.changeTracker.addChange({
      type: 'tags',
      fileId: file.value.id,
      data: newTags
    })
    // Update the local file object to reflect changes immediately
    file.value.tags = { ...newTags }
  }
}

function handleTagsUpdated(newTags) {
  if (!file.value) return
  props.changeTracker.addChange({
    type: 'tags',
    fileId: file.value.id,
    data: newTags
  })
  file.value.tags = { ...newTags }
}

// Permission management functions
function hasPermission(permissions, role, type) {
  if (!permissions) return false
  
  let bit
  if (role === 'owner' && type === 'read') bit = 0o400
  else if (role === 'owner' && type === 'write') bit = 0o200
  else if (role === 'group' && type === 'read') bit = 0o040
  else if (role === 'group' && type === 'write') bit = 0o020
  else if (role === 'others' && type === 'read') bit = 0o004
  else if (role === 'others' && type === 'write') bit = 0o002
  
  return Boolean(permissions & bit)
}

function togglePermission(role, type, enabled) {
  if (!file.value) return
  
  let bit
  if (role === 'owner' && type === 'read') bit = 0o400
  else if (role === 'owner' && type === 'write') bit = 0o200
  else if (role === 'group' && type === 'read') bit = 0o040
  else if (role === 'group' && type === 'write') bit = 0o020
  else if (role === 'others' && type === 'read') bit = 0o004
  else if (role === 'others' && type === 'write') bit = 0o002
  
  let newPermissions = file.value.permissions || 0
  
  if (enabled) {
    newPermissions |= bit  // Set the bit
  } else {
    newPermissions &= ~bit  // Clear the bit
  }
  
  // Update the file object immediately for UI responsiveness
  file.value.permissions = newPermissions
  
  // Add change to tracker for later commit
  props.changeTracker.addChange({
    type: 'permissions',
    fileId: file.value.id,
    data: newPermissions
  })
}

// File upload handlers
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
    processFile(files[0])
  }
}

function handleFileSelect(event) {
  const files = event.target.files
  if (files.length > 0) {
    processFile(files[0])
  }
}

async function processFile(uploadFileObj) {
  uploadStatus.value = { state: 'uploading', progress: 0 }
  try {
    // Prepare tags for the new file
    const tags = {
      name: uploadFileObj.name,
    }
    // Upload file via API with progress tracking
    // For collections, upload to the collection's path; for files, upload to root
    const parentPath = file.value?.object_type === 'collection' ? file.value.path : 'root'
    const uploadedFile = await apiService.uploadFile(
      uploadFileObj, 
      tags, 
      parentPath,
      (progress) => {
        uploadStatus.value = { state: 'uploading', progress: Math.round(progress * 100) }
      }
    )
    uploadStatus.value = { state: 'success' }
    emit('file-uploaded', uploadedFile)
    setTimeout(() => {
      uploadStatus.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }, 3000)
  } catch (error) {
    console.error('Upload failed:', error)
    uploadStatus.value = { 
      state: 'error', 
      error: error.message || 'Помилка завантаження файлу'
    }
    setTimeout(() => {
      uploadStatus.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }, 5000)
  }
}

function triggerFileSelect() {
  fileInput.value?.click()
}

async function handleCommit() {
  const result = await props.changeTracker.commitChanges(async (change) => {
    if (change.type === 'tags') {
      const updatedEntry = await apiService.updateTreeItem(file.value.id, { tags: change.data })
      // Update the local file object with the response
      if (updatedEntry && updatedEntry.object && file.value) {
        Object.assign(file.value, updatedEntry.object)
      }
    } else if (change.type === 'permissions') {
      const updatedEntry = await apiService.updateTreeItem(file.value.id, { permissions: change.data })
      // Update the local file object with the response
      if (updatedEntry && file.value) {
        file.value.permissions = change.data
      }
    }
  })
  if (result.success) {
    emit('tags-updated', file.value?.tags, true)
    emit('file-updated', file.value)
  } else {
    console.error('Commit failed:', result.error)
    // You might want to show an error message to the user
  }
}



</script>

<style scoped>
.file-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fafbfc;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #eee;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  color: #666;
  transition: all 0.15s;
}

.back-btn:hover {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}


.editor-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 420px;
  background: #f8f9fa;
  border-right: 1px solid #eee;
  overflow-y: auto;
  transition: width 0.3s ease;
}

.left-panel.collapsed {
  width: 60px;
}

/* Permissions Editor Styles */
.permissions-editor-section {
  background: white;
  border-radius: 8px;
  margin: 1rem;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  border: 1px solid #e9ecef;
}

.permissions-editor-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.permissions-edit-table {
  width: 100%;
  border-collapse: collapse;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

.permissions-edit-table th {
  background: #f8f9fa;
  padding: 0.5rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.85rem;
  color: #495057;
  border-bottom: 1px solid #e9ecef;
}

.permissions-edit-table td {
  padding: 0.5rem;
  border-bottom: 1px solid #f1f3f4;
  font-size: 0.85rem;
  text-align: center;
}

.permissions-edit-table .role-label {
  text-align: left;
  font-weight: 500;
  color: #495057;
}

.permissions-edit-table tbody tr:last-child td {
  border-bottom: none;
}

.permission-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #007bff;
}

.permission-checkbox:hover {
  transform: scale(1.1);
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-main {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.editor-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.placeholder-icon {
  margin-bottom: 1rem;
  opacity: 0.6;
}

.editor-placeholder h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.editor-placeholder p {
  margin: 0.25rem 0;
}

.placeholder-note {
  font-size: 0.9rem;
  font-style: italic;
  color: #999;
}

.placeholder-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 2rem 0;
  max-width: 400px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.info-item .info-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  background: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c757d;
  border: 1px solid #e9ecef;
}

.info-item span {
  color: #666;
  font-size: 0.9rem;
}

.upload-section {
  background: white;
  border-top: 1px solid #eee;
  padding: 1rem;
  margin-top: 1rem;
}

.upload-header {
  margin-bottom: 0.75rem;
}

.upload-header h3 {
  margin: 0 0 0.25rem 0;
  color: #333;
  font-size: 1rem;
}

.upload-header p {
  margin: 0;
  color: #666;
  font-size: 0.8rem;
}

.upload-area {
  position: relative;
  border: 2px dashed #ddd;
  border-radius: 6px;
  padding: 1rem;
  text-align: center;
  transition: all 0.15s;
  cursor: pointer;
  min-height: 80px;
}

.upload-area:hover {
  border-color: #007bff;
  background: #f8f9ff;
}

.upload-area.drag-over {
  border-color: #007bff;
  background: #f0f8ff;
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

.upload-content {
  pointer-events: none;
}

.upload-icon {
  margin-bottom: 0.5rem;
}

.upload-icon svg {
  width: 32px;
  height: 32px;
}

.upload-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: #333;
  margin: 0 0 0.25rem 0;
}

.upload-subtitle {
  color: #666;
  margin: 0;
  font-size: 0.75rem;
}

.upload-status {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.2s;
}

.progress-text {
  font-size: 0.8rem;
  color: #666;
  min-width: 35px;
}

.upload-success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.upload-error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.upload-success svg,
.upload-error svg {
  flex-shrink: 0;
}

.right-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #eee;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.panel-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.changes-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.changes-count {
  font-size: 0.9rem;
  color: #666;
}

.pure-button {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: #666;
  transition: all 0.15s;
}

.pure-button:hover {
  color: #007bff;
}

.pure-button-primary {
  background: #007bff;
  color: white;
  border-radius: 6px;
  padding: 0.5rem 1rem;
}

.pure-button-primary:hover {
  background: #0056b3;
}

.no-changes {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.no-changes span {
  font-size: 0.9rem;
  color: #666;
}

.interactive-map-container {
  margin: 1rem;
  border-radius: 8px;
  overflow: hidden;
  height: 600px;
}

/* Collection view styles */
.collection-view {
  padding: 2rem;
  background: white;
  border-radius: 8px;
  margin: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.collection-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #eee;
}

.collection-icon {
  flex-shrink: 0;
}

.collection-icon svg {
  width: 48px;
  height: 48px;
}

.collection-info h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.collection-info p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.collection-content {
  color: #555;
  line-height: 1.6;
}

.collection-content p {
  margin: 0 0 1rem 0;
}

.collection-description {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}

.collection-description h4 {
  margin: 0 0 0.75rem 0;
  color: #333;
  font-size: 1.1rem;
  font-weight: 600;
}

.collection-description p {
  margin: 0;
  color: #666;
  font-size: 0.95rem;
}

.collection-info-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.info-section {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
}

.info-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  background: #f8f9fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c757d;
}

.info-content h5 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1rem;
  font-weight: 600;
}

.info-content p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
}

.collection-note {
  font-size: 0.9rem;
  color: #888;
  font-style: italic;
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  border-left: 4px solid #ffb300;
}



</style> 