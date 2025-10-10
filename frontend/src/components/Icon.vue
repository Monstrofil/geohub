<template>
  <svg 
    :width="size" 
    :height="size" 
    viewBox="0 0 24 24" 
    fill="none"
    :class="iconClass"
  >
    <!-- Error Icon -->
    <template v-if="name === 'error'">
      <circle cx="12" cy="12" r="10" fill="currentColor"/>
      <path d="M15 9l-6 6M9 9l6 6" stroke="white" stroke-width="2" stroke-linecap="round"/>
    </template>
    
    <!-- Success Icon -->
    <template v-else-if="name === 'success'">
      <circle cx="12" cy="12" r="10" fill="currentColor"/>
      <path d="M9 12l2 2 4-4" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </template>
    
    <!-- Refresh Icon -->
    <template v-else-if="name === 'refresh'">
      <path d="M1 4v6h6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    </template>
    
    <!-- Spinner Icon -->
    <template v-else-if="name === 'spinner'">
      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/>
      <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
    </template>
    
    <!-- Clock Icon -->
    <template v-else-if="name === 'clock'">
      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
      <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </template>
    
    <!-- Close Icon -->
    <template v-else-if="name === 'close'">
      <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </template>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    required: true
  },
  size: {
    type: [String, Number],
    default: 20
  }
})

const iconClass = computed(() => ({
  'icon': true,
  [`icon-${props.name}`]: true
}))
</script>

<style scoped>
.icon {
  --color-error: #dc3545;
  --color-success: #28a745;
  
  display: inline-block;
  flex-shrink: 0;
}

.icon-error {
  color: var(--color-error);
}

.icon-success {
  color: var(--color-success);
}

.icon-refresh,
.icon-spinner,
.icon-clock,
.icon-close {
  color: currentColor;
}
</style>
