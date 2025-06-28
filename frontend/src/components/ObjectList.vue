<template>
  <div class="section section-feature-list">
    <h3>
      <span>Файли ({{ files.length }})</span>
    </h3>
    <div class="disclosure-wrap disclosure-wrap-feature_list">
      <div class="feature-list">
        <FileCard 
          v-for="file in files" 
          :key="file.id"
          :file="file"
          :type="getFileType(file)"
          :name="file.name"
          :selected="selectedFile && selectedFile.id === file.id"
          @click="selectFile(file)"
          @file-selected="handleFileSelected"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import FileCard from './FileCard.vue'

const props = defineProps({
  files: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['file-selected'])

const selectedFile = ref(null)

function getFileType(file) {
  const tags = file.tags || {}
  if (tags.type === 'raster') return 'raster'
  if (tags.type === 'vector') return 'vector'
  if (tags.type === 'text') return 'text'
  return 'binary'
}

function selectFile(file) {
  selectedFile.value = file
  emit('file-selected', file)
}

function handleFileSelected(file) {
  emit('file-selected', file)
}

// Watch for external file selection changes
watch(() => props.files, (newFiles) => {
  // Reset selection if the selected file is no longer in the list
  if (selectedFile.value && !newFiles.find(f => f.id === selectedFile.value.id)) {
    selectedFile.value = null
  }
}, { deep: true })
</script>

<style scoped>
.section-feature-list {
  padding: 1rem;
  background: #f8f9fa;
}
.feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-start;
}
</style> 