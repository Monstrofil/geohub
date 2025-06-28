<template>
  <div class="top-toolbar">
    <div class="toolbar-left">
      <button 
        class="pure-button" 
        @click="$emit('refresh')"
      >
        <i class="fas fa-sync-alt"></i> Refresh
      </button>
      
      <button 
        class="pure-button" 
        @click="$emit('upload')"
      >
        <i class="fas fa-upload"></i> Upload
      </button>
    </div>
  </div>
</template>

<script setup>
defineEmits(['refresh', 'upload'])
</script>

<style scoped>
.top-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  flex-grow: 1;
}

.toolbar-left {
  display: flex;
  gap: 0.5rem;
}

.pure-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  text-decoration: none;
  font-size: 0.9rem;
}

.pure-button:hover:not(:disabled) {
  background: #f8f9fa;
}

.pure-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style> 