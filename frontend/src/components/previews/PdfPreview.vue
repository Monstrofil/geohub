<template>
  <div class="pdf-preview">
    <div class="pdf-container">
      <div class="pdf-toolbar">
        <div class="pdf-actions">
          <button @click="downloadPdf" class="download-btn">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M14 10v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="8,14 8,4 8,4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="4" y1="8" x2="8" y2="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="4" x2="8" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Download
          </button>
        </div>
      </div>
      
      <div class="pdf-viewer">
        <embed 
          :src="pdfUrl" 
          type="application/pdf" 
          class="pdf-embed"
          @load="onLoad"
          @error="onError"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import apiService from '../../services/api.js'

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

const downloadUrl = computed(() => {
  return `${apiService.baseUrl}/files/${props.fileId}/download`
})

// Methods
function onLoad() {
  emit('loaded')
}

function onError() {
  const errorMsg = 'Failed to load PDF'
  emit('error', errorMsg)
}

function downloadPdf() {
  const link = document.createElement('a')
  link.href = downloadUrl.value
  link.download = props.file?.name || 'document.pdf'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
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
