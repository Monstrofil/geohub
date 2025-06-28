<template>
  <div class="geotiff-preview">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading map preview...</p>
    </div>
    
    <div v-else-if="error" class="error">
      <p>{{ error }}</p>
    </div>
    
    <div v-else-if="previewUrl" class="map-container">
      <div class="map-controls">
        <button @click="refreshMap" class="refresh-btn">
          <svg width="16" height="16" viewBox="0 0 24 24">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" fill="currentColor"/>
          </svg>
          Refresh
        </button>
        <button @click="openFullMap" class="full-map-btn">
          <svg width="16" height="16" viewBox="0 0 24 24">
            <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" fill="currentColor"/>
          </svg>
          Full Map
        </button>
      </div>
      
      <div class="map-frame">
        <iframe 
          :src="previewUrl" 
          frameborder="0" 
          width="100%" 
          height="400"
          @load="onMapLoad"
          @error="onMapError"
        ></iframe>
      </div>
      
      <div class="map-info">
        <p><strong>File:</strong> {{ filename }}</p>
        <p><strong>Type:</strong> GeoTIFF</p>
        <p><strong>Preview URL:</strong> <a :href="previewUrl" target="_blank">{{ previewUrl }}</a></p>
      </div>
    </div>
    
    <div v-else class="no-preview">
      <p>No preview available for this file type.</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import apiService from '../services/api.js'

export default {
  name: 'GeoTiffPreview',
  props: {
    fileId: {
      type: Number,
      required: true
    },
    filename: {
      type: String,
      required: true
    }
  },
  
  setup(props) {
    const loading = ref(false)
    const error = ref(null)
    const previewUrl = ref(null)
    
    const loadPreview = async () => {
      if (!props.fileId) return
      
      loading.value = true
      error.value = null
      
      try {
        const response = await apiService.request(`/files/${props.fileId}/preview`)
        previewUrl.value = response.preview_url
      } catch (err) {
        console.error('Failed to load preview:', err)
        error.value = err.message || 'Failed to load map preview'
      } finally {
        loading.value = false
      }
    }
    
    const refreshMap = () => {
      loadPreview()
    }
    
    const openFullMap = () => {
      if (previewUrl.value) {
        window.open(previewUrl.value, '_blank')
      }
    }
    
    const onMapLoad = () => {
      console.log('Map loaded successfully')
    }
    
    const onMapError = () => {
      error.value = 'Failed to load map in iframe'
    }
    
    onMounted(() => {
      loadPreview()
    })
    
    watch(() => props.fileId, () => {
      loadPreview()
    })
    
    return {
      loading,
      error,
      previewUrl,
      refreshMap,
      openFullMap,
      onMapLoad,
      onMapError
    }
  }
}
</script>

<style scoped>
.geotiff-preview {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #666;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error {
  padding: 20px;
  color: #d32f2f;
  text-align: center;
  background: #ffebee;
}

.map-container {
  display: flex;
  flex-direction: column;
}

.map-controls {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.refresh-btn,
.full-map-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.refresh-btn:hover,
.full-map-btn:hover {
  background: #f0f0f0;
  border-color: #bbb;
}

.map-frame {
  position: relative;
  background: #f9f9f9;
}

.map-frame iframe {
  display: block;
  border: none;
}

.map-info {
  padding: 12px;
  background: #f9f9f9;
  border-top: 1px solid #e0e0e0;
  font-size: 12px;
  color: #666;
}

.map-info p {
  margin: 4px 0;
}

.map-info a {
  color: #2196f3;
  text-decoration: none;
  word-break: break-all;
}

.map-info a:hover {
  text-decoration: underline;
}

.no-preview {
  padding: 40px;
  text-align: center;
  color: #666;
  background: #f9f9f9;
}
</style> 