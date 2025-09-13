<template>
  <div class="tree-card-container">
    <router-link :to="{name: 'FileList', query: { treePath: fullPath }}">
      <div class="tree-card" :class="{ 'selected': selected }">
        <div class="tree-icon" v-html="icon"></div>
        <div class="tree-name">Name {{ name }}</div>
        <div class="tree-name tree-path">{{ path }}</div>
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

const props = defineProps({
  name: { type: String, required: true },
  selected: { type: Boolean, default: false },
  path: { type: String, required: true },
  treePath: { type: [String, Array], required: false },
  file: { type: Object, required: false } // Add file prop to access collection object
})

const emit = defineEmits(['edit', 'removed'])

const fullPath = computed(() => {
  // Use the LTREE path from the collection object directly
  if (props.file && props.file.path) {
    return props.file.path
  }
  // Fallback to the path prop (which should be the LTREE path)
  return props.path
})

const icon = computed(() => {
  // Simple folder icon
  return `<svg width="40" height="40" viewBox="0 0 40 40">
    <rect x="4" y="14" width="32" height="18" rx="4" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
    <path d="M4 14l4-6h10l4 6" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
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
  position: relative;
}
.tree-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.10);
}
.tree-card.selected {
  border-color: #ffb300;
  background-color: #fffbe6;
  box-shadow: 0 4px 16px rgba(255,179,0,0.10);
}
.tree-icon {
  margin-bottom: 0.5rem;
}
.tree-name {
  font-size: 1em;
  color: #333;
  text-align: center;
  word-break: break-all;
  margin-bottom: 0.5rem;
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

.tree-card-container:hover .edit-btn {
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

.tree-card-container:hover .remove-btn {
  opacity: 1;
}

.remove-btn:hover {
  background: #dc3545;
}

.remove-btn:hover svg path {
  stroke: white;
}
</style> 