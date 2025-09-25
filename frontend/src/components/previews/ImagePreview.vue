<template>
  <div class="image-preview">

    <div v-if="imageUrl" class="image-container">
      
      <div class="image-viewer">
        <viewer :images="[imageUrl]" :options="options">
            <img :src="imageUrl" >
        </viewer>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import apiService from '../../services/api.js'

const options = computed(() => {
  return {
   "inline": true, 
   
   "button": false, 
   "navbar": true, 
   "title": false, 
   "toolbar": false, 
   "tooltip": false, 
   "movable": true, 
   "zoomable": true,
   "rotatable": false, 
   "scalable": true, 
   "transition": false, 
   "fullscreen": true, 
   "keyboard": false
  }
});

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

const imageUrl = computed(() => {
  return `${apiService.baseUrl}/files/${props.fileId}/download`
})

</script>

<style scoped>
.image-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

.loading, .error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  height: 100%;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  margin-bottom: 1rem;
}

.error h3 {
  color: #dc3545;
  margin-bottom: 0.5rem;
}

.error p {
  color: #6c757d;
  margin-bottom: 1rem;
}

.retry-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #0056b3;
}

.image-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.image-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.image-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: #fff;
  border: 1px solid #dee2e6;
  padding: 0.375rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.control-btn:hover {
  background: #e9ecef;
}

.zoom-info {
  font-weight: 500;
  color: #495057;
  margin-left: 0.5rem;
}

.image-actions {
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

.image-viewer {
  flex: 1;
  overflow: hidden;
  position: relative;
  cursor: grab;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-viewer:active {
  cursor: grabbing;
}

.image-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.preview-image {
  user-select: none;
  -webkit-user-drag: none;
  -khtml-user-drag: none;
  -moz-user-drag: none;
  -o-user-drag: none;
  user-drag: none;
}

.image-info {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border-top: 1px solid #dee2e6;
  font-size: 0.875rem;
  color: #6c757d;
}

.image-dimensions {
  font-weight: 500;
}

.image-size {
  color: #6c757d;
}

.image-format {
  font-weight: 500;
  color: #007bff;
}
</style>

