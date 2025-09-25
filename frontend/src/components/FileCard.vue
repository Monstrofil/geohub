<template>
  <div 
    class="file-card-wrapper"
    :draggable="isAuthenticated && !props.moveBlocked"
    @dragstart="handleDragStart"
    @dragend="handleDragEnd"
    :class="{ 'move-blocked': props.moveBlocked }"
  >
    <router-link :to="{name: 'FileViewer', query: { id: file.id }}" class="file-card-link">
      <div class="file-card" :class="{ 'selected': selected, 'dragging': isDragging }">
        <!-- Header with icon and actions -->
        <div class="file-header">
          <div class="file-icon" v-html="icon"></div>
          <div class="file-actions" v-if="isAuthenticated">
            <router-link :to="{name: 'FileEditor', query: { id: file.id }}" class="action-btn edit-btn" title="Edit file">
              <svg width="14" height="14" viewBox="0 0 16 16">
                <path d="M11 1L15 5L5 15H1V11L11 1Z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M8 4L12 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </router-link>
            <button class="action-btn move-btn" @click.stop="handleMove" title="Move file">
              <svg width="14" height="14" viewBox="0 0 16 16">
                <path d="M8 2L12 6H10V10H6V6H4L8 2Z" fill="currentColor"/>
                <path d="M2 14H14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
            <button class="action-btn remove-btn" @click.stop="handleRemove" title="Remove file">
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
              <span class="field-value">{{ field.value }}</span>
            </div>
          </div>
        </div>

        <!-- File type indicator -->
        <div class="file-type-indicator" v-if="fileType">
          <span class="type-badge">{{ fileType }}</span>
        </div>
      </div>
    </router-link>
    
    <!-- Move Modal -->
    <MoveModal
      :show="showMoveModal"
      :item-id="file.id"
      :item-name="name"
      :item-type="'file'"
      :current-path="treePath"
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
  refName: { type: String, required: true },
  moveBlocked: { type: Boolean, default: false }
})

const emit = defineEmits(['click', 'file-selected', 'removed', 'move-start', 'move-end', 'moved'])

// Drag state
const isDragging = ref(false)

// Move modal state
const showMoveModal = ref(false)

const fileType = computed(() => {
  return getBaseFileType(props.file)
})

// Get matched preset based on file tags using centralized presets
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
    const value = props.file.tags[fieldKey]
    
    if (!value) return null
    
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
  if (props.treePath) {
    const currentPath = Array.isArray(props.treePath) ? props.treePath.join('/') : props.treePath
    return currentPath + '/' + props.path
  }
  return props.path
})

const icon = computed(() => {
  // First, try to use icon from matched preset based on tags
  if (matchedPreset.value && matchedPreset.value.icon) {
    // Use preset icon at its original 24x24 size for better proportion
    return matchedPreset.value.icon
  }
  
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
})

const handleRemove = async () => {
  if (confirm(`Are you sure you want to remove "${props.name}"?`)) {
    try {
      await apiService.deleteTreeItem(props.file.id)
      emit('removed', props.path)
    } catch (error) {
      console.error('Failed to remove file:', error)
      alert(`Failed to remove file: ${error.message}`)
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
    type: 'file',
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
.file-card-wrapper {
  position: relative;
  display: inline-block;
  margin: 0.5rem;
}

.file-card-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.file-card {
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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

.file-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.file-card.selected {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #f8faff 0%, #e6f2ff 100%);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
}

.file-card.dragging {
  opacity: 0.6;
  transform: scale(0.95) rotate(2deg);
  z-index: 1000;
}

.file-card-wrapper.move-blocked {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-card-wrapper.move-blocked .file-card {
  pointer-events: none;
}

/* Header */
.file-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.file-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.file-card:hover .file-actions {
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

/* File name */
.file-name {
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
  background: rgba(249, 250, 251, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(229, 231, 235, 0.5);
}

.field-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: #6b7280;
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

/* File type indicator */
.file-type-indicator {
  margin-top: auto;
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
  .file-card {
    width: 200px;
    min-height: 140px;
    padding: 0.75rem;
  }
  
  .file-name {
    font-size: 0.8rem;
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