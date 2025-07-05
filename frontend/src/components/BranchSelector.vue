<template>
  <div class="section section-branch-selector">
    <label for="branch-select">Гілка:</label>
    <select id="branch-select" v-model="selectedBranch" @change="emitBranchChange">
      <option v-for="ref in refs" :key="ref.name" :value="ref">
        {{ ref.name }}
      </option>
    </select>
    <span v-if="selectedBranch" class="current-branch">(Поточна гілка: {{ selectedBranch }})</span>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import apiService from '../services/api.js'

const props = defineProps({
  modelValue: String
})
const emit = defineEmits(['update:modelValue', 'onBranchChange'])

// Expose loadRefs method for parent components
defineExpose({
  loadRefs
})

const refs = ref([])
const selectedBranch = ref(null)

onMounted(async () => {
  await loadRefs()
})

watch(() => props.modelValue, (val) => {
  if (val && val !== selectedBranch.value) {
    selectedBranch.value = val
  }
})

async function loadRefs() {
  try {
    const response = await apiService.getRefs()
    refs.value = response
    selectedBranch.value = refs.value[0]
  } catch (err) {
    console.error('Failed to load refs:', err)
  }

  emitBranchChange(selectedBranch.value)
}

function emitBranchChange() {
  emit('update:modelValue', selectedBranch.value)
  emit('onBranchChange', selectedBranch.value)
}
</script>

<style scoped>
.section-branch-selector {
  padding: 1rem;
  background: #e9f5ff;
  border-bottom: 1px solid #b3d8fd;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.current-branch {
  font-weight: bold;
  color: #1976d2;
}
</style> 