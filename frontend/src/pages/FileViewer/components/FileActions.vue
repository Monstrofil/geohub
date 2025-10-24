<template>
  <div v-if="shouldShow" class="file-actions">
    
    <h3>{{ $t('fileInfo.actionsTitle') }}</h3>
    <!-- Loading state -->
    <div v-if="loading" class="actions-loading">
      <div class="spinner"></div>
      <h3>{{ $t('fileInfo.loadingActions') }}</h3>
      <p>{{ $t('fileInfo.preparingActions') }}</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="actions-error">
      <h3>{{ $t('fileInfo.actionsError') }}</h3>
      <p>{{ error }}</p>
    </div>

    <!-- Actions list -->
    <div v-else class="actions-list">
      <div class="pure-g action-btn-container">
        <!-- Edit Action -->
        <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-1-3" v-if="actions.edit" >
          <button 
            v-if="actions.edit" 
            class="action-btn edit-action" 
            @click="$emit('edit')"
            :title="$t('actions.editFile')"
          >
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ $t('actions.edit') }}</span>
          </button>
        </div>

        <!-- Download Action -->
        <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-1-3" v-if="actions.download" >
          <button 
            class="action-btn download-action" 
            @click="$emit('download')"
            :title="$t('actions.downloadFile')"
          >
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="7,10 12,15 17,10" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ $t('actions.download') }}</span>
          </button>
        </div>

        <!-- Move Action -->
        <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-1-3" v-if="actions.move" >
          <button 
            class="action-btn move-action" 
            @click="$emit('move')"
            :title="$t('actions.moveFile')"
          >
            <svg width="20" height="20" viewBox="0 0 24 24">
              <polyline points="5,9 2,12 5,15" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="9,5 12,2 15,5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="15,19 12,22 9,19" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="19,9 22,12 19,15" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="2" x2="12" y2="22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ $t('actions.move') }}</span>
          </button>
        </div>

        <!-- Delete Action -->
        <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-1-3" v-if="actions.delete" >
          <button 
            class="action-btn delete-action" 
            @click="$emit('delete')"
            :title="$t('actions.deleteFile')"
          >
            <svg width="20" height="20" viewBox="0 0 24 24">
              <polyline points="3,6 5,6 21,6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="10" y1="11" x2="10" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="14" y1="11" x2="14" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ $t('actions.delete') }}</span>
          </button>
        </div>

        <!-- Convert Action (for raw files) -->
        <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-1-3" v-if="actions.convert" >
          <button 
            class="action-btn convert-action" 
            @click="$emit('convert')"
            :title="$t('actions.convertFile')"
          >
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ $t('actions.convert') }}</span>
          </button>
        </div>

        <!-- Georeference Action -->
        <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-2-3" v-if="actions.georeference" >
          <button 
            class="action-btn georef-action"
            :class="{ 'continue-georef-action': !props.file.object_details.is_georeferenced }"
            @click="$emit('georeference')"
            :title="$t('actions.georeferenceFile')"
          >
            <svg width="20" height="20" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
              <circle cx="12" cy="12" r="2" fill="currentColor"/>
              <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" stroke-width="2"/>
            </svg>
            <span v-if="props.file.object_details.is_georeferenced">{{ $t('actions.georeference') }}</span>
            <span v-else>{{ $t('actions.continueGeoreference') }}</span>
          </button>
        </div>

        <!-- Re-georeference Action (for already georeferenced files) -->
        <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-1-3" v-if="actions.regeoreference" >
          <button 
            class="action-btn regeoref-action" 
            @click="$emit('regeoreference')"
            :title="$t('actions.regeoreferenceFile')"
          >
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path d="M1 4v6h6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ $t('actions.regeoreference') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import apiService from '../../../services/api.js'

const props = defineProps({
  file: {
    type: Object,
    required: true
  }
})

const emit = defineEmits([
  'edit', 
  'download', 
  'move', 
  'delete', 
  'convert', 
  'georeference', 
  'regeoreference'
])

// Component state
const loading = ref(false)
const error = ref(null)
const probeResult = ref(null)

// Check if file is georeferenced
const isFileGeoreferenced = computed(() => {
  if (props.file && props.file.object_type === 'geo_raster_file' && props.file.object_details) {
    return props.file.object_details.is_georeferenced === true
  }
  return false
})

