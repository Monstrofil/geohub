<template>
  <div class="tree-card-container">
    <router-link :to="{name: 'FileList', query: { treePath: fullPath }}">
      <div class="tree-card" :class="{ 'selected': selected }">
        <div class="directory-badge">
          <svg width="12" height="12" viewBox="0 0 12 12">
            <path d="M2 2h8v8H2z" fill="none" stroke="#ffb300" stroke-width="1.2"/>
            <path d="M2 2h3l1 2h4" fill="none" stroke="#ffb300" stroke-width="1.2"/>
          </svg>
        </div>
        <div class="tree-icon" v-html="icon"></div>
        <div class="tree-name">{{ name }}</div>
      </div>
    </router-link>
    <router-link :to="{name: 'FileEditor', query: { id: props.file.id }}" v-if="props.file?.id">
      <button 
        class="edit-btn" 
        title="Edit collection"
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
      title="Remove collection"
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
import { matchTagsToPreset } from '../utils/tagMatcher.js'

const props = defineProps({
  name: { type: String, required: true },
  selected: { type: Boolean, default: false },
  path: { type: String, required: true },
  treePath: { type: [String, Array], required: false },
  file: { type: Object, required: false } // Add file prop to access collection object
})

const emit = defineEmits(['edit', 'removed'])

// Get matched preset based on collection tags using centralized presets
const matchedPreset = computed(() => {
  if (!props.file?.tags) {
    return null
  }
  return matchTagsToPreset(props.file.tags, null, props.file.object_type)
})

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

</script>

<style scoped>
.tree-card-container {
  position: relative;
  display: inline-block;
}

.tree-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fffbf0 0%, #fff8e1 100%);
  border: 2px solid #ffe082;
  border-radius: 16px;
  box-shadow: 0 3px 12px rgba(255, 193, 7, 0.15);
  padding: 1.25rem 1rem;
  margin: 0.5rem;
  width: 120px;
  height: 120px;
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.tree-card:hover {
  box-shadow: 0 6px 20px rgba(255, 193, 7, 0.25);
  transform: translateY(-3px) scale(1.02);
  border-color: #ffb300;
}
.tree-card.selected {
  border-color: #ff8f00;
  background: linear-gradient(135deg, #fff3c4 0%, #ffe082 100%);
  box-shadow: 0 6px 20px rgba(255, 143, 0, 0.3);
  transform: scale(1.05);
}
.tree-icon {
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  filter: drop-shadow(0 1px 2px rgba(255, 179, 0, 0.3));
}
.tree-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #333;
  text-align: center;
  word-break: break-word;
  line-height: 1.3;
  max-height: 2.2rem;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 0.1rem;
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

.tree-card-container:hover .edit-btn {
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

.tree-card-container:hover .remove-btn {
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