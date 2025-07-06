<template>
  <div class="file-card-container">
    <router-link :to="{name: 'FileViewer', params: { treePath: fullPath }}">
      <div class="file-card" :class="{ 'selected': selected }">
        <div class="file-icon" v-html="icon"></div>
        <div class="file-name">{{ name }}</div>
      </div>
    </router-link>
    <router-link :to="{name: 'FileEditor', params: { treePath: fullPath }}">
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
  return props.file.base_file_type || 'raw'
})



const fullPath = computed(() => {
  if (props.treePath) {
    const currentPath = Array.isArray(props.treePath) ? props.treePath.join('/') : props.treePath
    return currentPath + '/' + props.path
  }
  return props.path
})

const icon = computed(() => {
  switch (fileType.value) {
    case 'raster':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="4" y="8" width="32" height="24" rx="4" fill="#e0e7ef" stroke="#7faaff" stroke-width="2"/>
        <circle cx="14" cy="24" r="4" fill="#7faaff"/>
        <rect x="20" y="16" width="12" height="8" fill="#b3d1ff"/>
        <path d="M6 6l4 4M10 6l4 4M14 6l4 4" stroke="#7faaff" stroke-width="1" fill="none"/>
      </svg>`
    case 'vector':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="4" y="8" width="32" height="24" rx="4" fill="#e0f7e7" stroke="#2ecc71" stroke-width="2"/>
        <circle cx="12" cy="28" r="3" fill="#2ecc71"/>
        <circle cx="28" cy="14" r="3" fill="#2ecc71"/>
        <line x1="12" y1="28" x2="28" y2="14" stroke="#27ae60" stroke-width="2"/>
        <path d="M6 6l4 4M10 6l4 4M14 6l4 4" stroke="#2ecc71" stroke-width="1" fill="none"/>
      </svg>`
    case 'raw':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="6" y="8" width="28" height="24" rx="4" fill="#f7f7e7" stroke="#6c757d" stroke-width="2"/>
        <rect x="12" y="16" width="16" height="2" fill="#6c757d"/>
        <rect x="12" y="22" width="10" height="2" fill="#6c757d"/>
        <rect x="12" y="28" width="14" height="2" fill="#6c757d"/>
      </svg>`
    default:
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="8" y="8" width="24" height="24" rx="6" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
        <path d="M14 16h12M14 20h8M14 24h6" stroke="#6c757d" stroke-width="1.5" fill="none"/>
      </svg>`
  }
})

const handleRemove = async () => {
  if (confirm(`Are you sure you want to remove "${props.name}"?`)) {
    try {
              await apiService.removeObjectInTree(props.refName, fullPath.value)
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
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 1rem;
  margin: 0.5rem;
  width: 120px;
  min-height: 140px;
  transition: box-shadow 0.15s, border-color 0.15s, background-color 0.15s;
  cursor: pointer;
}
.file-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.10);
}
.file-card.selected {
  border-color: #007bff;
  background-color: #f8f9ff;
  box-shadow: 0 4px 16px rgba(0,123,255,0.15);
}
.file-icon {
  margin-bottom: 0.5rem;
}
.file-name {
  font-size: 1em;
  color: #333;
  text-align: center;
  word-break: break-all;
}

.edit-btn {
  position: absolute;
  top: 5px;
  right: 30px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #007bff;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, background-color 0.2s;
  z-index: 10;
}

.file-card-container:hover .edit-btn {
  opacity: 1;
}

.edit-btn:hover {
  background: #007bff;
}

.edit-btn:hover svg path {
  stroke: white;
}

.remove-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #dc3545;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, background-color 0.2s;
  z-index: 10;
}

.file-card-container:hover .remove-btn {
  opacity: 1;
}

.remove-btn:hover {
  background: #dc3545;
}

.remove-btn:hover svg path {
  stroke: white;
}
</style> 