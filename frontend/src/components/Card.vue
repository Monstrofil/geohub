<template>
  <div 
    class="card-wrapper"
    :draggable="isAuthenticated && !props.moveBlocked"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
    @dragover="handleDragOver"
    @drop="handleDrop"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    :class="{ 'move-blocked': props.moveBlocked }"
  >
    <router-link :to="linkTo" class="card-link">
      <div class="card" :class="cardClasses">
        <!-- Header with icon and actions -->
        <div class="card-header">
          <div class="card-icon-section">
            <div class="card-icon" v-html="icon"></div>
            <div class="preset-name" v-if="matchedPreset?.name">{{ $t(`presets.${matchedPreset.translationKey}.name`, matchedPreset.name) }}</div>
          </div>
          <div class="card-actions" v-if="isAuthenticated">
            <router-link v-if="props.file?.id" :to="{name: 'FileEditor', query: { id: props.file.id }}" class="action-btn edit-btn" :title="`Edit ${itemType}`" @click.stop>
              <svg width="14" height="14" viewBox="0 0 16 16">
                <path d="M11 1L15 5L5 15H1V11L11 1Z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M8 4L12 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </router-link>
            <button v-if="props.file?.id" class="action-btn move-btn" @click.prevent.stop="handleMove" :title="`Move ${itemType}`">
              <svg width="14" height="14" viewBox="0 0 16 16">
                <path d="M8 2L12 6H10V10H6V6H4L8 2Z" fill="currentColor"/>
                <path d="M2 14H14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
            <button class="action-btn remove-btn" @click.prevent.stop="handleRemove" :title="`Remove ${itemType}`">
              <svg width="14" height="14" viewBox="0 0 16 16">
                <path d="M2 2l12 12M14 2l-12 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Preview fields -->
        <div class="preview-section" v-if="previewValues.length > 0">
          <div class="preview-fields">
            <div 
              v-for="field in previewValues" 
              :key="field.key" 
              class="preview-field"
            >
              <span class="field-label">{{ $t(`fields.${field.key}.label`, field.label) }}</span>
              <span class="field-value">{{ field.value || 'undefined' }}</span>
            </div>
          </div>
        </div>

        <!-- Collection-specific elements -->
        <div v-if="isCollection" class="collection-elements">
          <!-- Directory badge -->
          <div class="directory-badge">
            <svg width="12" height="12" viewBox="0 0 12 12">
              <path d="M2 2h8v8H2z" fill="none" stroke="#ffb300" stroke-width="1.2"/>
              <path d="M2 2h3l1 2h4" fill="none" stroke="#ffb300" stroke-width="1.2"/>
            </svg>
          </div>

          <!-- Drop indicators -->
          <div v-if="isDropTarget && !isMoving" class="drop-indicator">Drop here to move</div>
          <div v-if="isMoving" class="move-indicator">
            <div class="spinner"></div>
            <span>Moving...</span>
          </div>
        </div>

        <!-- File-specific elements -->
        <div v-if="isFile" class="file-elements">
          <!-- File type indicator -->
          <div class="file-type-indicator" v-if="fileType">
            <span class="type-badge">{{ fileType }}</span>
          </div>
        </div>
      </div>
    </router-link>
    
    <!-- Move Modal -->
    <MoveModal
      :show="showMoveModal"
      :item-id="file?.id"
      :item-name="name"
      :item-type="itemType"
      :current-path="currentPath"
      @close="showMoveModal = false"
      @moved="handleMoved"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import apiService from '../services/api.js'
import { getBaseFileType } from '../utils/fileHelpers.js'
import { matchTagsToPreset } from '../utils/tagMatcher.js'
import { loadFieldDefinitions } from '../utils/fieldResolver.js'
import { isAuthenticated } from '../stores/auth.js'
import MoveModal from './MoveModal.vue'

const props = defineProps({
  name: { type: String, required: true },
  selected: { type: Boolean, default: false },
  path: { type: String, required: true },
  treePath: { type: [String, Array], required: false },
  file: { type: Object, required: true },
  refName: { type: String, required: false },
  moveBlocked: { type: Boolean, default: false }
})

const emit = defineEmits(['click', 'file-selected', 'removed', 'move-start', 'move-end', 'moved', 'item-moved'])

// Drag state
const isDragging = ref(false)
const isDropTarget = ref(false)
const dragCounter = ref(0)
const isMoving = ref(false)

// Move modal state
const showMoveModal = ref(false)

// Determine if this is a file or collection
const isFile = computed(() => props.file?.object_type === 'file')
const isCollection = computed(() => props.file?.object_type === 'collection')
const itemType = computed(() => isCollection.value ? 'collection' : 'file')

