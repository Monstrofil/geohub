<template>
  <div class="tree-card" :class="{ 'selected': selected }">
    <div class="tree-icon" v-html="icon" title="Edit category"></div>
    <router-link :to="{name: 'FileEditor', params: { treePath: fullPath }}">
        <div class="tree-name"title="Edit category">Name {{ name }}</div>
    </router-link>
    <div class="tree-name tree-path">{{ path }}</div>

    
    <router-link :to="{name: 'FileList', params: { treePath: fullPath }}">
        <button class="view-contents-btn" title="View files in this category">
        <svg width="20" height="20" viewBox="0 0 20 20">
            <path d="M5 10h10M12 7l3 3-3 3" stroke="#ffb300" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        </button>
    </router-link>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  selected: { type: Boolean, default: false },
  path: { type: String, required: true },
  treePath: { type: [String, Array], required: false }
})

const emit = defineEmits(['edit'])

const fullPath = computed(() => {
  if (props.treePath) {
    const currentPath = Array.isArray(props.treePath) ? props.treePath.join('/') : props.treePath
    return currentPath + '/' + props.path
  }
  return props.path
})

const icon = computed(() => {
  // Simple folder icon
  return `<svg width="40" height="40" viewBox="0 0 40 40">
    <rect x="4" y="14" width="32" height="18" rx="4" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
    <path d="M4 14l4-6h10l4 6" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
  </svg>`
})

</script>

<style scoped>
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
.view-contents-btn {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.2rem;
  border-radius: 4px;
  transition: background 0.15s;
}
.view-contents-btn:hover {
  background: #fff3cd;
}
</style> 