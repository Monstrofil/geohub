<template>
  <div class="file-card-container">
    <router-link :to="{name: 'FileViewer', query: { id: file.id }}">
      <div class="file-card" :class="{ 'selected': selected }">
        <div class="file-icon" v-html="icon"></div>
        <div class="file-name">{{ name }}</div>
      </div>
    </router-link>
    <router-link :to="{name: 'FileEditor', query: { id: file.id }}">
      <button 
        class="edit-btn" 
        title="Edit file"
      >
        <svg width="16" height="16" viewBox="0 0 16 16">
          <path d="M11 1L15 5L5 15H1V11L11 1Z" stroke="#007bff" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M8 4L12 8" stroke="#007bff" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </router-link>
    <button 
      class="remove-btn" 
      @click.stop="handleRemove"
      title="Remove file"
    >
      <svg width="16" height="16" viewBox="0 0 16 16">
        <path d="M2 2l12 12M14 2l-12 12" stroke="#dc3545" stroke-width="2" fill="none" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import apiService from '../services/api.js'
import { getBaseFileType } from '../utils/fileHelpers.js'
import { matchTagsToPreset } from '../utils/tagMatcher.js'

const props = defineProps({
  name: { type: String, required: true },
  selected: { type: Boolean, default: false },
  path: { type: String, required: true },
  treePath: { type: [String, Array], required: false },
  file: { type: Object, required: true },
  refName: { type: String, required: true }
})

const emit = defineEmits(['click', 'file-selected', 'removed'])

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

</script>

<style scoped>
.file-card-container {
  position: relative;
  display: inline-block;
}

.file-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 1.25rem 1rem;
  margin: 0.5rem;
  width: 120px;
  height: 120px;
  transition: box-shadow 0.15s, border-color 0.15s, background-color 0.15s, transform 0.1s;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.file-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.10);
  transform: translateY(-2px);
}
.file-card.selected {
  border-color: #007bff;
  background-color: #f8f9ff;
  box-shadow: 0 4px 16px rgba(0,123,255,0.15);
}
.file-icon {
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.file-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #333;
  text-align: center;
  word-break: break-word;
  line-height: 1.3;
  max-height: 2.6rem;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.edit-btn {
  position: absolute;
  top: 6px;
  right: 28px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #007bff;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, background-color 0.2s, transform 0.1s;
  z-index: 10;
  backdrop-filter: blur(4px);
}

.file-card-container:hover .edit-btn {
  opacity: 1;
}

.edit-btn:hover {
  background: #007bff;
  transform: scale(1.05);
}

.edit-btn:hover svg path {
  stroke: white;
}

.remove-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #dc3545;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, background-color 0.2s, transform 0.1s;
  z-index: 10;
  backdrop-filter: blur(4px);
}

.file-card-container:hover .remove-btn {
  opacity: 1;
}

.remove-btn:hover {
  background: #dc3545;
  transform: scale(1.05);
}

.remove-btn:hover svg path {
  stroke: white;
}
</style> 