// Determine which actions are available based on file type and state
const actions = computed(() => {
  if (!props.file) return {}

  const fileType = props.file.object_type
  const isGeoreferenced = isFileGeoreferenced.value
  const isCollection = fileType === 'collection'

  return {
    edit: true, // Always available for files
    download: !isCollection, // Not available for collections
    move: true, // Always available
    delete: true, // Always available
    convert: fileType === 'raw_file' && probeResult.value?.can_georeference, // Only for convertible raw files
    georeference: (fileType === 'geo_raster_file' && !isGeoreferenced) || 
                  (fileType === 'raw_file' && probeResult.value?.can_georeference), // For files that need georeferencing
    regeoreference: fileType === 'geo_raster_file' && isGeoreferenced // For already georeferenced files
  }
})

const shouldShow = computed(() => {
  return props.file && Object.values(actions.value).some(action => action)
})

// Probe functions for raw files
async function probeFile() {
  if (!props.file?.id || props.file.object_type !== 'raw_file') return

  loading.value = true
  error.value = null
  
  try {
    const result = await apiService.probeTreeItem(props.file.id)
    probeResult.value = result
  } catch (err) {
    console.error('Failed to probe file:', err)
    error.value = err.message || 'Failed to probe file'
  } finally {
    loading.value = false
  }
}

// Watch for file changes and probe when needed
watch(() => props.file, (newFile) => {
  if (newFile && newFile.type === 'file') {
    // Clear previous probe results
    probeResult.value = null
    error.value = null
    // Probe the file if it's a raw file
    if (newFile.object_type === 'raw_file') {
      probeFile()
    }
  }
}, { immediate: true })
</script>

<style scoped>
.file-actions {
  display: flex;
  flex-direction: column;
  padding: 3rem;
  background: #fff;
  border-radius: 8px;
  margin: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Actions section when in right panel */
.content-sidebar .file-actions {
  padding: 1.5rem;
  margin: 1.5rem 0 0 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Adjust button sizing for right panel */

/* Loading and error states */
.actions-loading,
.actions-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  color: #666;
}

.actions-loading .spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.actions-error {
  color: #dc3545;
}

/* Action button styles */
.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 0.75rem;
  background: #f8f9fa;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  color: #495057;
  font-weight: 500;
  min-height: 80px;
  width: 100%;
}

.action-btn-container > div {
  border: 0;
  margin-right: 2px transparent solid;
}

.action-btn:hover {
  background: #e9ecef;
  border-color: #007bff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,123,255,0.15);
}

.action-btn:active {
  transform: translateY(0);
}

.action-btn svg {
  color: #6c757d;
  transition: color 0.2s ease;
  width: 20px;
  height: 20px;
}

.action-btn:hover svg {
  color: #007bff;
}

.action-btn span {
  font-size: 0.8rem;
  text-align: center;
  font-weight: 500;
}

/* Specific action button colors */
.edit-action:hover {
  border-color: #28a745;
  box-shadow: 0 4px 12px rgba(40,167,69,0.15);
}

.edit-action:hover svg {
  color: #28a745;
}

.download-action:hover {
  border-color: #17a2b8;
  box-shadow: 0 4px 12px rgba(23,162,184,0.15);
}

.download-action:hover svg {
  color: #17a2b8;
}

.move-action:hover {
  border-color: #ffc107;
  box-shadow: 0 4px 12px rgba(255,193,7,0.15);
}

.move-action:hover svg {
  color: #ffc107;
}

.delete-action:hover {
  border-color: #dc3545;
  box-shadow: 0 4px 12px rgba(220,53,69,0.15);
}

.delete-action:hover svg {
  color: #dc3545;
}

.convert-action:hover {
  border-color: #6f42c1;
  box-shadow: 0 4px 12px rgba(111,66,193,0.15);
}

.convert-action:hover svg {
  color: #6f42c1;
}

.georef-action:hover {
  border-color: #fd7e14;
  box-shadow: 0 4px 12px rgba(253,126,20,0.15);
}

.georef-action:hover svg {
  color: #fd7e14;
}

/* Continue georeferencing warning styles */
.continue-georef-action {
  background: #fff3cd !important;
}

.continue-georef-action:hover {
  background: #ffeaa7 !important;
  box-shadow: 0 4px 12px rgba(243,156,18,0.25) !important;
}

.continue-georef-action svg {
  color: #856404 !important;
}

.continue-georef-action:hover svg {
  color: #6c4a00 !important;
}

.regeoref-action:hover {
  border-color: #e83e8c;
  box-shadow: 0 4px 12px rgba(232,62,140,0.15);
}

.regeoref-action:hover svg {
  color: #e83e8c;
}

/* Spinner animation */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive design */
@media (max-width: 768px) {
  .action-btn {
    padding: 0.75rem 0.5rem;
    min-height: 70px;
  }
  
  .action-btn span {
    font-size: 0.75rem;
  }
}
</style>
