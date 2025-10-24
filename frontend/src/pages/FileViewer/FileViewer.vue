<template>
  <div class="file-viewer">
    <!-- Header with back button -->
    <div class="viewer-header">
      <button class="back-btn" @click="goBack">
        <svg width="16" height="16" viewBox="0 0 16 16">
          <path d="M10 2L4 8L10 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Назад до списку
      </button>
      <div class="header-actions">
        <router-link v-if="isAuthenticated" :to="{name: 'FileEditor', query: { id: props.treeItemId }}" class="edit-btn">
          <svg width="16" height="16" viewBox="0 0 16 16">
            <path d="M11 1L15 5L5 15H1V11L11 1Z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 4L12 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Редагувати
        </router-link>
        <router-link v-else :to="loginUrl" class="login-btn">
          <svg width="16" height="16" viewBox="0 0 16 16">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="16,17 21,12 16,7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Увійти щоб редагувати
        </router-link>
      </div>
    </div>


    <div class="viewer-content">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading file...</p>
      </div>
      
      <div v-else-if="error" class="error">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading File</h3>
        <p>{{ error }}</p>
        <button @click="loadFile" class="retry-btn">Try Again</button>
      </div>
      
      <div v-else-if="!file" class="not-found">
        <i class="fas fa-file-excel"></i>
        <h3>File Not Found</h3>
        <p>The requested file could not be found.</p>
        <button @click="goBack" class="back-btn">Go Back</button>
      </div>
      
      
      <div v-else class="file-content">
        <div class="content-layout">
          <!-- Left panel: Main content -->
          <div class="content-main">
            <!-- Collection viewer -->
            <div v-if="file.object_type === 'tree'" class="collection-viewer">
              <div class="collection-info">
                <h3>Collection: {{ file.name || 'Untitled Collection' }}</h3>
                <p class="collection-description">
                  This is a collection containing {{ file.entries?.length || 0 }} items.
                </p>
                <div class="collection-stats">
                  <div class="stat-item">
                    <span class="stat-label">Items:</span>
                    <span class="stat-value">{{ file.entries?.length || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">Created:</span>
                    <span class="stat-value">{{ formatDate(file.created_at) }}</span>
                  </div>
                </div>
              </div>
              
              <div class="collection-content">
                <p>This is a collection of files. You can view the contents in tree.</p>
              </div>
            </div>
            
            <!-- File viewer -->
            <div v-else class="file-viewer">
            <!-- Layer controls filter block - for georeferenced files -->
            <div v-if="file && isFileGeoreferenced" class="layer-filter-block">
                <div class="filter-header" @click="toggleLayerPanel">
                  <div class="filter-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" class="filter-icon">
                      <path d="M12 16l-6-6h12l-6 6z" fill="currentColor"/>
                      <path d="M12 10l-6-6h12l-6 6z" fill="currentColor" opacity="0.6"/>
                      <path d="M12 4l-6-6h12l-6 6z" fill="currentColor" opacity="0.3"/>
                    </svg>
                    <span>Map Layers</span>
                  </div>
                  <button class="filter-toggle" :class="{ 'expanded': layerPanelOpen }">
                    <svg width="16" height="16" viewBox="0 0 24 24">
                      <path d="M6 9l6 6 6-6" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
                
                <div v-show="layerPanelOpen" class="filter-content">
                  <div class="layer-controls-grid">
                    <!-- Base Map Layer -->
                    <div class="layer-filter-item">
                      <label class="layer-filter-label">
                        <input 
                          type="checkbox" 
                          v-model="layers.baseMap.visible"
                          @change="toggleLayer('osm-tiles', layers.baseMap.visible)"
                          class="layer-filter-checkbox"
                        />
                        <span class="layer-filter-name">Base Map</span>
                      </label>
                      <div class="layer-description">OpenStreetMap background tiles</div>
                      
                      <!-- Opacity slider for Base Map layer -->
                      <div class="layer-opacity-section">
                        <label class="opacity-section-label">Opacity: {{ Math.round(layers.baseMap.opacity * 100) }}%</label>
                        <input 
                          type="range" 
                          min="0" 
                          max="1" 
                          step="0.1"
                          v-model="layers.baseMap.opacity"
                          @input="updateLayerOpacity('osm-tiles', layers.baseMap.opacity)"
                          class="layer-filter-opacity-slider"
                          :disabled="!layers.baseMap.visible"
                        />
                      </div>
                    </div>
                    
                    <!-- GeoTIFF Layer -->
                    <div class="layer-filter-item">
                      <label class="layer-filter-label">
                        <input 
                          type="checkbox" 
                          v-model="layers.geotiff.visible"
                          @change="toggleLayer('geotiff-layer', layers.geotiff.visible)"
                          class="layer-filter-checkbox"
                        />
                        <span class="layer-filter-name">{{ file.name || 'Georeferenced File' }}</span>
                      </label>
                      <div class="layer-description">Uploaded georeferenced overlay</div>
                      
                      <!-- Opacity slider for GeoTIFF layer -->
                      <div class="layer-opacity-section">
                        <label class="opacity-section-label">Opacity: {{ Math.round(layers.geotiff.opacity * 100) }}%</label>
                        <input 
                          type="range" 
                          min="0" 
                          max="1" 
                          step="0.1"
                          v-model="layers.geotiff.opacity"
                          @input="updateLayerOpacity('geotiff-layer', layers.geotiff.opacity)"
                          class="layer-filter-opacity-slider"
                          :disabled="!layers.geotiff.visible"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
            <!-- Interactive Map for georeferenced files -->
            <InteractiveMap 
              v-if="file && isFileGeoreferenced"
              :fileId="file.id"
              :filename="file.name"
              class="interactive-map-container"
              ref="interactiveMapRef"
            />
            
            <!-- WMS/TMS Links section for georeferenced files -->
            <MapLinksSection 
              v-if="file && isFileGeoreferenced"
              :map-url="mapUrl"
            />
              
              <!-- File Preview Section - displays regardless of georeferencing ability -->
              <div v-if="!isFileGeoreferenced && previewComponent" class="file-preview-section">
                <div class="file-preview-container">
                  <div class="preview-header">
                    <h3>File Preview</h3>
                  </div>
                  <component 
                    :is="previewComponent.component" 
                    :file-id="file.id"
                    :file="file"
                    @error="handlePreviewError"
                    @loaded="handlePreviewLoaded"
                  />
                </div>
              </div>
              
              <div v-else-if="!isFileGeoreferenced && !previewComponent" class="file-preview-section">
                Preview is not available for this file type.
              </div>
            </div>
          </div>

          <!-- Right panel: Object Information -->
          <div class="content-sidebar">

            <!-- File Actions -->
            <FileActions 
              :file="file"
              @edit="handleEdit"
              @download="handleDownload"
              @move="handleMove"
              @delete="handleDelete"
              @convert="startConversion"
              @georeference="startGeoreferencing"
              @regeoreference="confirmResetGeoreferencing"
            />

            <!-- Unified Object Type and Properties section -->
            <ObjectInformation 
              :file="file"
            />

            <!-- File Information section -->
            <FileInfoSection :file="file" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- Reset Georeferencing Confirmation Modal -->
    <div v-if="showResetConfirmation" class="modal-overlay" @click="showResetConfirmation = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Reset Georeferencing</h3>
          <button class="modal-close" @click="showResetConfirmation = false">
            <svg width="24" height="24" viewBox="0 0 24 24">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="warning-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path d="M12 9v4M12 17h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h4>Are you ready to start from scratch?</h4>
          <p>This will reset the georeferencing for this file, removing all current control points and returning it to its original state. You will need to re-add control points to georeference it again.</p>
          <p><strong>This action cannot be undone.</strong></p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showResetConfirmation = false">
            Cancel
          </button>
          <button class="btn btn-danger" @click="resetGeoreferencing" :disabled="loading">
            <div v-if="loading" class="spinner"></div>
            Reset & Start Over
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InteractiveMap from '../../components/InteractiveMap.vue'
import GeoreferencingModal from '../../components/GeoreferencingModal.vue'
import TaskProgressModal from './components/TaskProgressModal.vue'
import ObjectInformation from './components/ObjectInformation.vue'
import FileInfoSection from './components/FileInfoSection.vue'
import FileActions from './components/FileActions.vue'
import MapLinksSection from './components/MapLinksSection.vue'
import MoveModal from '../../components/MoveModal/MoveModal.vue'
import { isAuthenticated } from '../../stores/auth.js'
import apiService from '../../services/api.js'
import { getFileSize, getBaseFileType } from '../../utils/fileHelpers.js'
import { findPreviewComponent, previewComponents } from '../../components/previews/index.js'
import { useModal } from 'vue-final-modal'

const route = useRoute()
const router = useRouter()

// Create login URL with current path as redirect
const loginUrl = computed(() => {
  const redirectParam = encodeURIComponent(route.fullPath)
  return `/login?redirect=${redirectParam}`
})

// State
const file = ref(null)
const loading = ref(false)
const error = ref(null)

// Georeferencing state
const showResetConfirmation = ref(false)


// Task progress modal state
const activeTaskId = ref(null)

// Preview component state
const previewComponent = ref(null)

// Layer controls state
const layerPanelOpen = ref(true)
const layers = ref({
  baseMap: {
    visible: true,
    opacity: 1.0
  },
  geotiff: {
    visible: true,
    opacity: 0.8
  }
})
const interactiveMapRef = ref(null)

// Map service URLs state
const mapUrl = ref(null)


const props = defineProps({
  treeItemId: {
    type: String,
    required: true // Tree item ID for direct API access
  }
})


const { open: openTaskProgressModal, close: closeTaskProgressModal } = useModal({
    component: TaskProgressModal,
    attrs: {
      title: "Converting to Geo-Raster",
      "item-id": file?.id,
      "task-id": activeTaskId,
      onComplete() {
        handleTaskProgressClose()
      },
      onError() {
        handleTaskError()
      },
      onClose() {
        handleTaskProgressClose()
      },
    },
    slots: {
      default: '<p>UseModal: The content of the modal</p>',
    },
  })

const { open: openGeoreferencingModal, close: closeGeoreferencingModal } = useModal({
    component: GeoreferencingModal,
    attrs: {
      "file-id": computed(() => file.value.id),
      "file-info": computed(() => file.value.tags),
      onClose() {
        handleGeoreferencingClose()
      },
      onCompleted(result) {
        handleGeoreferencingCompleted(result)
      },
    },
  })

const { open: openMoveModal, close: closeMoveModal } = useModal({
    component: MoveModal,
    attrs: {
      "item-id": computed(() => file.value?.id),
      "item-name": computed(() => getDisplayName()),
      "item-type": computed(() => file.value?.object_type === 'collection' ? 'collection' : 'file'),
      "current-path": computed(() => file.value?.parent_path || 'root'),
      onClose() {
        closeMoveModal()
      },
      onMoved() {
        handleMoveCompleted()
      },
    },
  })



// Methods

async function loadFile() {
  if (!props.treeItemId) {
    error.value = 'No tree item ID provided'
    return
  }

  loading.value = true
  error.value = null
  
  try {
    // Use direct API call with tree item ID
    const response = await apiService.getTreeItem(props.treeItemId)
    
    file.value = response
    // Store the object type for UI rendering
    file.value.object_type = response.object_type || response.type


    // Check for active tasks
    await checkActiveTasks()

    // Check for preview components if file is not georeferenced
    if (file.value && file.value.type === 'file' && !isFileGeoreferenced.value) {
      checkPreviewComponent()
    }
    
    // Load map URL for georeferenced files
    if (file.value && file.value.object_type === 'geo_raster_file') {
      await loadMapUrl()
    }
  } catch (err) {
    console.error('Failed to load file:', err)
    error.value = err.message || 'Failed to load file'
    file.value = null
  } finally {
    loading.value = false
  }
}


function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}

function goBack() {
  router.back()
}

function getDisplayName() {
  if (!file.value) return 'Untitled'
  
  if (file.value.object_type === 'tree') {
    return file.value.tags?.name || file.value.name || 'Untitled Collection'
  } else {
    return file.value.tags?.name || file.value.original_name || file.value.name || 'Untitled File'
  }
}



// File type detection and labels (reused from FileEditor)
const fileType = computed(() => {
  // Check if this is a collection first
  if (file.value?.object_type === 'tree') {
    return 'collection'
  }
  return getBaseFileType(file.value)
})


// Check if file is georeferenced
const isFileGeoreferenced = computed(() => {
  // For geo_raster_file objects, check the is_georeferenced field from the database
  if (file.value && file.value.object_type === 'geo_raster_file') {
    return true;
  }
  
  // Default to false if no conclusive information
  return false
})

// Handle collection files updates
function handleCollectionFilesUpdated(files) {
  // Update the collection entries count if needed
  if (file.value && file.value.object_type === 'tree') {
    file.value.entries = files
  }
}



// Georeferencing functions
function startGeoreferencing() {
  openGeoreferencingModal()
  
}

function handleGeoreferencingClose() {
  closeGeoreferencingModal()
}

function handleGeoreferencingCompleted(result) {
  
  // Update file tags to reflect georeferencing status
  if (file.value && result.fileInfo) {
    file.value.tags = { ...file.value.tags, ...result.fileInfo }
  }
  
  // Update the is_georeferenced field in the file object
  if (file.value && file.value.object_details) {
    file.value.object_details.is_georeferenced = true
  }
  
  // Force re-render to show the map
  loadFile()
  closeGeoreferencingModal()
}

// Reset georeferencing functions
function confirmResetGeoreferencing() {
  showResetConfirmation.value = true
}

async function resetGeoreferencing() {
  if (!file.value?.id) return
  
  loading.value = true
  
  try {
    // Call the reset-georeferencing API
    await apiService.resetGeoreferencing(file.value.id)
    
    // Close the confirmation modal
    showResetConfirmation.value = false
    
    // Update the is_georeferenced field in the file object
    if (file.value && file.value.object_details) {
      file.value.object_details.is_georeferenced = false
    }
    
    // Reload the file to reflect the changes
    await loadFile()
    
    // Now start the georeferencing process
    startGeoreferencing()
  } catch (err) {
    console.error('Failed to reset georeferencing:', err)
    alert(`Failed to reset georeferencing: ${err.message}`)
  } finally {
    loading.value = false
  }
}

// Preview component functions
function checkPreviewComponent() {
  console.log('🔍 [FileViewer] Checking preview component for file:', file.value)
  
  if (!file.value) {
    console.log('⚠️ [FileViewer] No file available for preview check')
    return
  }
  
  // Check file size - only show preview for files that aren't too large
  const fileSize = file.value.object_details?.file_size
  const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB maximum size for preview
  const isSizeAppropriate = fileSize && fileSize <= MAX_FILE_SIZE
  
  console.log('📏 [FileViewer] File size check:', {
    fileSize: fileSize,
    maxSize: MAX_FILE_SIZE,
    isSizeAppropriate: isSizeAppropriate,
    fileSizeFormatted: fileSize ? `${(fileSize / 1024 / 1024).toFixed(2)} MB` : 'unknown'
  })
  
  if (!isSizeAppropriate) {
    previewComponent.value = null
    console.log('❌ [FileViewer] File too large for preview:', fileSize, 'bytes (max:', MAX_FILE_SIZE, 'bytes)')
    
    // For large files that can be converted to geo-raster, start automatic conversion
    if (file.value.object_type === 'raster_file' || file.value.object_type === 'image_file') {
      console.log('🔄 [FileViewer] Starting automatic conversion for large file')
      startConversion()
    }
    return
  }
  
  const preview = findPreviewComponent(file.value)
  console.log('🔍 [FileViewer] Preview component search result:', preview)
  
  if (preview) {
    previewComponent.value = preview
    console.log('✅ [FileViewer] Found preview component:', preview.name)
  } else {
    previewComponent.value = null
    console.log('❌ [FileViewer] No preview component found for file type:', file.value.object_details?.mime_type)
    console.log('❌ [FileViewer] File details:', {
      id: file.value.id,
      name: file.value.name,
      object_type: file.value.object_type,
      mime_type: file.value.mime_type,
      'object_details.mime_type': file.value.object_details?.mime_type,
      'object_details.file_size': file.value.object_details?.file_size,
      type: file.value.type
    })
  }
}

function handlePreviewError(error) {
  console.error('❌ [FileViewer] Preview component error:', error)
  // Could show a toast notification or handle the error as needed
}

function handlePreviewLoaded() {
  console.log('✅ [FileViewer] Preview component loaded successfully')
}


// Check for active tasks
async function checkActiveTasks() {
  if (!file.value?.id) return

  try {
    console.log('[FileViewer] Checking for active tasks for file:', file.value.id)
    const tasks = await apiService.getItemTaskRecords(file.value.id, true) // activeOnly = true
    console.log('[FileViewer] Active tasks:', tasks)
    
    if (tasks && tasks.length > 0) {
      // Get the most recent active task
      const activeTask = tasks[0]
      console.log('[FileViewer] Found active task:', activeTask)
      
      if (activeTask.state === 'PROGRESS' || activeTask.state === 'PENDING') {
        activeTaskId.value = activeTask.task_id
        openTaskProgressModal();
        console.log('[FileViewer] Showing task progress modal for active task:', activeTask.task_id)
      }
    } else {
      console.log('[FileViewer] No active tasks found')
    }
  } catch (err) {
    console.error('[FileViewer] Failed to check active tasks:', err)
  }
}

async function startConversion() {
  if (!file.value?.id) {
    console.error('Cannot start conversion: file.value.id is missing', file.value)
    return
  }

  try {
    console.log('[FileViewer] Starting new conversion for file:', file.value.id)
    // Start the conversion task
    const response = await apiService.convertToGeoRaster(file.value.id)
    console.log('[FileViewer] Conversion started:', response)
    
    // Set the active task ID and show the modal
    activeTaskId.value = response.task_id
    openTaskProgressModal()
    console.log('[FileViewer] Task modal shown for new task:', response.task_id)
  } catch (err) {
    console.error('[FileViewer] Failed to start conversion:', err)
    alert(`Failed to start conversion: ${err.message}`)
  }
}

function handleTaskError(state) {
  console.error('[FileViewer] Task failed:', state)
  // Modal will show the error, user can close it manually
}

function handleTaskProgressClose() {
  console.log('[FileViewer] Closing task progress modal')
  closeTaskProgressModal()
  activeTaskId.value = null
}

// Layer control functions
function toggleLayerPanel() {
  layerPanelOpen.value = !layerPanelOpen.value
}

function toggleLayer(layerId, visible) {
  if (interactiveMapRef.value && interactiveMapRef.value.map) {
    const map = interactiveMapRef.value.map
    if (visible) {
      map.setLayoutProperty(layerId, 'visibility', 'visible')
    } else {
      map.setLayoutProperty(layerId, 'visibility', 'none')
    }
  }
}

function updateLayerOpacity(layerId, opacity) {
  if (interactiveMapRef.value && interactiveMapRef.value.map) {
    const map = interactiveMapRef.value.map
    if (layerId === 'geotiff-layer') {
      map.setPaintProperty(layerId, 'raster-opacity', parseFloat(opacity))
    } else if (layerId === 'osm-tiles') {
      map.setPaintProperty(layerId, 'raster-opacity', parseFloat(opacity))
    }
  }
}

// Map service URL functions
async function loadMapUrl() {
  if (!file.value?.id || file.value.object_type !== 'geo_raster_file') {
    mapUrl.value = null
    return
  }
  
  try {
    const response = await apiService.request(`/files/${file.value.id}/map`)
    mapUrl.value = response.map_url
  } catch (err) {
    console.error('Failed to load map URL:', err)
    mapUrl.value = null
  }
}


// File Actions handlers
function handleEdit() {
  if (!file.value?.id) return
  router.push({ name: 'FileEditor', query: { id: file.value.id } })
}

function handleDownload() {
  if (!file.value?.id) return
  // Open download URL in new tab
  window.open(`/api/v1/files/${file.value.id}/download`, '_blank')
}

function handleMove() {
  if (!file.value?.id) return
  openMoveModal()
}

function handleMoveCompleted() {
  // Reload the file to reflect any changes
  loadFile()
}

async function handleDelete() {
  if (!file.value?.id) return
  
  const fileName = getDisplayName()
  if (confirm(`Are you sure you want to delete "${fileName}"? This action cannot be undone.`)) {
    try {
      loading.value = true
      await apiService.deleteFile(file.value.id)
      
      // Show success message and go back
      alert(`"${fileName}" has been deleted successfully.`)
      goBack()
    } catch (err) {
      console.error('Failed to delete file:', err)
      alert(`Failed to delete file: ${err.message}`)
    } finally {
      loading.value = false
    }
  }
}


// Lifecycle
onMounted(async () => {
  await loadFile()
})

// Watch for prop changes
watch(() => props.treeItemId, async () => {
  await loadFile()
})
</script>

<style scoped>
.file-viewer {
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  overflow: hidden;
}

.viewer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #eee;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  flex-wrap: wrap;
}