// Get matched preset based on tags using centralized presets
const matchedPreset = computed(() => {
  if (!props.file?.tags) {
    return null
  }
  return matchTagsToPreset(props.file.tags, null, props.file.object_type)
})

// Preview field values
const previewValues = ref([])

// Load preview values when component mounts or file changes
const loadPreviewValues = async () => {
  if (!matchedPreset.value?.previewFields || !props.file?.tags) {
    previewValues.value = []
    return
  }
  
  const fieldDefinitions = await loadFieldDefinitions()
  const previewFields = matchedPreset.value.previewFields
  
  previewValues.value = previewFields.map(fieldKey => {
    const fieldDef = fieldDefinitions[fieldKey]
    const value = props.file.tags[fieldKey] || 'undefined'
    
    return {
      key: fieldKey,
      label: fieldDef?.label || fieldKey.charAt(0).toUpperCase() + fieldKey.slice(1),
      value: value
    }
  }).filter(Boolean)
}

// Watch for changes in matched preset and file tags
watch([matchedPreset, () => props.file?.tags], () => {
  loadPreviewValues()
}, { immediate: true })

const fileType = computed(() => {
  if (isFile.value) {
    return getBaseFileType(props.file)
  }
  return null
})

const fullPath = computed(() => {
  if (isCollection.value) {
    // Use the LTREE path from the collection object directly
    if (props.file && props.file.path) {
      return props.file.path
    }
    // Fallback to the path prop (which should be the LTREE path)
    return props.path
  } else {
    // For files, construct the full path
    if (props.treePath) {
      const currentPath = Array.isArray(props.treePath) ? props.treePath.join('/') : props.treePath
      return currentPath + '/' + props.path
    }
    return props.path
  }
})

const linkTo = computed(() => {
  if (isCollection.value) {
    return { name: 'FileList', query: { treePath: fullPath.value } }
  } else {
    return { name: 'FileViewer', query: { id: props.file.id } }
  }
})

const currentPath = computed(() => {
  return isCollection.value ? props.path : props.treePath
})

const cardClasses = computed(() => {
  const classes = {
    'selected': props.selected,
    'dragging': isDragging.value
  }
  
  if (isCollection.value) {
    classes['drop-target'] = isDropTarget.value
    classes['moving'] = isMoving.value
  }
  
  return classes
})

const icon = computed(() => {
  // First, try to use icon from matched preset based on tags
  if (matchedPreset.value && matchedPreset.value.icon) {
    // Use preset icon at its original 24x24 size for better proportion
    return matchedPreset.value.icon
  }
  
  if (isCollection.value) {
    // Fallback to enhanced folder icon at 32x32 for better proportion
    return `<svg width="32" height="32" viewBox="0 0 32 32">
      <defs>
        <linearGradient id="folderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#fff3c4;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#ffe082;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect x="3" y="11" width="26" height="15" rx="3" fill="url(#folderGrad)" stroke="#ffb300" stroke-width="1.5"/>
      <path d="M3 11l3-5h8l3 5" fill="url(#folderGrad)" stroke="#ffb300" stroke-width="1.5"/>
      <rect x="6" y="17" width="4" height="1.5" rx="0.5" fill="#ffb300" opacity="0.6"/>
      <rect x="12" y="17" width="4" height="1.5" rx="0.5" fill="#ffb300" opacity="0.6"/>
      <rect x="18" y="17" width="4" height="1.5" rx="0.5" fill="#ffb300" opacity="0.6"/>
      <rect x="6" y="20" width="4" height="1.5" rx="0.5" fill="#ffb300" opacity="0.6"/>
      <rect x="12" y="20" width="4" height="1.5" rx="0.5" fill="#ffb300" opacity="0.6"/>
    </svg>`
  } else {
    // Fallback to original file type-based icons at 32x32 for better proportion
    switch (fileType.value) {
      case 'raster':
        return `<svg width="32" height="32" viewBox="0 0 32 32">
          <rect x="3" y="6" width="26" height="20" rx="3" fill="#e0e7ef" stroke="#7faaff" stroke-width="1.5"/>
          <circle cx="11" cy="19" r="3" fill="#7faaff"/>
          <rect x="16" y="13" width="10" height="6" fill="#b3d1ff"/>
          <path d="M5 5l3 3M8 5l3 3M11 5l3 3" stroke="#7faaff" stroke-width="0.8" fill="none"/>
        </svg>`
      case 'vector':
        return `<svg width="32" height="32" viewBox="0 0 32 32">
          <rect x="3" y="6" width="26" height="20" rx="3" fill="#e0f7e7" stroke="#2ecc71" stroke-width="1.5"/>
          <circle cx="10" cy="22" r="2.5" fill="#2ecc71"/>
          <circle cx="22" cy="11" r="2.5" fill="#2ecc71"/>
          <line x1="10" y1="22" x2="22" y2="11" stroke="#27ae60" stroke-width="1.5"/>
          <path d="M5 5l3 3M8 5l3 3M11 5l3 3" stroke="#2ecc71" stroke-width="0.8" fill="none"/>
        </svg>`
      case 'raw':
        return `<svg width="32" height="32" viewBox="0 0 32 32">
          <rect x="5" y="6" width="22" height="20" rx="3" fill="#f7f7e7" stroke="#6c757d" stroke-width="1.5"/>
          <rect x="9" y="13" width="14" height="1.5" fill="#6c757d"/>
          <rect x="9" y="17" width="10" height="1.5" fill="#6c757d"/>
          <rect x="9" y="21" width="12" height="1.5" fill="#6c757d"/>
        </svg>`
      default:
        return `<svg width="32" height="32" viewBox="0 0 32 32">
          <rect x="6" y="6" width="20" height="20" rx="5" fill="#f8f9fa" stroke="#dee2e6" stroke-width="1.5"/>
          <path d="M11 13h10M11 16h7M11 19h5" stroke="#6c757d" stroke-width="1.2" fill="none"/>
        </svg>`
    }
  }
})

