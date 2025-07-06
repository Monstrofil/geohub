<template>
  <div class="section section-branch-selector">
    <label for="branch-select">Гілка:</label>
    <select id="branch-select" v-model="selectedBranch" @change="emitBranchChange">
      <option v-for="ref in props.refs" :key="ref.name" :value="ref">
        {{ ref.name }}
      </option>
    </select>
    <span v-if="selectedBranch" class="current-branch">(Поточна гілка: {{ selectedBranch }})</span>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'

const props = defineProps({
  modelValue: Object, // Changed to Object to pass the full branch object
  refs: Array
})
const emit = defineEmits(['update:modelValue', 'onBranchChange'])

const selectedBranch = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

onMounted(() => {
  // No need to load refs here anymore, parent will provide them
})

// No need for this watch anymore since we're using computed

// Removed loadRefs function - no longer needed

function emitBranchChange() {
  emit('onBranchChange', selectedBranch.value)
}
</script>

<style scoped>
.section-branch-selector {
  display: none; /* Hide the branch selector section */
}
.current-branch {
  font-weight: bold;
  color: #1976d2;
}
</style> 