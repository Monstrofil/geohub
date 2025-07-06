<template>
  <div class="file-viewer">
    <div class="viewer-header">
      <div class="header-content">
        <div class="file-info">
          <div class="file-icon" v-html="fileIcon"></div>
          <div class="file-details">
            <h1 class="file-name">{{ getDisplayName() }}</h1>
            <div class="file-meta">
              <span class="file-type">{{ fileTypeLabel }}</span>
              <span class="file-size" v-if="file?.file_size">{{ formatFileSize(file.file_size) }}</span>
              <span class="file-date" v-if="file?.created_at">{{ formatDate(file.created_at) }}</span>
              <span class="file-id" v-if="file?.id">ID: {{ file.id }}</span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <router-link :to="{name: 'FileEditor', query: { treePath: $route.query.treePath }}" class="edit-btn">
            <i class="fas fa-edit"></i>
            Edit
          </router-link>
          <button @click="goBack" class="back-btn">
            <i class="fas fa-arrow-left"></i>
            Back
          </button>
        </div>
      </div>
    </div>

    <div class="viewer-content">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading file...</p>
      </div>
      
      <div v-else-if="error" class="error">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading File</h3>
        <p>{{ error }}</p>
        <button @click="loadFile" class="retry-btn">Try Again</button>
      </div>
      
      <div v-else-if="!file" class="not-found">
        <i class="fas fa-file-excel"></i>
        <h3>File Not Found</h3>
        <p>The requested file could not be found.</p>
        <button @click="goBack" class="back-btn">Go Back</button>
      </div>
      
      <div v-else class="file-content">
        <div class="content-layout">
          <!-- Left panel: Main content -->
          <div class="content-main">
            <!-- Collection viewer -->
            <div v-if="file.object_type === 'tree'" class="collection-viewer">
              <div class="collection-info">
                <h3>Collection: {{ file.name || 'Untitled Collection' }}</h3>
                <p class="collection-description">
                  This is a collection containing {{ file.entries?.length || 0 }} items.
                </p>
                <div class="collection-stats">
                  <div class="stat-item">
                    <span class="stat-label">Items:</span>
                    <span class="stat-value">{{ file.entries?.length || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">Created:</span>
                    <span class="stat-value">{{ formatDate(file.created_at) }}</span>
                  </div>
                </div>
              </div>
              
              <div class="collection-content">
                <p>This is a collection of files. You can view the contents below.</p>
                
                <!-- Collection files list -->
                <CollectionFilesList 
                  :ref-name="props.refName"
                  :collection-path="props.treePath"
                  @files-updated="handleCollectionFilesUpdated"
                  ref="collectionFilesList"
                />
              </div>
            </div>
            
            <!-- File viewer -->
            <div v-else class="file-viewer">
              <!-- Interactive Map for GeoTIFF files -->
              <InteractiveMap 
                v-if="isGeoTiff && file"
                :fileId="file.id"
                :filename="file.name"
                class="interactive-map-container"
              />
              
              <!-- Vector file content -->
              <div v-else-if="file.base_file_type === 'vector'" class="vector-content">
                <h3>Vector File</h3>
                <p>This is a vector file ({{ file.mime_type }}).</p>
                <div class="preview-placeholder">
                  <i class="fas fa-draw-polygon"></i>
                  <p>Vector preview would be displayed here</p>
                </div>
              </div>
              
              <!-- Generic file content -->
              <div v-else class="generic-content">
                <h3>File Content</h3>
                <p>File type: {{ file.mime_type }}</p>
                <div class="preview-placeholder">
                  <i class="fas fa-file"></i>
                  <p>File preview would be displayed here</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Right panel: Object Information -->
          <div class="content-sidebar">
            <!-- Unified Object Type and Properties section -->
            <div v-if="selectedType || (file.tags && Object.keys(file.tags).length > 0)" class="unified-properties-section">
              <h3>Object Information</h3>
              
              <!-- Object type display -->
              <div v-if="selectedType" class="object-type-display">
                <div class="preset-icon-container">
                  <span v-html="selectedType.icon" class="preset-icon"></span>
                </div>
                <div class="object-type-info">
                  <div class="object-type-name">{{ selectedType.name }}</div>
                  <div class="object-type-description">
                    Matched based on file tags and properties
                  </div>
                </div>
              </div>

              <!-- Object properties using field definitions -->
              <div v-if="file.tags && Object.keys(file.tags).length > 0" class="properties-section">
                <h4>Properties</h4>
                <div v-if="selectedFields.length > 0" class="properties-grid">
                  <div v-for="field in selectedFields" :key="field.key" class="property-item">
                    <span class="property-label">{{ field.label || field.key }}:</span>
                    <span class="property-value">{{ file.tags[field.key] || 'Not set' }}</span>
                  </div>
                </div>
                <div v-else class="tags-grid">
                  <div v-for="(value, key) in file.tags" :key="key" class="tag-item">
                    <span class="tag-key">{{ key }}:</span>
                    <span class="tag-value">{{ value }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- File Information section -->
            <div class="file-info-section">
              <h3>File Information</h3>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Name:</span>
                  <span class="info-value">{{ file.original_name || file.name }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Type:</span>
                  <span class="info-value">{{ fileTypeLabel }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">MIME Type:</span>
                  <span class="info-value">{{ file.mime_type || 'Unknown' }}</span>
                </div>
                <div class="info-item" v-if="file.file_size">
                  <span class="info-label">Size:</span>
                  <span class="info-value">{{ formatFileSize(file.file_size) }}</span>
                </div>
                <div class="info-item" v-if="file.created_at">
                  <span class="info-label">Created:</span>
                  <span class="info-value">{{ formatDate(file.created_at) }}</span>
                </div>
                <div class="info-item" v-if="file.updated_at">
                  <span class="info-label">Modified:</span>
                  <span class="info-value">{{ formatDate(file.updated_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InteractiveMap from './InteractiveMap.vue'
import CollectionFilesList from './CollectionFilesList.vue'
import { matchTagsToPreset } from '../utils/tagMatcher.js'
import { loadFieldDefinitions, resolveFields } from '../utils/fieldResolver.js'
import apiService from '../services/api.js'

const route = useRoute()
const router = useRouter()

// State
const file = ref(null)
const loading = ref(false)
const error = ref(null)

// Field definitions and presets (reused from FileEditor)
const allPresets = ref([])
const allFieldDefinitions = ref({})
const selectedType = ref(null)

const props = defineProps({
  refName: {
    type: String,
    required: true
  },
  treePath: {
    type: [String, Number, Array],
    required: true
  }
})


// Computed
const fileIcon = computed(() => {
  switch (fileType.value) {
    case 'raster':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="2" y="6" width="36" height="28" rx="4" fill="#e0e7ef" stroke="#7faaff" stroke-width="2"/>
        <circle cx="14" cy="24" r="4" fill="#7faaff"/>
        <rect x="20" y="16" width="12" height="8" fill="#b3d1ff"/>
        <path d="M6 6l4 4M10 6l4 4M14 6l4 4" stroke="#7faaff" stroke-width="1" fill="none"/>
      </svg>`
    case 'vector':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="2" y="6" width="36" height="28" rx="4" fill="#e0f7e7" stroke="#2ecc71" stroke-width="2"/>
        <circle cx="12" cy="28" r="3" fill="#2ecc71"/>
        <circle cx="28" cy="14" r="3" fill="#2ecc71"/>
        <line x1="12" y1="28" x2="28" y2="14" stroke="#27ae60" stroke-width="2"/>
        <path d="M6 6l4 4M10 6l4 4M14 6l4 4" stroke="#2ecc71" stroke-width="1" fill="none"/>
      </svg>`
    case 'raw':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="4" y="6" width="32" height="28" rx="4" fill="#f7f7e7" stroke="#6c757d" stroke-width="2"/>
        <rect x="12" y="16" width="16" height="2" fill="#6c757d"/>
        <rect x="12" y="22" width="10" height="2" fill="#6c757d"/>
        <rect x="12" y="28" width="14" height="2" fill="#6c757d"/>
      </svg>`
    case 'collection':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="3" y="8" width="34" height="24" rx="4" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
        <path d="M3 8l4-6h12l4 6" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
        <rect x="8" y="14" width="4" height="2" fill="#ffb300"/>
        <rect x="14" y="14" width="4" height="2" fill="#ffb300"/>
        <rect x="20" y="14" width="4" height="2" fill="#ffb300"/>
        <rect x="8" y="18" width="4" height="2" fill="#ffb300"/>
        <rect x="14" y="18" width="4" height="2" fill="#ffb300"/>
        <rect x="20" y="18" width="4" height="2" fill="#ffb300"/>
      </svg>`
    default:
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="6" y="6" width="28" height="28" rx="6" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
        <path d="M12 12h16M12 16h12M12 20h8" stroke="#6c757d" stroke-width="2" fill="none"/>
      </svg>`
  }
})

// Methods
// Dynamically import all presets (reused from FileEditor)
const presetModules = import.meta.glob('../data/presets/*/*.json', { eager: true })

async function loadFile() {
  if (!props.treePath) {
    error.value = 'No file path provided'
    return
  }

  loading.value = true
  error.value = null
  
  try {
    const response = await apiService.getTreeEntry(props.refName, props.treePath)
    if (!response || !response.object) {
      throw new Error('File not found')
    }
    
    file.value = response.object
    // Store the object type for UI rendering
    file.value.object_type = response.object_type

    // Set initial type based on file tags (reused from FileEditor)
    if (file.value && file.value.tags) {
      const matchedPreset = matchTagsToPreset(file.value.tags, allPresets.value)
      selectedType.value = matchedPreset
    }
  } catch (err) {
    console.error('Failed to load file:', err)
    error.value = err.message || 'Failed to load file'
    file.value = null
  } finally {
    loading.value = false
  }
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}

function goBack() {
  router.back()
}

function getDisplayName() {
  if (!file.value) return 'Untitled'
  
  if (file.value.object_type === 'tree') {
    return file.value.tags?.name || file.value.name || 'Untitled Collection'
  } else {
    return file.value.tags?.name || file.value.original_name || file.value.name || 'Untitled File'
  }
}



// File type detection and labels (reused from FileEditor)
const fileType = computed(() => {
  // Check if this is a collection first
  if (file.value?.object_type === 'tree') {
    return 'collection'
  }
  return file.value?.base_file_type || 'raw'
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

// Check if file is a GeoTIFF (raster type)
const isGeoTiff = computed(() => {
  return fileType.value === 'raster'
})

// Handle collection files updates
function handleCollectionFilesUpdated(files) {
  // Update the collection entries count if needed
  if (file.value && file.value.object_type === 'tree') {
    file.value.entries = files
  }
}

// Resolve field keys to full field definitions (reused from FileEditor)
const selectedFields = computed(() => {
  if (!selectedType.value || !selectedType.value.fields) {
    return []
  }
  return resolveFields(selectedType.value.fields, allFieldDefinitions.value)
})

// Lifecycle
onMounted(async () => {
  // Load all field definitions and presets (reused from FileEditor)
  allPresets.value = Object.values(presetModules).map(module => module.default || module)
  console.log('Loaded presets:', allPresets.value)
  allFieldDefinitions.value = await loadFieldDefinitions()
  await loadFile()
})

// Watch for prop changes
watch(() => [props.refName, props.treePath], () => {
  loadFile()
})
</script>

<style scoped>
.file-viewer {
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  overflow: hidden;
}

.viewer-header {
  background: white;
  border-bottom: 1px solid #eee;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  flex-shrink: 0;
}

.file-details {
  min-width: 0;
}

.file-name {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  word-break: break-word;
}

.file-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #666;
}

.file-type {
  text-transform: uppercase;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.edit-btn, .back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s;
}

.edit-btn {
  background: #007bff;
  color: white;
  border: none;
}

.edit-btn:hover {
  background: #0056b3;
}

.back-btn {
  background: none;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.back-btn:hover {
  background: #6c757d;
  color: white;
}

.viewer-content {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
}

.content-layout {
  display: flex;
  gap: 2rem;
}

.content-main {
  flex: 1;
  min-width: 0;
}

.content-sidebar {
  width: 350px;
  flex-shrink: 0;
}

.loading, .error, .not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error i, .not-found i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #dc3545;
}

.not-found i {
  color: #6c757d;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #0056b3;
}

.file-content {
  width: 100%;
}

.raster-viewer, .vector-viewer, .generic-viewer {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: #f8f9fa;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  margin-top: 1rem;
  color: #6c757d;
}

.preview-placeholder i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.file-tags {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.tag-item {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.tag-key {
  font-weight: 500;
  color: #495057;
  min-width: 80px;
}

.tag-value {
  color: #333;
  word-break: break-word;
}

/* Collection viewer styles */
.collection-viewer {
  width: 100%;
}

.collection-info {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.collection-description {
  color: #666;
  margin-bottom: 1.5rem;
}

.collection-stats {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.collection-actions {
  text-align: center;
}

.view-collection-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background-color 0.15s;
}

.view-collection-btn:hover {
  background: #0056b3;
}

/* File viewer styles */
.file-viewer {
  width: 100%;
}

/* File info section in sidebar */
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

/* Content sections */
.raster-content,
.vector-content,
.generic-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Unified properties section */
.unified-properties-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  top: 1rem;
}

.unified-properties-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
}

.object-type-display {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.preset-icon-container {
  flex-shrink: 0;
}

.preset-icon {
  display: block;
  width: 32px;
  height: 32px;
}

.object-type-info {
  flex: 1;
}

.object-type-name {
  font-weight: 600;
  font-size: 1.1rem;
  color: #212529;
  margin-bottom: 0.25rem;
}

.object-type-description {
  font-size: 0.9rem;
  color: #6c757d;
}

.properties-section {
  margin-top: 1.5rem;
}

.properties-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.properties-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.property-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.property-label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.property-value {
  color: #666;
  word-break: break-word;
  font-size: 1rem;
}

/* Fallback for raw tags */
.object-tags {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Interactive map container */
.interactive-map-container {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  min-height: 400px;
  height: 80vh;
}

/* Collection content */
.collection-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.collection-content p {
  color: #666;
  margin-bottom: 1.5rem;
}
</style> 