const handleRemove = async () => {
  if (confirm(`Are you sure you want to remove "${props.name}"?`)) {
    try {
      if (isCollection.value) {
        if (props.file && props.file.id) {
          await apiService.deleteCollection(props.file.id)
          emit('removed', props.path)
        } else {
          console.error('Cannot remove collection: missing collection ID')
          alert('Cannot remove collection: missing collection ID')
        }
      } else {
        await apiService.deleteTreeItem(props.file.id)
        emit('removed', props.path)
      }
    } catch (error) {
      console.error(`Failed to remove ${itemType.value}:`, error)
      alert(`Failed to remove ${itemType.value}: ${error.message}`)
    }
  }
}

// Drag and drop handlers
const handleDragStart = (event) => {
  if (!isAuthenticated.value || props.moveBlocked) {
    event.preventDefault()
    return
  }
  
  isDragging.value = true
  
  // Set the drag data
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('application/json', JSON.stringify({
    type: itemType.value,
    id: props.file.id,
    name: props.name,
    path: props.path,
    currentParentPath: props.treePath
  }))
  
  // Visual feedback
  event.dataTransfer.setDragImage(event.target, 50, 50)
  
  emit('move-start', props.file)
}

const handleDragEnd = () => {
  isDragging.value = false
  emit('move-end', props.file)
}

// Collection-specific drag handlers
const handleDragOver = (event) => {
  if (!isAuthenticated.value || props.moveBlocked || !isCollection.value) return
  
  event.preventDefault()
  event.stopPropagation()
  event.dataTransfer.dropEffect = 'move'
}

const handleDragEnter = (event) => {
  if (!isAuthenticated.value || props.moveBlocked || !isCollection.value) return
  
  event.preventDefault()
  event.stopPropagation()
  dragCounter.value++
  isDropTarget.value = true
}

const handleDragLeave = (event) => {
  if (!isAuthenticated.value || props.moveBlocked || !isCollection.value) return
  
  event.preventDefault()
  event.stopPropagation()
  dragCounter.value--
  if (dragCounter.value === 0) {
    isDropTarget.value = false
  }
}

const handleDrop = async (event) => {
  if (!isAuthenticated.value || props.moveBlocked || !isCollection.value) return
  
  event.preventDefault()
  event.stopPropagation() // Prevent event bubbling to parent components
  isDropTarget.value = false
  dragCounter.value = 0
  
  try {
    const dragData = JSON.parse(event.dataTransfer.getData('application/json'))
    
    // Don't allow dropping on self
    if (dragData.id === props.file?.id) {
      return
    }
    
    // Don't allow dropping a collection on its own descendant
    if (dragData.type === 'collection' && props.path.startsWith(dragData.path + '.')) {
      alert('Cannot move a collection into its own descendant')
      return
    }
    
    // Show loading state and emit to parent to block other operations
    isMoving.value = true
    
    // Move the item to this collection
    await apiService.updateTreeItem(dragData.id, {
      parent_path: props.path
    })
    
    emit('item-moved', {
      item: dragData,
      newParent: props.file,
      newParentPath: props.path
    })
    
  } catch (error) {
    console.error('Failed to move item:', error)
    alert(`Failed to move item: ${error.message}`)
  } finally {
    // Hide loading state
    isMoving.value = false
  }
}