/* Mobile header styles */
@media (max-width: 768px) {
  .viewer-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .edit-btn, .login-btn {
    flex: 1;
    justify-content: center;
    min-height: 44px;
  }
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
  /* Better touch targets for mobile */
  min-height: 44px;
}

.back-btn:hover {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

/* Mobile back button */
@media (max-width: 768px) {
  .back-btn {
    width: 100%;
    justify-content: center;
    padding: 0.75rem 1rem;
  }
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s;
  background: #007bff;
  color: white;
  border: none;
  min-height: 44px;
}

.edit-btn:hover {
  background: #0056b3;
}

.login-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s;
  background: #7b1fa2;
  color: white;
  border: none;
  min-height: 44px;
}

.login-btn:hover {
  background: #4a148c;
}


.viewer-content {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
}

/* Mobile viewer content */
@media (max-width: 768px) {
  .viewer-content {
    padding: 0.75rem;
  }
}

.content-layout {
  display: flex;
  gap: 2rem;
}

.content-main {
  flex: 1;
  min-width: 0;
}

.content-sidebar {
  width: 400px;
  flex-shrink: 0;
}

/* Mobile responsive layout */
@media (max-width: 768px) {
  .content-layout {
    flex-direction: column;
    gap: 1rem;
  }
  
  .content-sidebar {
    width: 100%;
    order: -1; /* Show sidebar first on mobile */
  }
}

