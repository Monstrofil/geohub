<template>
  <div class="file-info-section">
    <h3>{{ $t('fileInfo.title') }}</h3>
    <div class="info-grid">
      <div class="info-item">
        <span class="info-label">{{ $t('fileInfo.name') }}</span>
        <span class="info-value">{{ getOriginalName(file) }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">{{ $t('fileInfo.type') }}</span>
        <span class="info-value">{{ fileTypeLabel }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">{{ $t('fileInfo.mimeType') }}</span>
        <span class="info-value">{{ getMimeType(file) || $t('fileInfo.unknown') }}</span>
      </div>
      <div class="info-item" v-if="getFileSize(file)">
        <span class="info-label">{{ $t('fileInfo.size') }}</span>
        <span class="info-value">{{ formatSize(getFileSize(file)) }}</span>
      </div>
      <div class="info-item" v-if="file.created_at">
        <span class="info-label">{{ $t('fileInfo.created') }}</span>
        <span class="info-value">{{ formatDate(file.created_at) }}</span>
      </div>
      <div class="info-item" v-if="file.updated_at">
        <span class="info-label">{{ $t('fileInfo.modified') }}</span>
        <span class="info-value">{{ formatDate(file.updated_at) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getFileSize, getBaseFileType, getMimeType, getOriginalName, formatFileSize as formatSize } from '../../../utils/fileHelpers.js'

const props = defineProps({
  file: {
    type: Object,
    required: true
  }
})

// File type detection and labels
const fileType = computed(() => {
  // Check if this is a collection first
  if (props.file?.object_type === 'tree') {
    return 'collection'
  }
  return getBaseFileType(props.file)
})

const fileTypeLabel = computed(() => {
  const labels = {
    'raster': 'Georeferenced Raster Image',
    'vector': 'Georeferenced Vector File', 
    'raw': 'Regular File',
    'collection': 'File Collection',
  }
  return labels[fileType.value] || 'Unknown Type'
})

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}
</script>

<style scoped>
.file-info-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.file-info-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.info-label {
  font-size: 0.9rem;
  color: #495057;
  font-weight: 500;
  min-width: 80px;
}

.info-value {
  font-size: 0.9rem;
  color: #212529;
  text-align: right;
  word-break: break-word;
  max-width: 200px;
}
</style>
