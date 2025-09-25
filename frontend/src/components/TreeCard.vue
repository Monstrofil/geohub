<template>
  <div 
    class="tree-card-wrapper"
    :draggable="isAuthenticated && !props.moveBlocked"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
    @dragover="handleDragOver"
    @drop="handleDrop"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    :class="{ 'move-blocked': props.moveBlocked }"
  >
    <router-link :to="{name: 'FileList', query: { treePath: fullPath }}" class="tree-card-link">
      <div class="tree-card" :class="{ 'selected': selected, 'dragging': isDragging, 'drop-target': isDropTarget, 'moving': isMoving }">
        <!-- Header with icon and actions -->
        <div class="tree-header">
          <div class="tree-icon" v-html="icon"></div>
          <div class="tree-actions" v-if="isAuthenticated">
            <router-link v-if="props.file?.id" :to="{name: 'FileEditor', query: { id: props.file.id }}" class="action-btn edit-btn" title="Edit collection">
              <svg width="14" height="14" viewBox="0 0 16 16">
                <path d="M11 1L15 5L5 15H1V11L11 1Z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M8 4L12 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </router-link>
            <button v-if="props.file?.id" class="action-btn move-btn" @click.stop="handleMove" title="Move collection">
              <svg width="14" height="14" viewBox="0 0 16 16">
                <path d="M8 2L12 6H10V10H6V6H4L8 2Z" fill="currentColor"/>
                <path d="M2 14H14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
            <button class="action-btn remove-btn" @click.stop="handleRemove" title="Remove collection">
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
              <span class="field-label">{{ field.label }}</span>
              <span class="field-value">{{ field.value || 'undefined' }}</span>
            </div>
          </div>
        </div>

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
    </router-link>
    
    <!-- Move Modal -->
    <MoveModal
      :show="showMoveModal"
      :item-id="file?.id"
      :item-name="name"
      :item-type="'collection'"
      :current-path="path"
      @close="showMoveModal = false"
      @moved="handleMoved"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import apiService from '../services/api.js'
import { matchTagsToPreset } from '../utils/tagMatcher.js'
import { loadFieldDefinitions } from '../utils/fieldResolver.js'
import { isAuthenticated } from '../stores/auth.js'
import MoveModal from './MoveModal.vue'

const props = defineProps({
  name: { type: String, required: true },
  selected: { type: Boolean, default: false },
  path: { type: String, required: true },
  treePath: { type: [String, Array], required: false },
  file: { type: Object, required: false }, // Add file prop to access collection object
  moveBlocked: { type: Boolean, default: false }
})

const emit = defineEmits(['edit', 'removed', 'move-start', 'move-end', 'item-moved', 'moved'])

// Drag state
const isDragging = ref(false)
const isDropTarget = ref(false)
const dragCounter = ref(0)
const isMoving = ref(false)

// Move modal state
const showMoveModal = ref(false)

// Get matched preset based on collection tags using centralized presets
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

const fullPath = computed(() => {
  // Use the LTREE path from the collection object directly
  if (props.file && props.file.path) {
    return props.file.path
  }
  // Fallback to the path prop (which should be the LTREE path)
  return props.path
})

const icon = computed(() => {
  // First, try to use icon from matched preset based on tags
  if (matchedPreset.value && matchedPreset.value.icon) {
    // Use preset icon at its original 24x24 size for better proportion
    return matchedPreset.value.icon
  }
  
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
})

const handleRemove = async () => {
  if (confirm(`Are you sure you want to remove collection "${props.name}"?`)) {
    try {
      if (props.file && props.file.id) {
        await apiService.deleteCollection(props.file.id)
        emit('removed', props.path)
      } else {
        console.error('Cannot remove collection: missing collection ID')
        alert('Cannot remove collection: missing collection ID')
      }
    } catch (error) {
      console.error('Failed to remove collection:', error)
      alert(`Failed to remove collection: ${error.message}`)
    }
  }
}

// Drag and drop handlers
const handleDragStart = (event) => {
  if (!isAuthenticated.value || !props.file?.id || props.moveBlocked) {
    event.preventDefault()
    return
  }
  
  isDragging.value = true
  
  // Set the drag data
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('application/json', JSON.stringify({
    type: 'collection',
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

const handleDragOver = (event) => {
  if (!isAuthenticated.value || props.moveBlocked) return
  
  event.preventDefault()
  event.stopPropagation()
  event.dataTransfer.dropEffect = 'move'
}

const handleDragEnter = (event) => {
  if (!isAuthenticated.value || props.moveBlocked) return
  
  event.preventDefault()
  event.stopPropagation()
  dragCounter.value++
  isDropTarget.value = true
}

const handleDragLeave = (event) => {
  if (!isAuthenticated.value || props.moveBlocked) return
  
  event.preventDefault()
  event.stopPropagation()
  dragCounter.value--
  if (dragCounter.value === 0) {
    isDropTarget.value = false
  }
}

const handleDrop = async (event) => {
  if (!isAuthenticated.value || props.moveBlocked) return
  
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
.tree-card-wrapper {
  position: relative;
  display: inline-block;
  margin: 0.5rem;
}

.tree-card-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.tree-card {
  background: linear-gradient(135deg, #fffbf0 0%, #fff8e1 100%);
  border: 2px solid #ffe082;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.15);
  padding: 1rem;
  width: 240px;
  min-height: 160px;
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.tree-card:hover {
  border-color: #ffb300;
  box-shadow: 0 8px 25px rgba(255, 179, 0, 0.25);
  transform: translateY(-2px);
}

.tree-card.selected {
  border-color: #ff8f00;
  background: linear-gradient(135deg, #fff3c4 0%, #ffe082 100%);
  box-shadow: 0 8px 25px rgba(255, 143, 0, 0.3);
}

.tree-card.dragging {
  opacity: 0.6;
  transform: scale(0.95) rotate(2deg);
  z-index: 1000;
}

.tree-card.drop-target {
  border-color: #4caf50;
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
  box-shadow: 0 8px 25px rgba(76, 175, 80, 0.3);
  transform: scale(1.05);
}

/* Header */
.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.tree-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tree-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.tree-card:hover .tree-actions {
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

.tree-card.moving {
  opacity: 0.8;
  pointer-events: none;
}

.tree-card-wrapper.move-blocked {
  opacity: 0.6;
  cursor: not-allowed;
}

.tree-card-wrapper.move-blocked .tree-card {
  pointer-events: none;
}
/* Collection name */
.tree-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1f2937;
  text-align: center;
  word-break: break-word;
  line-height: 1.3;
  margin-bottom: 0.75rem;
  min-height: 2.6rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Preview section */
.preview-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
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
  background: rgba(255, 248, 225, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(255, 224, 130, 0.5);
}

.field-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: #92400e;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
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

/* Responsive adjustments */
@media (max-width: 768px) {
  .tree-card {
    width: 200px;
    min-height: 140px;
    padding: 0.75rem;
  }
  
  .tree-name {
    font-size: 0.8rem;
  }
}

</style> 