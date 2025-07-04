<template>
  <div class="tree-card" :class="{ 'selected': selected }" @click="selectTree">
    <div class="tree-icon" v-html="icon"></div>
    <div class="tree-name">{{ name }}sdfsdf</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  selected: { type: Boolean, default: false },
  tree: { type: Object, required: true }
})

const emit = defineEmits(['click', 'tree-selected'])

const icon = computed(() => {
  // Simple folder icon
  return `<svg width="40" height="40" viewBox="0 0 40 40">
    <rect x="4" y="14" width="32" height="18" rx="4" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
    <path d="M4 14l4-6h10l4 6" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
  </svg>`
})

function selectTree() {
  emit('click')
  emit('tree-selected', props.tree)
}
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
}
</style> 