// Move modal handlers
const handleMove = () => {
  showMoveModal.value = true
}

const handleMoved = (moveData) => {
  showMoveModal.value = false
  emit('moved', moveData)
}
</script>

<style scoped>
.card-wrapper {
  position: relative;
  display: inline-block;
  margin: 1rem;
}

.card-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.card {
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  width: 100%;
  flex: 1 1 240px;
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Collection-specific styling */
.card:has(.collection-elements) {
  background: linear-gradient(135deg, #fffbf0 0%, #fff8e1 100%);
  border-color: #ffe082;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.15);
}

.card:hover {
  border-color: #3b82f6;
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.card:has(.collection-elements):hover {
  border-color: #ffb300;
  box-shadow: 0 8px 25px rgba(255, 179, 0, 0.25);
}

.card.selected {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #f8faff 0%, #e6f2ff 100%);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
}

.card:has(.collection-elements).selected {
  border-color: #ff8f00;
  background: linear-gradient(135deg, #fff3c4 0%, #ffe082 100%);
  box-shadow: 0 8px 25px rgba(255, 143, 0, 0.3);
}

.card.dragging {
  opacity: 0.6;
  transform: scale(0.95) rotate(2deg);
  z-index: 1000;
}

.card.drop-target {
  border-color: #4caf50;
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.3);
  transform: scale(1.05);
}

.card.moving {
  opacity: 0.8;
  pointer-events: none;
}

.card-wrapper.move-blocked {
  opacity: 0.6;
  cursor: not-allowed;
}

.card-wrapper.move-blocked .card {
  pointer-events: none;
}

/* Header */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  padding: 1rem 1rem 0 1rem;
}

.card-icon-section {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
  flex-grow: 1;
}

.card-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preset-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-align: center;
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: rgba(249, 250, 251, 0.8);
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
  border: 1px solid rgba(229, 231, 235, 0.5);
}

.card-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.card:hover .card-actions {
  opacity: 1;
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.edit-btn {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.edit-btn:hover {
  background: #3b82f6;
  color: white;
  transform: scale(1.1);
}

.move-btn {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.move-btn:hover {
  background: #f59e0b;
  color: white;
  transform: scale(1.1);
}

.remove-btn {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.remove-btn:hover {
  background: #ef4444;
  color: white;
  transform: scale(1.1);
}

/* Preview section */
.preview-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  min-width: 0; /* Allow shrinking */
  padding: 0 1rem;
  padding-bottom: 1rem;
}

.preview-fields {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.preview-field {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0.5rem;
  background: rgba(249, 250, 251, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(229, 231, 235, 0.5);
  width: 100%;
  box-sizing: border-box;
}

.card:has(.collection-elements) .preview-field {
  background: rgba(255, 248, 225, 0.8);
  border-color: rgba(255, 224, 130, 0.5);
}

.card:has(.collection-elements) .preset-name {
  background: rgba(255, 248, 225, 0.8);
  border-color: rgba(255, 224, 130, 0.5);
  color: #92400e;
}

.field-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.card:has(.collection-elements) .field-label {
  color: #92400e;
}

.field-value {
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  text-align: left;
  word-break: break-word;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Collection-specific elements */
.collection-elements {
  position: relative;
  padding: 0 1rem 1rem 1rem;
}

.directory-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #ffe082;
  border-radius: 6px;
  padding: 2px 4px;
  backdrop-filter: blur(4px);
  z-index: 5;
}

.drop-indicator {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  background: #4caf50;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  z-index: 10;
}

.move-indicator {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  background: #2196f3;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 4px;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* File-specific elements */
.file-elements {
  margin-top: auto;
  padding: 0 1rem 1rem 1rem;
}

.file-type-indicator {
  padding-top: 0.75rem;
  display: flex;
  justify-content: center;
}

.type-badge {
  background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
  color: #6b7280;
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  border: 1px solid rgba(209, 213, 219, 0.5);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .card {
    min-width: 180px;
    max-width: 300px;
    min-height: 140px;
  }
  
  .card-header {
    padding: 0.75rem 0.75rem 0 0.75rem;
  }
  
  .preview-section {
    padding: 0 0.75rem;
  }
  
  .collection-elements {
    padding: 0 0.75rem 0.75rem 0.75rem;
  }
  
  .file-elements {
    padding: 0 0.75rem 0.75rem 0.75rem;
  }
  
  .preview-field {
    padding: 0.375rem;
  }
  
  .field-label {
    font-size: 0.65rem;
  }
  
  .field-value {
    font-size: 0.75rem;
  }
}
</style>
