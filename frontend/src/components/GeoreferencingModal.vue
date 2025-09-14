<template>
  <div class="georeferencing-modal-overlay">
    <div class="georeferencing-modal" @click.stop>
      <!-- Header -->
      <div class="modal-header">
        <h2>Georeference Image</h2>
        <div class="header-actions">
          <div class="control-points-count">
            <span class="label">Control Points:</span>
            <span class="count">{{ controlPoints.length }}/{{ minControlPoints }}</span>
          </div>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
      </div>

      <!-- Instructions -->
      <div class="instructions-bar">
        <div class="instruction-text">
          <template v-if="currentMode === 'adding'">
            <strong>Click on the image</strong> to add a control point, then <strong>click on the map</strong> to set its real-world coordinates.
          </template>
          <template v-else-if="currentMode === 'waiting-map'">
            Now <strong>click on the map</strong> to set the world coordinates for this point.
          </template>
          <template v-else>
            Add at least {{ minControlPoints }} control points to georeference the image.
          </template>
        </div>
        <div class="mode-indicator" :class="currentMode">
          {{ getModeText() }}
        </div>
      </div>

      <!-- Split Screen Container -->
      <div class="split-container">
        <!-- Left Panel: Image -->
        <div class="image-panel">
          <div class="panel-header">
            <h3>Original Image</h3>
            <div class="image-controls">
              <button class="control-btn" @click="resetImageView" title="Reset View">
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <path d="M8 2L2 8l6 6 6-6-6-6z" fill="currentColor"/>
                </svg>
              </button>
              <button class="control-btn" @click="toggleImageFullscreen" title="Fullscreen">
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <path d="M1 1h6v2H3v4H1V1zM1 15h6v-2H3v-4H1v6zM15 1H9v2h4v4h2V1zM15 15H9v-2h4v-4h2v6z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="image-container" ref="imageContainer">
            <div id="image-map" class="maplibre-map"></div>
          </div>
        </div>

        <!-- Right Panel: Map -->
        <div class="map-panel">
          <div class="panel-header">
            <h3>Reference Map</h3>
            <div class="map-controls">
              <select v-model="selectedMapLayer" @change="changeMapLayer" class="map-layer-select">
                <option value="osm">OpenStreetMap</option>
                <option value="satellite">Satellite</option>
                <option value="terrain">Terrain</option>
              </select>
            </div>
          </div>
          
          <div class="map-container" ref="mapContainer">
            <div id="georef-map" class="maplibre-map"></div>
            
            <!-- Control Points on Map -->
            <div v-for="(point, index) in controlPoints" 
                 :key="`map-${index}`"
                 class="control-point map-point"
                 :class="{ 'active': index === activePointIndex }"
                 @click.stop="selectControlPoint(index)">
              <div class="point-marker">{{ index + 1 }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Control Points List -->
      <div class="control-points-panel">
        <div class="panel-header">
          <h3>Control Points</h3>
          <div class="validation-status" v-if="validationResults">
            <span class="rmse" :class="{ 'good': validationResults.statistics?.rmse < 50, 'warning': validationResults.statistics?.rmse >= 50 }">
              RMSE: {{ validationResults.statistics?.rmse?.toFixed(2) || 'N/A' }}
            </span>
          </div>
        </div>
        
        <div class="points-list">
          <div v-if="controlPoints.length === 0" class="empty-message">
            No control points added yet. Click on the image to start.
          </div>
          
          <div v-for="(point, index) in controlPoints" 
               :key="index"
               class="point-row"
               :class="{ 'active': index === activePointIndex }"
               @click="selectControlPoint(index)">
            <div class="point-number">{{ index + 1 }}</div>
            <div class="point-coordinates">
              <div class="coord-group">
                <label>Image:</label>
                <span>{{ point.image_x.toFixed(2) }}, {{ point.image_y.toFixed(2) }}</span>
              </div>
              <div class="coord-group">
                <label>World:</label>
                <span>{{ point.world_x.toFixed(6) }}, {{ point.world_y.toFixed(6) }}</span>
              </div>
            </div>
            <button class="delete-point" @click.stop="removeControlPoint(index)" title="Delete Point">
              <svg width="14" height="14" viewBox="0 0 14 14">
                <path d="M14 1.41L12.59 0L7 5.59L1.41 0L0 1.41L5.59 7L0 12.59L1.41 14L7 8.41L12.59 14L14 12.59L8.41 7L14 1.41Z" fill="currentColor"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="modal-actions">
        <button class="btn btn-secondary" @click="closeModal">Cancel</button>
        <button class="btn btn-outline" @click="clearAllPoints" :disabled="controlPoints.length === 0">
          Clear All
        </button>
        <button class="btn btn-primary apply-btn" @click="applyGeoreferencing" :disabled="!canApply || isApplyingGeoreferencing">
          <div v-if="isApplyingGeoreferencing" class="spinner"></div>
          <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 2v4M8 10v4M2 8h4M10 8h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="8" cy="8" r="2" fill="currentColor"/>
          </svg>
          {{ isApplyingGeoreferencing ? 'Applying Georeferencing...' : 'Apply Georeferencing' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import apiService from '../services/api.js'

const props = defineProps({
  fileId: { type: String, required: true },
  fileInfo: { type: Object, required: true }
})

const emit = defineEmits(['close', 'completed'])

// State
const imageContainer = ref(null)
const mapContainer = ref(null)
const imageMap = ref(null)  // MapLibre instance for the image
const referenceMap = ref(null)  // MapLibre instance for the reference map
const imageMapUrl = ref('')
const minControlPoints = 3

// Control points
const controlPoints = ref([])
const activePointIndex = ref(-1)
const pendingImagePoint = ref(null)
const currentMode = ref('adding') // 'adding', 'waiting-map', 'complete'

// MapLibre markers
const imageMarkers = ref([]) // Array of MapLibre markers on image map
const referenceMarkers = ref([]) // Array of MapLibre markers on reference map
const pendingImageMarker = ref(null) // Pending marker on image map

// Map state
const selectedMapLayer = ref('osm')

// Validation
const validationResults = ref(null)

// Apply georeferencing loading state
const isApplyingGeoreferencing = ref(false)

// Computed
const imageTransform = computed(() => {
  return {
    transform: `scale(${imageScale.value}) translate(${imageTranslate.value.x}px, ${imageTranslate.value.y}px)`,
    transformOrigin: 'top left'
  }
})

const canApply = computed(() => controlPoints.value.length >= minControlPoints && validationResults.value?.valid)

// Methods
function closeModal() {
  emit('close')
}

function getModeText() {
  switch (currentMode.value) {
    case 'adding': return 'Click Image'
    case 'waiting-map': return 'Click Map'
    case 'complete': return 'Ready'
    default: return 'Ready'
  }
}

async function loadImageMapUrl() {
  try {
    // Get MapServer URL for the file
    const response = await apiService.request(`/files/${props.fileId}/map`)
    imageMapUrl.value = response.map_url
    console.log('Image map URL:', imageMapUrl.value)
    
    // Also get the file extent to center the image map
    try {
      const extentResponse = await apiService.request(`/files/${props.fileId}/extent`)
      const extent = extentResponse.extent.split(',').map(Number) // [minX, minY, maxX, maxY]
      
      // Calculate center and zoom level for the image map
      const centerLng = (extent[0] + extent[2]) / 2
      const centerLat = (extent[1] + extent[3]) / 2
      
      // Store extent info for later use
      window.imageExtent = { 
        center: [centerLng, centerLat],
        bounds: [[extent[0], extent[1]], [extent[2], extent[3]]]
      }
      
      console.log('Image extent:', window.imageExtent)
    } catch (extentError) {
      console.warn('Could not get file extent:', extentError)
    }
    
  } catch (error) {
    console.error('Failed to load image map URL:', error)
    throw new Error('Could not load image map URL: ' + error.message)
  }
}

function initializeMaps() {
  // Initialize image map (left panel) - shows the uploaded raster
  // Now using EPSG:3857, start at center (0,0) which is intersection of equator and prime meridian
  if (imageMapUrl.value) {
    console.log('Initializing image map with URL:', imageMapUrl.value)
    
    imageMap.value = new maplibregl.Map({
      container: 'image-map',
      center: [0, 0], // Center on equator/prime meridian intersection in Web Mercator
      zoom: 5, // Start zoomed out to see the 1000km area
      style: getImageMapStyle()
    })
    
    // Log when style loads
    imageMap.value.on('styledata', () => {
      console.log('Image map style loaded')
    })
    
    // Log when sources are loaded
    imageMap.value.on('sourcedata', (e) => {
      if (e.sourceId === 'raster-source') {
        console.log('Raster source loaded:', e)
      }
    })
    
    // Handle clicks on image map
    imageMap.value.on('click', onImageMapClick)
    
    // Add map bounds for debugging
    imageMap.value.on('moveend', () => {
      const bounds = imageMap.value.getBounds()
      console.log('Image map bounds:', bounds)
    })
  } else {
    console.warn('Cannot initialize image map: missing URL')
  }

  // Initialize reference map (right panel) - shows base layers
  referenceMap.value = new maplibregl.Map({
    container: 'georef-map',
    center: [30.5234, 50.4501], // Default to Kyiv [lng, lat]
    zoom: 10,
    style: getMapStyle(selectedMapLayer.value)
  })

  // Handle clicks on reference map
  referenceMap.value.on('click', onReferenceMapClick)
}

function getImageMapStyle() {
  // Create a style that will show the raster image via WMS
  const baseUrl = imageMapUrl.value
  
  // Now we can use proper tiled raster source with EPSG:3857 (Web Mercator)
  // MapLibre GL natively supports {bbox-epsg-3857} template replacement
  const wmsUrl = `${baseUrl}&LAYERS=geotiff_layer&TRANSPARENT=true&FORMAT=image/png&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&SRS=EPSG:3857&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256`
  
  return {
    version: 8,
    sources: {
      'raster-source': {
        type: 'raster',
        tiles: [wmsUrl],
        tileSize: 256
      }
    },
    layers: [{
      id: 'raster-layer',
      type: 'raster',
      source: 'raster-source'
    }]
  }
}

function getMapStyle(layerType) {
  const styles = {
    osm: {
      version: 8,
      sources: {
        osm: {
          type: 'raster',
          tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
          tileSize: 256,
          attribution: '© OpenStreetMap contributors'
        }
      },
      layers: [{
        id: 'osm',
        type: 'raster',
        source: 'osm'
      }]
    },
    satellite: {
      version: 8,
      sources: {
        satellite: {
          type: 'raster',
          tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
          tileSize: 256,
          attribution: 'Tiles © Esri'
        }
      },
      layers: [{
        id: 'satellite',
        type: 'raster',
        source: 'satellite'
      }]
    },
    terrain: {
      version: 8,
      sources: {
        terrain: {
          type: 'raster',
          tiles: ['https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png'],
          tileSize: 256,
          attribution: '© OpenTopoMap contributors'
        }
      },
      layers: [{
        id: 'terrain',
        type: 'raster',
        source: 'terrain'
      }]
    }
  }
  
  return styles[layerType] || styles.osm
}

function changeMapLayer() {
  // Update reference map style
  if (referenceMap.value) {
    referenceMap.value.setStyle(getMapStyle(selectedMapLayer.value))
  }
}

function onImageMapClick(event) {
  if (currentMode.value !== 'adding') return
  
  const { lng, lat } = event.lngLat
  
  console.log('=== IMAGE MAP CLICK DEBUG ===')
  console.log('Raw coordinates:', { lng, lat })
  console.log('Event object:', event)
  console.log('Event lngLat type:', typeof lng, typeof lat)
  console.log('Map center:', imageMap.value?.getCenter())
  console.log('Map zoom:', imageMap.value?.getZoom())
  console.log('Map bounds:', imageMap.value?.getBounds())
  
  // Also try alternative coordinate extraction methods
  const point = event.point
  console.log('Event.point (pixel coordinates):', point)
  
  const queriedFeatures = imageMap.value.queryRenderedFeatures(point)
  console.log('Queried features at click point:', queriedFeatures)
  
  // Ensure we have valid numbers
  if (typeof lng !== 'number' || typeof lat !== 'number' || isNaN(lng) || isNaN(lat)) {
    console.error('Invalid coordinates received:', { lng, lat })
    return
  }
  
  // Store pending point - these are Web Mercator coordinates from the dummy georeference
  pendingImagePoint.value = { lng, lat }
  currentMode.value = 'waiting-map'
  
  console.log('Stored pending image point:', pendingImagePoint.value)
  
  // Remove previous pending marker if exists
  if (pendingImageMarker.value) {
    pendingImageMarker.value.remove()
  }
  
  // Create a pending marker on the image map
  const markerElement = document.createElement('div')
  markerElement.className = 'control-point pending-point'
  markerElement.innerHTML = '<div class="point-marker">?</div>'
  
  pendingImageMarker.value = new maplibregl.Marker(markerElement)
    .setLngLat([lng, lat])
    .addTo(imageMap.value)
  
  console.log('=== END DEBUG ===')
}

function onReferenceMapClick(event) {
  if (currentMode.value !== 'waiting-map' || !pendingImagePoint.value) return
  
  const { lng, lat } = event.lngLat
  
  console.log('Reference map clicked:', { lng, lat })
  console.log('Pending image point at reference click:', pendingImagePoint.value)
  
  // Create control point using Web Mercator coordinates from image and lat/lng from reference
  const controlPoint = {
    image_x: pendingImagePoint.value.lng,  // Web Mercator X coordinate from dummy georeference
    image_y: pendingImagePoint.value.lat,  // Web Mercator Y coordinate from dummy georeference
    world_x: lng,  // Real world longitude
    world_y: lat   // Real world latitude
  }
  
  console.log('Created control point:', controlPoint)
  
  const pointIndex = controlPoints.value.length
  controlPoints.value.push(controlPoint)
  
  // Convert pending marker to permanent marker on image map
  if (pendingImageMarker.value) {
    // Remove pending marker
    pendingImageMarker.value.remove()
    pendingImageMarker.value = null
    
    // Create permanent marker on image map
    const imageMarkerElement = document.createElement('div')
    imageMarkerElement.className = 'control-point image-point'
    imageMarkerElement.innerHTML = `<div class="point-marker">${pointIndex + 1}</div>`
    imageMarkerElement.addEventListener('click', () => selectControlPoint(pointIndex))
    
    const imageMarker = new maplibregl.Marker(imageMarkerElement)
      .setLngLat([controlPoint.image_x, controlPoint.image_y])
      .addTo(imageMap.value)
    
    imageMarkers.value.push(imageMarker)
  }
  
  // Create marker on reference map
  const refMarkerElement = document.createElement('div')
  refMarkerElement.className = 'control-point reference-point'
  refMarkerElement.innerHTML = `<div class="point-marker">${pointIndex + 1}</div>`
  refMarkerElement.addEventListener('click', () => selectControlPoint(pointIndex))
  
  const referenceMarker = new maplibregl.Marker(refMarkerElement)
    .setLngLat([controlPoint.world_x, controlPoint.world_y])
    .addTo(referenceMap.value)
  
  referenceMarkers.value.push(referenceMarker)
  
  // Reset state
  pendingImagePoint.value = null
  currentMode.value = 'adding'
  
  console.log('Reference map clicked, control point created:', controlPoint)
  
  // Validate if we have enough points
  if (controlPoints.value.length >= minControlPoints) {
    validateControlPoints()
  }
}

function selectControlPoint(index) {
  activePointIndex.value = index
  
  // Pan both maps to selected point
  if (controlPoints.value[index]) {
    const point = controlPoints.value[index]
    
    // Pan image map to Web Mercator coordinates (these are already in the correct format)
    if (imageMap.value) {
      imageMap.value.setCenter([point.image_x, point.image_y])
    }
    
    // Pan reference map to world coordinates (lat/lng)
    if (referenceMap.value) {
      referenceMap.value.setCenter([point.world_x, point.world_y])
    }
  }
}

function removeControlPoint(index) {
  // Remove markers
  if (imageMarkers.value[index]) {
    imageMarkers.value[index].remove()
    imageMarkers.value.splice(index, 1)
  }
  
  if (referenceMarkers.value[index]) {
    referenceMarkers.value[index].remove()
    referenceMarkers.value.splice(index, 1)
  }
  
  // Remove control point
  controlPoints.value.splice(index, 1)
  
  // Update remaining marker numbers
  imageMarkers.value.forEach((marker, i) => {
    const element = marker.getElement()
    const numberElement = element.querySelector('.point-marker')
    if (numberElement) {
      numberElement.textContent = (i + 1).toString()
    }
  })
  
  referenceMarkers.value.forEach((marker, i) => {
    const element = marker.getElement()
    const numberElement = element.querySelector('.point-marker')
    if (numberElement) {
      numberElement.textContent = (i + 1).toString()
    }
  })
  
  if (activePointIndex.value === index) {
    activePointIndex.value = -1
  } else if (activePointIndex.value > index) {
    activePointIndex.value--
  }
  
  // Re-validate if we still have enough points
  if (controlPoints.value.length >= minControlPoints) {
    validateControlPoints()
  } else {
    validationResults.value = null
  }
}

function clearAllPoints() {
  // Remove all markers
  imageMarkers.value.forEach(marker => marker.remove())
  referenceMarkers.value.forEach(marker => marker.remove())
  
  if (pendingImageMarker.value) {
    pendingImageMarker.value.remove()
    pendingImageMarker.value = null
  }
  
  // Clear arrays
  imageMarkers.value = []
  referenceMarkers.value = []
  controlPoints.value = []
  
  activePointIndex.value = -1
  pendingImagePoint.value = null
  currentMode.value = 'adding'
  validationResults.value = null
}

async function validateControlPoints() {
  if (controlPoints.value.length < minControlPoints) return
  
  try {
    const response = await apiService.validateControlPoints(props.fileId, {
      control_points: controlPoints.value
    })
    
    validationResults.value = response
  } catch (error) {
    console.error('Validation failed:', error)
    validationResults.value = { valid: false, errors: [error.message] }
  }
}

async function applyGeoreferencing() {
  if (!canApply.value || isApplyingGeoreferencing.value) return
  
  isApplyingGeoreferencing.value = true
  
  try {
    const response = await apiService.applyGeoreferencing(props.fileId, {
      control_points: controlPoints.value,
      control_points_srs: 'EPSG:4326'
    })
    
    emit('completed', {
      message: 'Georeferencing applied successfully',
      fileInfo: response.file.tags,
      validationResults: response.validation_results
    })
  } catch (error) {
    console.error('Apply georeferencing failed:', error)
    alert('Failed to apply georeferencing: ' + error.message)
  } finally {
    isApplyingGeoreferencing.value = false
  }
}

// Map manipulation functions
function resetImageView() {
  if (imageMap.value) {
    // Reset image map to fit the raster extent
    const extent = window.imageExtent
    if (extent && extent.bounds) {
      imageMap.value.fitBounds(extent.bounds, { padding: 20 })
    } else {
      imageMap.value.setZoom(1)
      imageMap.value.setCenter([0, 0])
    }
  }
}

function toggleImageFullscreen() {
  // TODO: Implement fullscreen mode for image map
}

// Lifecycle
onMounted(async () => {
  try {
    await loadImageMapUrl()
    await nextTick()
    initializeMaps()
  } catch (error) {
    console.error('Failed to initialize georeferencing modal:', error)
    // You might want to show an error message to the user
  }
})

onUnmounted(() => {
  // Clean up markers
  imageMarkers.value.forEach(marker => marker.remove())
  referenceMarkers.value.forEach(marker => marker.remove())
  
  if (pendingImageMarker.value) {
    pendingImageMarker.value.remove()
  }
  
  // Clean up maps
  if (imageMap.value) {
    imageMap.value.remove()
  }
  
  if (referenceMap.value) {
    referenceMap.value.remove()
  }
})
</script>

<style scoped>
.georeferencing-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.georeferencing-modal {
  background: white;
  border-radius: 12px;
  width: 95vw;
  height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.control-points-count {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.control-points-count .label {
  color: #666;
  font-weight: 500;
}

.control-points-count .count {
  color: #333;
  font-weight: 600;
  background: #e9ecef;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e9ecef;
  color: #333;
}

.instructions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #e3f2fd;
  border-bottom: 1px solid #bbdefb;
}

.instruction-text {
  color: #1565c0;
  font-size: 0.9rem;
}

.mode-indicator {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.mode-indicator.adding {
  background: #e3f2fd;
  color: #1565c0;
}

.mode-indicator.waiting-map {
  background: #fff3e0;
  color: #ef6c00;
}

.mode-indicator.complete {
  background: #e8f5e8;
  color: #2e7d32;
}

.split-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.image-panel, .map-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #eee;
}

.map-panel {
  border-right: none;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.panel-header h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
}

.image-controls, .map-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.control-btn {
  background: none;
  border: 1px solid #ddd;
  padding: 0.375rem;
  border-radius: 4px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #e9ecef;
  border-color: #adb5bd;
  color: #333;
}

.map-layer-select {
  padding: 0.375rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.8rem;
  background: white;
}

.image-container, .map-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}


.maplibre-map {
  width: 100%;
  height: 100%;
}

.control-point {
  position: absolute;
  z-index: 1000;
  pointer-events: auto;
  cursor: pointer;
}

.point-marker {
  width: 24px;
  height: 24px;
  background: #007bff;
  color: white;
  border: 2px solid white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transform: translate(-50%, -50%);
}

.point-crosshair {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 40px;
  height: 40px;
  border: 1px solid #007bff;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.point-crosshair::before,
.point-crosshair::after {
  content: '';
  position: absolute;
  background: #007bff;
}

.point-crosshair::before {
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  transform: translateY(-50%);
}

.point-crosshair::after {
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  transform: translateX(-50%);
}

.control-point.active .point-marker {
  background: #dc3545;
  border-color: white;
}

.control-point.active .point-crosshair {
  border-color: #dc3545;
}

.control-point.active .point-crosshair::before,
.control-point.active .point-crosshair::after {
  background: #dc3545;
}

.pending-point .point-marker {
  background: #ffc107;
  color: #212529;
}

.pending-point .point-crosshair {
  border-color: #ffc107;
}

.pending-point .point-crosshair::before,
.pending-point .point-crosshair::after {
  background: #ffc107;
}

.control-points-panel {
  border-top: 1px solid #eee;
  background: #f8f9fa;
  max-height: 200px;
  overflow-y: auto;
}

.points-list {
  padding: 1rem;
}

.empty-message {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 2rem;
}

.point-row {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.point-row:hover {
  background: #f8f9ff;
  border-color: #007bff;
}

.point-row.active {
  background: #e3f2fd;
  border-color: #1976d2;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.2);
}

.point-number {
  width: 32px;
  height: 32px;
  background: #007bff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
  margin-right: 1rem;
}

.point-coordinates {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.coord-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.coord-group label {
  font-size: 0.75rem;
  color: #666;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.coord-group span {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.8rem;
  color: #333;
}

.delete-point {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.delete-point:hover {
  background: #f8d7da;
}

.validation-status {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.rmse {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
}

.rmse.good {
  background: #d4edda;
  color: #155724;
}

.rmse.warning {
  background: #fff3cd;
  color: #856404;
}

.modal-actions {
  display: flex;
  justify-content: space-between;
  padding: 1.5rem 2rem;
  border-top: 1px solid #eee;
  background: #f8f9fa;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-outline {
  background: none;
  border: 1px solid #007bff;
  color: #007bff;
}

.btn-outline:hover:not(:disabled) {
  background: #007bff;
  color: white;
}

/* Apply button layout */
.apply-btn {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Spinner animation for apply button */
.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