.loading, .error, .not-found, .task-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error i, .not-found i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #dc3545;
}

.not-found i {
  color: #6c757d;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #0056b3;
}

.file-content {
  width: 100%;
}

.raster-viewer, .vector-viewer, .generic-viewer {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: #f8f9fa;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  margin-top: 1rem;
  color: #6c757d;
}

.preview-placeholder i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.file-tags {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.tag-item {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.tag-key {
  font-weight: 500;
  color: #495057;
  min-width: 80px;
}

.tag-value {
  color: #333;
  word-break: break-word;
}

/* Collection viewer styles */
.collection-viewer {
  width: 100%;
}

.collection-info {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  width: 100%;
  box-sizing: border-box;
}

.collection-description {
  color: #666;
  margin-bottom: 1.5rem;
}

.collection-stats {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

/* Mobile collection styles */
@media (max-width: 768px) {
  .collection-info {
    padding: 1rem;
    margin-bottom: 1rem;
    width: 100%;
  }
  
  .collection-stats {
    flex-direction: column;
    gap: 1rem;
  }
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.collection-actions {
  text-align: center;
}

.view-collection-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background-color 0.15s;
}

.view-collection-btn:hover {
  background: #0056b3;
}

/* File viewer styles */
.file-viewer {
  width: 100%;
}


/* Content sections */
.raster-content,
.vector-content,
.generic-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}


/* Interactive map container */
.interactive-map-container {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  min-height: 400px;
  height: 80vh;
}

/* Collection content */
.collection-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  width: 100%;
}

.collection-content p {
  color: #666;
  margin-bottom: 1.5rem;
}

/* Mobile collection content */
@media (max-width: 768px) {
  .collection-content {
    padding: 1rem;
    margin-bottom: 1rem;
    width: 100%;
    box-sizing: border-box;
  }
}






/* Layer Filter Block */
.layer-filter-block {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
  border-radius: 8px;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  border-radius: 8px 8px 0 0;
  transition: background-color 0.2s ease;
}

.filter-header:hover {
  background: #e9ecef;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.filter-icon {
  color: #666;
}

.filter-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
  color: #666;
}

