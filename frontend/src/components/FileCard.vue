<template>
  <div class="file-card" :class="{ 'selected': selected }" @click="selectFile">
    <div class="file-icon" v-html="icon"></div>
    <div class="file-name">{{ name }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, required: true }, // 'raster', 'vector', 'text', 'binary'
  name: { type: String, required: true },
  selected: { type: Boolean, default: false },
  file: { type: Object, required: true } // Add file object prop
})

const emit = defineEmits(['click', 'file-selected'])

const icon = computed(() => {
  switch (props.type) {
    case 'raster':
      return `<svg width="40" height="40" viewBox="0 0 40 40"><rect x="4" y="8" width="32" height="24" rx="4" fill="#e0e7ef" stroke="#7faaff" stroke-width="2"/><circle cx="14" cy="24" r="4" fill="#7faaff"/><rect x="20" y="16" width="12" height="8" fill="#b3d1ff"/></svg>`
    case 'vector':
      return `<svg width="40" height="40" viewBox="0 0 40 40"><rect x="4" y="8" width="32" height="24" rx="4" fill="#e0f7e7" stroke="#2ecc71" stroke-width="2"/><circle cx="12" cy="28" r="3" fill="#2ecc71"/><circle cx="28" cy="14" r="3" fill="#2ecc71"/><line x1="12" y1="28" x2="28" y2="14" stroke="#27ae60" stroke-width="2"/></svg>`
    case 'text':
      return `<svg width="40" height="40" viewBox="0 0 40 40"><rect x="6" y="8" width="28" height="24" rx="4" fill="#f7f7e7" stroke="#f1c40f" stroke-width="2"/><rect x="12" y="16" width="16" height="2" fill="#f1c40f"/><rect x="12" y="22" width="10" height="2" fill="#f1c40f"/></svg>`
    case 'binary':
      return `<svg width="40" height="40" viewBox="0 0 40 40"><rect x="8" y="8" width="24" height="24" rx="6" fill="#f7e0ef" stroke="#e67ec7" stroke-width="2"/><circle cx="20" cy="20" r="6" fill="#e67ec7"/><rect x="16" y="16" width="8" height="8" fill="#fff"/></svg>`
    default:
      return ''
  }
})

function selectFile() {
  emit('click')
  emit('file-selected', props.file)
}
</script>

<style scoped>
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
</style> 