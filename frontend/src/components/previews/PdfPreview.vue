<template>
  <div class="pdf-preview">
    <div class="pdf-container">
      <div class="pdf-viewer">
        <vue-pdf-app class="pdf-embed" :pdf="pdfUrl"></vue-pdf-app>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import apiService from '../../services/api.js'

import VuePdfApp from "vue3-pdf-app";
// import this to use default icons for buttons
import "vue3-pdf-app/dist/icons/main.css";

const props = defineProps({
  fileId: {
    type: String,
    required: true
  },
  file: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['error', 'loaded'])

// Computed
const pdfUrl = computed(() => {
  return `${apiService.baseUrl}/files/${props.fileId}/download`
})

</script>

<style scoped>
.pdf-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

.pdf-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.pdf-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.pdf-actions {
  display: flex;
  gap: 0.5rem;
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: #28a745;
  color: white;
  border: none;
  padding: 0.375rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.download-btn:hover {
  background: #218838;
}

.pdf-viewer {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.pdf-embed {
  width: 100%;
  height: 1200px;
  border: none;
}
</style>