.filter-toggle:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

.filter-toggle.expanded svg {
  transform: rotate(180deg);
}

.filter-toggle svg {
  transition: transform 0.2s ease;
}

.filter-content {
  padding: 16px;
  background: white;
  max-height: 200px;
  overflow-y: auto;
  border-radius: 0 0 8px 8px;
}

.layer-controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.layer-filter-item {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #f8f9fa;
  transition: all 0.2s ease;
}

.layer-filter-item:hover {
  border-color: #007bff;
  background: #f0f7ff;
}

.layer-filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  margin-bottom: 4px;
}

.layer-filter-checkbox {
  width: 16px;
  height: 16px;
  margin: 0;
  cursor: pointer;
  accent-color: #007bff;
}

.layer-filter-name {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.layer-description {
  font-size: 12px;
  color: #666;
  margin-left: 24px;
  margin-bottom: 8px;
}

.layer-opacity-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.opacity-section-label {
  display: block;
  font-size: 12px;
  color: #666;
  font-weight: 500;
  margin-bottom: 6px;
}

.layer-filter-opacity-slider {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: #e0e0e0;
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}

.layer-filter-opacity-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.layer-filter-opacity-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.layer-filter-opacity-slider:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
  opacity: 0.6;
}

.layer-filter-opacity-slider:disabled::-webkit-slider-thumb {
  background: #6c757d;
  cursor: not-allowed;
}

