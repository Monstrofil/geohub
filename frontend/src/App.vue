<template>
  <div class="pure-g app-grid">
    <!-- File List View -->
    <div v-if="!selectedFile" class="pure-u-1">
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
              :selected="false"
              @click="selectFile(file)"
              @file-selected="handleFileSelected"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- File Editor View -->
    <div v-else class="pure-u-1">
      <FileEditor 
        :file="selectedFile"
        @back="backToList"
        @file-uploaded="handleFileUploaded"
        @tags-updated="handleTagsUpdated"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import FileCard from './components/FileCard.vue'
import FileEditor from './components/FileEditor.vue'
import { loadFieldDefinitions } from './utils/fieldResolver.js'

const selectedFile = ref(null)
const allFieldDefinitions = ref({})

// Central files array management
const files = ref([
  { id: 1, name: 'photo.jpg', tags: {"type": "raster", "name": "photo.jpg"} },
  { id: 2, name: 'map.svg', tags: {"type": "vector", "name": "map.svg"} },
  { id: 3, name: 'checkpoint.jpg', tags: {"military": "checkpoint", "name": "checkpoint.jpg"} },
  { id: 4, name: 'trench.jpg', tags: {"military": "trench", "name": "trench.jpg"} },
  { id: 5, name: 'unknown.bin', tags: {"name": "unknown.bin"} },
  { id: 6, name: 'highway.jpg', tags: {"highway": "motorway", "name": "highway.jpg", "ref_road_number": "M1", "maxspeed": "120"} }
])

onMounted(async () => {
  // Load all field definitions
  allFieldDefinitions.value = await loadFieldDefinitions()
})

function getFileType(file) {
  const tags = file.tags || {}
  if (tags.type === 'raster') return 'raster'
  if (tags.type === 'vector') return 'vector'
  if (tags.type === 'text') return 'text'
  return 'binary'
}

function selectFile(file) {
  selectedFile.value = file
}

function handleFileSelected(file) {
  selectedFile.value = file
}

function backToList() {
  selectedFile.value = null
}

function handleFileUploaded(uploadData) {
  // Here you would typically handle the file upload
  // For now, we'll just log the upload data
  console.log('File uploaded:', uploadData)
  
  // You could update the file in the files array here
  // const fileIndex = files.value.findIndex(f => f.id === uploadData.originalFile.id)
  // if (fileIndex !== -1) {
  //   files.value[fileIndex] = { ...uploadData.originalFile, uploadedFile: uploadData.file }
  // }
}

function handleTagsUpdated(newTags) {
  if (selectedFile.value) {
    // Update the file's tags in the files array
    const fileIndex = files.value.findIndex(f => f.id === selectedFile.value.id)
    if (fileIndex !== -1) {
      files.value[fileIndex].tags = { ...newTags }
      // Update the selectedFile reference to reflect changes
      selectedFile.value = files.value[fileIndex]
    }
  }
}
</script>

<style scoped>
.app-grid {
  min-height: 100vh;
  background: #fafbfc;
}

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