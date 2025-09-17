<template>
  <div class="file-viewer">
    <!-- Header with back button -->
    <div class="viewer-header">
      <button class="back-btn" @click="goBack">
        <svg width="16" height="16" viewBox="0 0 16 16">
          <path d="M10 2L4 8L10 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Назад до списку
      </button>
      <div class="header-actions">
        <router-link v-if="isAuthenticated" :to="{name: 'FileEditor', query: { id: props.treeItemId }}" class="edit-btn">
          <svg width="16" height="16" viewBox="0 0 16 16">
            <path d="M11 1L15 5L5 15H1V11L11 1Z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 4L12 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Редагувати
        </router-link>
        <router-link v-else :to="loginUrl" class="login-btn">
          <svg width="16" height="16" viewBox="0 0 16 16">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="16,17 21,12 16,7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Увійти щоб редагувати
        </router-link>
      </div>
    </div>

    <!-- File info section moved below header -->
    <div class="file-info-header" v-if="file">
      <div class="file-info">
        <div class="file-icon" v-html="fileIcon"></div>
        <div class="file-details">
          <h1 class="file-name">{{ getDisplayName() }}</h1>
          <div class="file-meta">
            <span class="file-type">{{ fileTypeLabel }}</span>
            <span class="file-size" v-if="getFileSize(file)">{{ formatFileSize(getFileSize(file)) }}</span>
            <span class="file-date" v-if="file?.created_at">{{ formatDate(file.created_at) }}</span>
            <span class="file-id" v-if="file?.id">ID: {{ file.id }}</span>
          </div>
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
                  :collection-id="props.treeItemId"
                  @files-updated="handleCollectionFilesUpdated"
                  ref="collectionFilesList"
                />
              </div>
            </div>
            
            <!-- File viewer -->
            <div v-else class="file-viewer">
              <!-- Layer controls filter block - for GeoTIFF files -->
              <div v-if="isGeoTiff && file && isFileGeoreferenced" class="layer-filter-block">
                <div class="filter-header" @click="toggleLayerPanel">
                  <div class="filter-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" class="filter-icon">
                      <path d="M12 16l-6-6h12l-6 6z" fill="currentColor"/>
                      <path d="M12 10l-6-6h12l-6 6z" fill="currentColor" opacity="0.6"/>
                      <path d="M12 4l-6-6h12l-6 6z" fill="currentColor" opacity="0.3"/>
                    </svg>
                    <span>Map Layers</span>
                  </div>
                  <button class="filter-toggle" :class="{ 'expanded': layerPanelOpen }">
                    <svg width="16" height="16" viewBox="0 0 24 24">
                      <path d="M6 9l6 6 6-6" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
                
                <div v-show="layerPanelOpen" class="filter-content">
                  <div class="layer-controls-grid">
                    <!-- Base Map Layer -->
                    <div class="layer-filter-item">
                      <label class="layer-filter-label">
                        <input 
                          type="checkbox" 
                          v-model="layers.baseMap.visible"
                          @change="toggleLayer('osm-tiles', layers.baseMap.visible)"
                          class="layer-filter-checkbox"
                        />
                        <span class="layer-filter-name">Base Map</span>
                      </label>
                      <div class="layer-description">OpenStreetMap background tiles</div>
                      
                      <!-- Opacity slider for Base Map layer -->
                      <div class="layer-opacity-section">
                        <label class="opacity-section-label">Opacity: {{ Math.round(layers.baseMap.opacity * 100) }}%</label>
                        <input 
                          type="range" 
                          min="0" 
                          max="1" 
                          step="0.1"
                          v-model="layers.baseMap.opacity"
                          @input="updateLayerOpacity('osm-tiles', layers.baseMap.opacity)"
                          class="layer-filter-opacity-slider"
                          :disabled="!layers.baseMap.visible"
                        />
                      </div>
                    </div>
                    
                    <!-- GeoTIFF Layer -->
                    <div class="layer-filter-item">
                      <label class="layer-filter-label">
                        <input 
                          type="checkbox" 
                          v-model="layers.geotiff.visible"
                          @change="toggleLayer('geotiff-layer', layers.geotiff.visible)"
                          class="layer-filter-checkbox"
                        />
                        <span class="layer-filter-name">{{ file.name || 'Georeferenced File' }}</span>
                      </label>
                      <div class="layer-description">Uploaded georeferenced overlay</div>
                      
                      <!-- Opacity slider for GeoTIFF layer -->
                      <div class="layer-opacity-section">
                        <label class="opacity-section-label">Opacity: {{ Math.round(layers.geotiff.opacity * 100) }}%</label>
                        <input 
                          type="range" 
                          min="0" 
                          max="1" 
                          step="0.1"
                          v-model="layers.geotiff.opacity"
                          @input="updateLayerOpacity('geotiff-layer', layers.geotiff.opacity)"
                          class="layer-filter-opacity-slider"
                          :disabled="!layers.geotiff.visible"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Interactive Map for GeoTIFF files -->
              <InteractiveMap 
                v-if="isGeoTiff && file && isFileGeoreferenced"
                :fileId="file.id"
                :filename="file.name"
                class="interactive-map-container"
                ref="interactiveMapRef"
              />
              
              <!-- Georeferencing needed for raster files -->
              <div v-else-if="file && !isFileGeoreferenced" class="georeferencing-needed">
                
                <!-- Probing status -->
                <div v-if="probeLoading" class="probe-status">
                  <div class="spinner"></div>
                  <h3>Checking file compatibility...</h3>
                  <p>Analyzing if this file can be georeferenced...</p>
                </div>

                <!-- Probe error -->
                <div v-else-if="probeError" class="probe-error">
                  <div class="georef-icon">
                    <svg width="64" height="64" viewBox="0 0 64 64">
                      <circle cx="32" cy="32" r="30" fill="#dc3545"/>
                      <path d="M20 20l24 24M44 20l-24 24" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <h3>File Analysis Failed</h3>
                  <p>{{ probeError }}</p>
                </div>

                <!-- File cannot be georeferenced -->
                <div v-else-if="probeResult && !probeResult.can_georeference" class="cannot-georeference">
                  <div class="georef-icon">
                    <svg width="64" height="64" viewBox="0 0 64 64">
                      <circle cx="32" cy="32" r="30" fill="#6c757d"/>
                      <path d="M20 20l24 24M44 20l-24 24" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <h3>Cannot Be Georeferenced</h3>
                  <p>{{ probeResult.error || 'This file is not compatible with georeferencing tools.' }}</p>
                </div>

                <!-- Regular file that can be converted and georeferenced -->
                <div v-else-if="file.object_type === 'raw_file' && probeResult && probeResult.can_georeference && !probeResult.is_already_georeferenced" class="can-georeference">
                  <div class="georef-icon">
                    <svg width="64" height="64" viewBox="0 0 64 64">
                      <circle cx="32" cy="32" r="30" fill="#28a745"/>
                      <path d="M20 32l8 8 16-16" stroke="white" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <h3>Ready for Georeferencing</h3>
                  <p>This file can be prepared for georeferencing. We'll convert it to a geo-raster format and then open the georeferencing interface where you can add control points.</p>
                  
                  <div class="georef-actions">
                    <button class="btn btn-success convert-btn" @click="convertToGeoRaster" :disabled="isConverting">
                      <div v-if="isConverting" class="spinner"></div>
                      <svg v-else width="24" height="24" viewBox="0 0 24 24">
                        <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      {{ isConverting ? 'Converting...' : 'Convert & Start Georeferencing' }}
                    </button>
                  </div>
                  
                  <div class="file-info">
                    <p><strong>File details:</strong> {{ probeResult.image_info?.width }}×{{ probeResult.image_info?.height }} pixels, {{ probeResult.image_info?.bands }} bands</p>
                  </div>
                </div>

                <!-- Geo-raster file that needs georeferencing (no conversion needed) -->
                <div v-else-if="file.object_type === 'geo_raster_file' && probeResult && probeResult.can_georeference && !probeResult.is_already_georeferenced" class="needs-georeferencing">
                  <div class="georef-icon">
                    <svg width="64" height="64" viewBox="0 0 64 64">
                      <circle cx="32" cy="32" r="30" fill="#ffc107"/>
                      <path d="M32 16v16M32 40h0" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <h3>Georeferencing Required</h3>
                  <p>This geo-raster file is ready for georeferencing. Add control points to georeference it to a map coordinate system.</p>
                  
                  <div class="georef-actions">
                    <button class="btn btn-primary georef-btn" @click="startGeoreferencing">
                      <svg width="24" height="24" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                        <circle cx="12" cy="12" r="2" fill="currentColor"/>
                        <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      Start Georeferencing
                    </button>
                  </div>
                  
                  <div class="file-info">
                    <p><strong>File details:</strong> {{ probeResult.image_info?.width }}×{{ probeResult.image_info?.height }} pixels, {{ probeResult.image_info?.bands }} bands</p>
                  </div>
                </div>

                <!-- File is already georeferenced (fallback case) -->
                <div v-else-if="probeResult && probeResult.is_already_georeferenced" class="already-georeferenced">
                  <div class="georef-icon">
                    <svg width="64" height="64" viewBox="0 0 64 64">
                      <circle cx="32" cy="32" r="30" fill="#17a2b8"/>
                      <path d="M20 32l8 8 16-16" stroke="white" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <h3>Already Georeferenced</h3>
                  <p>This file already has georeferencing information. It should be displayed on the map.</p>
                </div>

                <!-- Default georeferencing option (no probe result yet) -->
                <div v-else class="default-georeferencing">
                  <div class="georef-header">
                    <div class="georef-icon">
                      <svg width="64" height="64" viewBox="0 0 64 64">
                        <circle cx="32" cy="32" r="30" fill="#ffc107"/>
                        <path d="M32 16v16M32 40h0" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
                      </svg>
                    </div>
                    <h3>Georeferencing Required</h3>
                    <p>This raster file needs georeferencing to be displayed on a map. Add control points to georeference it.</p>
                  </div>
                  
                  <div class="georef-actions">
                    <button class="btn btn-primary georef-btn" @click="startGeoreferencing">
                      <svg width="24" height="24" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                        <circle cx="12" cy="12" r="2" fill="currentColor"/>
                        <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      Start Georeferencing
                    </button>
                  </div>
                </div>
                
                <div v-if="georeferencingStatus" class="georef-status">
                  <div v-if="georeferencingStatus.loading" class="status-loading">
                    <div class="spinner"></div>
                    <span>Loading georeferencing interface...</span>
                  </div>
                  <div v-else-if="georeferencingStatus.error" class="status-error">
                    <span>Error: {{ georeferencingStatus.error }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Vector file content -->
              <div v-else-if="getBaseFileType(file) === 'vector'" class="vector-content">
                <h3>Vector File</h3>
                <p>This is a vector file ({{ getMimeType(file) }}).</p>
                <div class="preview-placeholder">
                  <i class="fas fa-draw-polygon"></i>
                  <p>Vector preview would be displayed here</p>
                </div>
              </div>
              
              <!-- Generic file content -->
              <div v-else class="generic-content">
                <h3>File Content</h3>
                <p>File type: {{ getMimeType(file) }}</p>
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
                  <span class="info-value">{{ getOriginalName(file) }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Type:</span>
                  <span class="info-value">{{ fileTypeLabel }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">MIME Type:</span>
                  <span class="info-value">{{ getMimeType(file) || 'Unknown' }}</span>
                </div>
                <div class="info-item" v-if="getFileSize(file)">
                  <span class="info-label">Size:</span>
                  <span class="info-value">{{ formatSize(getFileSize(file)) }}</span>
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
    
    <!-- Georeferencing Modal -->
    <GeoreferencingModal 
      v-if="showGeoreferencingModal && file"
      :file-id="file.id"
      :file-info="file.tags"
      @close="closeGeoreferencing"
      @completed="onGeoreferencingCompleted" 
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InteractiveMap from './InteractiveMap.vue'
import CollectionFilesList from './CollectionFilesList.vue'
import GeoreferencingModal from './GeoreferencingModal.vue'
import { isAuthenticated } from '../stores/auth.js'
import { matchTagsToPreset, getAllPresets } from '../utils/tagMatcher.js'
import { loadFieldDefinitions, resolveFields } from '../utils/fieldResolver.js'
import apiService from '../services/api.js'
import { getFileSize, getBaseFileType, getMimeType, getOriginalName, getDisplayName as getFileDisplayName, formatFileSize as formatSize } from '../utils/fileHelpers.js'

const route = useRoute()
const router = useRouter()

// Create login URL with current path as redirect
const loginUrl = computed(() => {
  const redirectParam = encodeURIComponent(route.fullPath)
  return `/login?redirect=${redirectParam}`
})

// State
const file = ref(null)
const loading = ref(false)
const error = ref(null)

// Georeferencing state
const showGeoreferencingModal = ref(false)
const georeferencingStatus = ref(null)

// Probe state for checking if file can be georeferenced
const probeResult = ref(null)
const probeLoading = ref(false)
const probeError = ref(null)

// Conversion state
const isConverting = ref(false)

// Layer controls state
const layerPanelOpen = ref(true)
const layers = ref({
  baseMap: {
    visible: true,
    opacity: 1.0
  },
  geotiff: {
    visible: true,
    opacity: 0.8
  }
})
const interactiveMapRef = ref(null)

// Field definitions and presets (reused from FileEditor)
const allPresets = ref([])
const allFieldDefinitions = ref({})
const selectedType = ref(null)

const props = defineProps({
  treeItemId: {
    type: String,
    required: true // Tree item ID for direct API access
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

async function loadFile() {
  if (!props.treeItemId) {
    error.value = 'No tree item ID provided'
    return
  }

  loading.value = true
  error.value = null
  
  try {
    // Use direct API call with tree item ID
    const response = await apiService.getTreeItem(props.treeItemId)
    
    file.value = response
    // Store the object type for UI rendering
    file.value.object_type = response.object_type || response.type

    // Set initial type based on file tags
    if (file.value && file.value.tags) {
      const matchedPreset = matchTagsToPreset(file.value.tags, allPresets.value, file.value.object_type)
      selectedType.value = matchedPreset
    }

    // Probe file if it's not already confirmed as georeferenced
    // This includes both regular files and geo-raster files that might need georeferencing
    if (file.value && file.value.type === 'file' && !isFileGeoreferenced.value) {
      // Clear previous probe results
      probeResult.value = null
      probeError.value = null
      // Probe the file in the background
      probeFile()
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
  return getBaseFileType(file.value)
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

// Check if file is georeferenced
const isFileGeoreferenced = computed(() => {
  if (probeResult.value && probeResult.value.can_georeference) {
    return probeResult.value.is_already_georeferenced
  }
  
  // Default to false if no conclusive information
  return false
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

// Georeferencing functions
function startGeoreferencing() {
  georeferencingStatus.value = { loading: true }
  showGeoreferencingModal.value = true
}

function closeGeoreferencing() {
  showGeoreferencingModal.value = false
  georeferencingStatus.value = null
}

function onGeoreferencingCompleted(result) {
  showGeoreferencingModal.value = false
  georeferencingStatus.value = null
  
  // Update file tags to reflect georeferencing status
  if (file.value && result.fileInfo) {
    file.value.tags = { ...file.value.tags, ...result.fileInfo }
  }
  
  // Force re-render to show the map
  loadFile()
}

// Probe functions
async function probeFile() {
  if (!file.value?.id) return

  probeLoading.value = true
  probeError.value = null
  
  try {
    const result = await apiService.probeTreeItem(file.value.id)
    probeResult.value = result
  } catch (err) {
    console.error('Failed to probe file:', err)
    probeError.value = err.message || 'Failed to probe file'
  } finally {
    probeLoading.value = false
  }
}

async function convertToGeoRaster() {
  if (!file.value?.id) return

  isConverting.value = true
  
  try {
    // Convert the file to geo-raster format
    const updatedFile = await apiService.convertToGeoRaster(file.value.id)
    
    // Update the file object with the new data
    file.value = updatedFile
    
    // Clear probe result since file is now converted
    probeResult.value = null
    
    // Reload the file to get the latest state
    await loadFile()
    
    // After conversion, automatically start the georeferencing process
    // The file is now a geo-raster but needs control points to be properly georeferenced
    startGeoreferencing()
  } catch (err) {
    console.error('Failed to convert file:', err)
    alert(`Failed to convert file: ${err.message}`)
  } finally {
    isConverting.value = false
  }
}

// Layer control functions
function toggleLayerPanel() {
  layerPanelOpen.value = !layerPanelOpen.value
}

function toggleLayer(layerId, visible) {
  if (interactiveMapRef.value && interactiveMapRef.value.map) {
    const map = interactiveMapRef.value.map
    if (visible) {
      map.setLayoutProperty(layerId, 'visibility', 'visible')
    } else {
      map.setLayoutProperty(layerId, 'visibility', 'none')
    }
  }
}

function updateLayerOpacity(layerId, opacity) {
  if (interactiveMapRef.value && interactiveMapRef.value.map) {
    const map = interactiveMapRef.value.map
    if (layerId === 'geotiff-layer') {
      map.setPaintProperty(layerId, 'raster-opacity', parseFloat(opacity))
    } else if (layerId === 'osm-tiles') {
      map.setPaintProperty(layerId, 'raster-opacity', parseFloat(opacity))
    }
  }
}

// Lifecycle
onMounted(async () => {
  // Load all field definitions and presets using centralized loading
  allPresets.value = getAllPresets()
  console.log('Loaded presets:', allPresets.value)
  allFieldDefinitions.value = await loadFieldDefinitions()
  await loadFile()
})

// Watch for prop changes
watch(() => props.treeItemId, () => {
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #eee;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
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

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  color: #666;
  transition: all 0.15s;
}

.back-btn:hover {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s;
  background: #007bff;
  color: white;
  border: none;
}

.edit-btn:hover {
  background: #0056b3;
}

.login-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s;
  background: #7b1fa2;
  color: white;
  border: none;
}

.login-btn:hover {
  background: #4a148c;
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

/* Georeferencing needed styles */
.georeferencing-needed {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
  background: #fff;
  border-radius: 8px;
  margin: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.georef-header {
  margin-bottom: 2rem;
}

.georef-icon {
  margin-bottom: 1rem;
}

.georef-header h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.georef-header p {
  margin: 0;
  color: #666;
  font-size: 1rem;
  max-width: 500px;
}

.georef-actions {
  margin-bottom: 1rem;
}

.georef-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.georef-btn:hover {
  background: #0056b3;
}

.georef-status {
  min-height: 40px;
}

.status-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
}

.status-error {
  color: #dc3545;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Probe status styles */
.probe-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  color: #666;
}

.probe-status .spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.probe-error,
.cannot-georeference,
.can-georeference,
.already-georeferenced {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
}

.probe-error .georef-icon,
.cannot-georeference .georef-icon {
  margin-bottom: 1rem;
}

.can-georeference {
  background: #f8f9fa;
  border: 2px solid #28a745;
  border-radius: 12px;
}

.needs-georeferencing {
  background: #fff8e1;
  border: 2px solid #ffc107;
  border-radius: 12px;
}

.convert-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.15s;
  margin-top: 1rem;
}

.convert-btn:hover:not(:disabled) {
  background: #218838;
}

.convert-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.7;
}

.convert-btn .spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.file-info {
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #495057;
}

.already-georeferenced {
  background: #e7f3ff;
  border: 2px solid #17a2b8;
  border-radius: 12px;
}

.default-georeferencing {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Layer Filter Block */
.layer-filter-block {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
  border-radius: 8px;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  border-radius: 8px 8px 0 0;
  transition: background-color 0.2s ease;
}

.filter-header:hover {
  background: #e9ecef;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.filter-icon {
  color: #666;
}

.filter-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
  color: #666;
}

.filter-toggle:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

.filter-toggle.expanded svg {
  transform: rotate(180deg);
}

.filter-toggle svg {
  transition: transform 0.2s ease;
}

.filter-content {
  padding: 16px;
  background: white;
  max-height: 200px;
  overflow-y: auto;
  border-radius: 0 0 8px 8px;
}

.layer-controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.layer-filter-item {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #f8f9fa;
  transition: all 0.2s ease;
}

.layer-filter-item:hover {
  border-color: #007bff;
  background: #f0f7ff;
}

.layer-filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  margin-bottom: 4px;
}

.layer-filter-checkbox {
  width: 16px;
  height: 16px;
  margin: 0;
  cursor: pointer;
  accent-color: #007bff;
}

.layer-filter-name {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.layer-description {
  font-size: 12px;
  color: #666;
  margin-left: 24px;
  margin-bottom: 8px;
}

.layer-opacity-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.opacity-section-label {
  display: block;
  font-size: 12px;
  color: #666;
  font-weight: 500;
  margin-bottom: 6px;
}

.layer-filter-opacity-slider {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: #e0e0e0;
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}

.layer-filter-opacity-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.layer-filter-opacity-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.layer-filter-opacity-slider:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
  opacity: 0.6;
}

.layer-filter-opacity-slider:disabled::-webkit-slider-thumb {
  background: #6c757d;
  cursor: not-allowed;
}

.layer-filter-opacity-slider:disabled::-moz-range-thumb {
  background: #6c757d;
  cursor: not-allowed;
}

.layer-opacity-section .opacity-section-label {
  color: #333;
}

.layer-filter-item:has(.layer-filter-opacity-slider:disabled) .opacity-section-label {
  color: #6c757d;
  opacity: 0.7;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .layer-controls-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-content {
    max-height: 150px;
  }
  
  .filter-header {
    padding: 10px 12px;
  }
}
</style> 