.layer-filter-opacity-slider:disabled::-moz-range-thumb {
  background: #6c757d;
  cursor: not-allowed;
}

.layer-opacity-section .opacity-section-label {
  color: #333;
}

.layer-filter-item:has(.layer-filter-opacity-slider:disabled) .opacity-section-label {
  color: #6c757d;
  opacity: 0.7;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .layer-controls-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-content {
    max-height: 150px;
  }
  
  .filter-header {
    padding: 10px 12px;
  }
}

/* Reset Confirmation Modal Styles */
.modal-overlay {
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

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 1.5rem 0 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 1rem;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.modal-close {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 6px;
  color: #6b7280;
  transition: all 0.15s;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 0 1.5rem 1rem 1.5rem;
  text-align: center;
}

.warning-icon {
  margin-bottom: 1rem;
}

.modal-body h4 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

.modal-body p {
  margin: 0 0 1rem 0;
  color: #6b7280;
  line-height: 1.5;
  text-align: left;
}

.modal-body p:last-child {
  margin-bottom: 0;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem 1.5rem 1.5rem;
  justify-content: flex-end;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 0.875rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.btn-danger {
  background: #dc2626;
  color: white;
  border: 1px solid #dc2626;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
  border-color: #b91c1c;
}

.btn-danger .spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style> 