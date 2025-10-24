<template>
  <div class="interactive-map">
    <!-- Layer controls - positioned above the map -->
    <div v-if="!loading && !error" class="layer-controls">
      <div class="layer-controls-header" @click="toggleLayerPanel">
        <div class="layer-controls-title">
          <svg width="20" height="20" viewBox="0 0 24 24" class="layer-icon">
            <path d="M12 16l-6-6h12l-6 6z" fill="currentColor"/>
            <path d="M12 10l-6-6h12l-6 6z" fill="currentColor" opacity="0.6"/>
            <path d="M12 4l-6-6h12l-6 6z" fill="currentColor" opacity="0.3"/>
          </svg>
          <span>Map Layers</span>
        </div>
        <button class="layer-toggle" :class="{ 'expanded': layerPanelOpen }">
          <svg width="16" height="16" viewBox="0 0 24 24">
            <path d="M6 9l6 6 6-6" fill="currentColor"/>
          </svg>
        </button>
      </div>
      
      <div v-show="layerPanelOpen" class="layer-controls-content">
        <div class="layer-controls-grid">
          <!-- Base Map Layer -->
          <div class="layer-control-item">
            <label class="layer-control-label">
              <input 
                type="checkbox" 
                v-model="layers.baseMap.visible"
                @change="toggleLayer('base-map', layers.baseMap.visible)"
                class="layer-control-checkbox"
              />
              <span class="layer-control-name">Base Map</span>
            </label>
            
            <!-- Base Layer Switcher -->
            <div class="base-layer-switcher">
              <div class="base-layer-options">
                <button 
                  class="base-layer-option"
                  :class="{ 'active': baseLayer === 'osm' }"
                  @click="switchBaseLayer('osm')"
                  :disabled="!layers.baseMap.visible"
                >
                  <svg class="base-layer-icon" width="16" height="16" viewBox="0 0 24 24">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
                    <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" fill="none"/>
                    <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" fill="none"/>
                  </svg>
                  <span class="base-layer-name">OpenStreetMap</span>
                </button>
                <button 
                  class="base-layer-option"
                  :class="{ 'active': baseLayer === 'satellite' }"
                  @click="switchBaseLayer('satellite')"
                  :disabled="!layers.baseMap.visible"
                >
                  <svg class="base-layer-icon" width="16" height="16" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.3"/>
                    <path d="M12 2A10 10 0 0 0 2 12A10 10 0 0 0 12 22A10 10 0 0 0 22 12A10 10 0 0 0 12 2Z" stroke="currentColor" stroke-width="2" fill="none"/>
                    <path d="M8 12L12 8L16 12L12 16L8 12Z" fill="currentColor"/>
                  </svg>
                  <span class="base-layer-name">Satellite</span>
                </button>
              </div>

            </div>
          </div>
          
          <!-- GeoTIFF Layer -->
          <div class="layer-control-item">
            <label class="layer-control-label">
              <input 
                type="checkbox" 
                v-model="layers.geotiff.visible"
                @change="toggleLayer('geotiff-layer', layers.geotiff.visible)"
                class="layer-control-checkbox"
              />
              <span class="layer-control-name">{{ filename || 'Georeferenced File' }}</span>
            </label>
            <div class="layer-description">Uploaded georeferenced overlay</div>
            
            <!-- Opacity slider for GeoTIFF layer -->
            <div class="layer-opacity-section">
              <label class="opacity-label">Opacity: {{ Math.round(layers.geotiff.opacity * 100) }}%</label>
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.1"
                v-model="layers.geotiff.opacity"
                @input="updateLayerOpacity('geotiff-layer', layers.geotiff.opacity)"
                class="layer-opacity-slider"
                :disabled="!layers.geotiff.visible"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Map container with controls -->
    <div class="map-container">
      <!-- Map wrapper -->
      <div ref="mapContainer" class="map-wrapper"></div>
      
      <!-- Loading overlay -->
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <p>Loading interactive map...</p>
      </div>
      
      <!-- Error overlay -->
      <div v-else-if="error" class="error-overlay">
        <p>{{ error }}</p>
        <button @click="loadMap" class="retry-btn">Retry</button>
      </div>

      <!-- Map controls - only show when map is loaded -->
      <div v-if="!loading && !error" class="map-controls">
        <div class="control-group">
          <button @click="zoomIn" class="control-btn" title="Zoom In">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" fill="currentColor"/>
            </svg>
          </button>
          <button @click="zoomOut" class="control-btn" title="Zoom Out">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M19 13H5v-2h14v2z" fill="currentColor"/>
            </svg>
          </button>
        </div>
        
        <div class="control-group">
          <button @click="resetView" class="control-btn" title="Reset View">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z" fill="currentColor"/>
            </svg>
          </button>
          <button @click="fullscreen" class="control-btn" title="Fullscreen">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" fill="currentColor"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
    
    
    <!-- Map info panel - only show when map is loaded -->
    <div v-if="!loading && !error" class="map-info">
      <div class="info-item">
        <span class="info-label">File:</span>
        <span class="info-value">{{ filename }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">Zoom:</span>
        <span class="info-value">{{ zoomLevel }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">Center:</span>
        <span class="info-value">{{ centerCoords }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import apiService from '../services/api.js'

export default {
  name: 'InteractiveMap',
  props: {
    fileId: {
      type: String,
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
    const mapContainer = ref(null)
    const map = ref(null)
    const zoomLevel = ref(0)
    const centerCoords = ref('0, 0')
    
    // Layer controls state
    const layerPanelOpen = ref(true)
    const baseLayer = ref('osm') // 'osm' or 'satellite'
    const layers = ref({
      baseMap: {
        visible: true
      },
      geotiff: {
        visible: true,
        opacity: 0.8
      }
    })
    
    
    const loadMap = async () => {
      if (!props.fileId) return
      
      loading.value = true
      error.value = null
      
      try {
        // Wait for DOM to be ready
        await nextTick()
        
        // Check if container is available
        if (!mapContainer.value) {
          console.error('Map container not found')
          error.value = 'Map container not available'
          loading.value = false
          return
        }
        
        console.log('Container element found:', mapContainer.value)
        
        // Get the map URL from the backend
        const response = await apiService.request(`/files/${props.fileId}/map`)
        const mapUrl = response.map_url
        
        if (!mapUrl) {
          throw new Error('No map URL available for this file')
        }
        
        console.log('Map URL:', mapUrl)
        
        // Initialize MapLibre map with multiple base layer sources
        map.value = new maplibregl.Map({
          container: mapContainer.value,
          style: {
            version: 8,
            sources: {
              'osm': {
                type: 'raster',
                tiles: [
                  'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
                ],
                tileSize: 256,
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              },
              'satellite': {
                type: 'raster',
                tiles: [
                  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                ],
                tileSize: 256,
                attribution: '© <a href="https://www.esri.com/">Esri</a> — Source: Esri, Maxar, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community'
              }
            },
            layers: [
              {
                id: 'osm-tiles',
                type: 'raster',
                source: 'osm',
                minzoom: 0,
                maxzoom: 18
              }
            ]
          },
          center: [0, 0],
          zoom: 2,
          attributionControl: true
        })
        
        // Listen to map events
        map.value.on('load', () => {
          console.log('Map loaded successfully')
          loading.value = false
          
          // Add navigation controls
          map.value.addControl(new maplibregl.NavigationControl(), 'top-right')
          
          // Add scale control
          map.value.addControl(new maplibregl.ScaleControl({
            maxWidth: 100,
            unit: 'metric'
          }), 'bottom-left')
          
          // Add the GeoTIFF layer after the base map loads
          if (map.value && mapUrl) {
            map.value.addSource('geotiff', {
              type: 'raster',
              tiles: [
                `${mapUrl}&SERVICE=WMS&VERSION=1.3.0&STYLES=&REQUEST=GetMap&FORMAT=image/png&TRANSPARENT=true&LAYERS=geotiff_layer&CRS=EPSG:3857&WIDTH=256&HEIGHT=256&BBOX={bbox-epsg-3857}`
              ],
              tileSize: 256,
              attribution: '© MapServer'
            })
            
            map.value.addLayer({
              id: 'geotiff-layer',
              type: 'raster',
              source: 'geotiff',
              paint: {
                'raster-opacity': 0.8
              }
            })
            
            // Get the extent from the backend and zoom to it
            getAndZoomToExtent()
          }
        })
        
        map.value.on('zoom', () => {
          if (map.value) {
            zoomLevel.value = Math.round(map.value.getZoom() * 100) / 100
          }
        })
        
        map.value.on('move', () => {
          if (map.value) {
            const center = map.value.getCenter()
            centerCoords.value = `${center.lng.toFixed(4)}, ${center.lat.toFixed(4)}`
          }
        })
        
        map.value.on('error', (e) => {
          console.error('Map error:', e)
          error.value = 'Failed to load map tiles'
          loading.value = false
        })
        
      } catch (err) {
        console.error('Failed to load map:', err)
        error.value = err.message || 'Failed to load interactive map'
        loading.value = false
      }
    }
    
    const zoomIn = () => {
      if (map.value) {
        map.value.zoomIn()
      }
    }
    
    const zoomOut = () => {
      if (map.value) {
        map.value.zoomOut()
      }
    }
    
    const resetView = () => {
      if (map.value) {
        map.value.flyTo({
          center: [0, 0],
          zoom: 2,
          duration: 1000
        })
      }
    }
    
    const fullscreen = () => {
      if (map.value) {
        const container = mapContainer.value
        if (container.requestFullscreen) {
          container.requestFullscreen()
        } else if (container.webkitRequestFullscreen) {
          container.webkitRequestFullscreen()
        } else if (container.msRequestFullscreen) {
          container.msRequestFullscreen()
        }
      }
    }
    
    const getAndZoomToExtent = async () => {
      try {
        const response = await apiService.request(`/files/${props.fileId}/extent`)
        const extent = response.extent
        
        if (map.value && extent) {
          const [minLng, minLat, maxLng, maxLat] = extent.split(',').map(Number)
          
          // Calculate center point
          const centerLng = (minLng + maxLng) / 2
          const centerLat = (minLat + maxLat) / 2
          
          // Calculate appropriate zoom level based on extent size
          const lngDiff = Math.abs(maxLng - minLng)
          const latDiff = Math.abs(maxLat - minLat)
          const maxDiff = Math.max(lngDiff, latDiff)
          
          // Calculate zoom level (higher zoom for smaller extents)
          let zoom = 2
          if (maxDiff > 0) {
            // Use a logarithmic scale to determine zoom
            zoom = Math.max(2, Math.min(18, Math.floor(14 - Math.log2(maxDiff))))
          }
          
          console.log(`Zooming to extent: ${extent}, center: [${centerLng}, ${centerLat}], zoom: ${zoom}`)
          
          // Use fitBounds for better automatic fitting
          map.value.fitBounds(
            [[minLng, minLat], [maxLng, maxLat]],
            {
              padding: 50, // Add some padding around the bounds
              duration: 0,
              essential: true
            }
          )
        }
      } catch (err) {
        console.error('Failed to get and zoom to extent:', err)
        // Don't show error to user, just log it - the map will still work
        console.log('Continuing with default map view')
      }
    }
    
    // Layer control functions
    const toggleLayerPanel = () => {
      layerPanelOpen.value = !layerPanelOpen.value
    }
    
    const toggleLayer = (layerId, visible) => {
      if (map.value) {
        // Handle base map layer switching
        if (layerId === 'base-map') {
          const currentLayerId = baseLayer.value === 'osm' ? 'osm-tiles' : 'satellite-tiles'
          if (visible) {
            map.value.setLayoutProperty(currentLayerId, 'visibility', 'visible')
          } else {
            map.value.setLayoutProperty(currentLayerId, 'visibility', 'none')
          }
        } else {
          // Handle other layers (GeoTIFF)
          if (visible) {
            map.value.setLayoutProperty(layerId, 'visibility', 'visible')
          } else {
            map.value.setLayoutProperty(layerId, 'visibility', 'none')
          }
        }
      }
    }
    
    const updateLayerOpacity = (layerId, opacity) => {
      if (map.value) {
        if (layerId === 'geotiff-layer') {
          map.value.setPaintProperty(layerId, 'raster-opacity', parseFloat(opacity))
        }
      }
    }
    
    // Base layer switching function
    const switchBaseLayer = (newBaseLayer) => {
      if (map.value && baseLayer.value !== newBaseLayer) {
        baseLayer.value = newBaseLayer
        
        // Remove current base layer
        if (map.value.getLayer('osm-tiles')) {
          map.value.removeLayer('osm-tiles')
        }
        if (map.value.getLayer('satellite-tiles')) {
          map.value.removeLayer('satellite-tiles')
        }
        
        // Add new base layer at the bottom (before any other layers)
        const layerId = newBaseLayer === 'osm' ? 'osm-tiles' : 'satellite-tiles'
        const sourceId = newBaseLayer
        
        map.value.addLayer({
          id: layerId,
          type: 'raster',
          source: sourceId,
          minzoom: 0,
          maxzoom: 18
        }, 'geotiff-layer') // Insert before the GeoTIFF layer
        
        // Apply current visibility setting
        const currentVisibility = layers.value.baseMap.visible ? 'visible' : 'none'
        map.value.setLayoutProperty(layerId, 'visibility', currentVisibility)
      }
    }
    
    
    onMounted(async () => {
      await nextTick()
      loadMap()
    })
    
    onUnmounted(() => {
      if (map.value) {
        map.value.remove()
      }
    })
    
    watch(() => props.fileId, async () => {
      if (map.value) {
        map.value.remove()
      }
      await nextTick()
      loadMap()
    })
    
    return {
      loading,
      error,
      mapContainer,
      zoomLevel,
      centerCoords,
      loadMap,
      zoomIn,
      zoomOut,
      resetView,
      fullscreen,
      map,
      // Layer controls
      layerPanelOpen,
      baseLayer,
      layers,
      toggleLayerPanel,
      toggleLayer,
      updateLayerOpacity,
      switchBaseLayer
    }
  }
}
</script>

<style scoped>
.interactive-map {
  height: 100%;
  position: relative;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 1000;
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

.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 235, 238, 0.95);
  z-index: 1000;
  color: #d32f2f;
  text-align: center;
  padding: 2rem;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #d32f2f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #b71c1c;
}

.map-controls {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: white;
  border-radius: 6px;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.map-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.map-wrapper {
  width: 100%;
  height: 100%;
}

.map-info {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 1000;
}

.info-item {
  display: flex;
  gap: 8px;
  margin: 2px 0;
}

.info-label {
  font-weight: 500;
  color: #666;
  min-width: 50px;
}

.info-value {
  color: #333;
  font-family: monospace;
}

/* MapLibre GL JS styles */
:deep(.maplibregl-map) {
  border-radius: 8px;
}

:deep(.maplibregl-ctrl-group) {
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

:deep(.maplibregl-ctrl-group button) {
  border-radius: 4px;
  margin: 2px;
}

:deep(.maplibregl-ctrl-scale) {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 4px 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Layer Controls Styles */
.layer-controls {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
  width: 100%;
}

.layer-controls-header {
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

.layer-controls-header:hover {
  background: #e9ecef;
}

.layer-controls-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.layer-icon {
  color: #666;
}

.layer-toggle {
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

.layer-toggle:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

.layer-toggle.expanded svg {
  transform: rotate(180deg);
}

.layer-toggle svg {
  transition: transform 0.2s ease;
}

.layer-controls-content {
  padding: 16px;
  background: white;
  max-height: 300px;
  overflow-y: auto;
  border-radius: 0 0 8px 8px;
}

.layer-controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.layer-control-item {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #f8f9fa;
  transition: all 0.2s ease;
}

.layer-control-item:hover {
  border-color: #007bff;
  background: #f0f7ff;
}

.layer-control-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  margin-bottom: 4px;
}

.layer-control-checkbox {
  width: 16px;
  height: 16px;
  margin: 0;
  cursor: pointer;
  accent-color: #007bff;
}

.layer-control-name {
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

.base-layer-switcher {
  margin-top: 12px;
  margin-left: 24px;
  margin-bottom: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}


.base-layer-options {
  display: flex;
  gap: 12px;
}

.base-layer-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  padding: 8px 12px;
  border-radius: 6px;
  background: white;
  border: 2px solid #e9ecef;
  transition: all 0.2s ease;
  flex: 1;
  justify-content: center;
  position: relative;
  font-family: inherit;
  font-size: inherit;
}

.base-layer-option:hover {
  border-color: #007bff;
  background: #f8f9ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.1);
}

.base-layer-option:hover .base-layer-name {
  color: #007bff;
}

.base-layer-option:hover .base-layer-icon {
  color: #007bff;
}

.base-layer-option.active {
  border-color: #007bff;
  background: #e3f2fd;
  box-shadow: 0 0 0 1px #007bff;
}

.base-layer-option.active .base-layer-name {
  color: #007bff;
}

.base-layer-option.active .base-layer-icon {
  color: #007bff;
}

.base-layer-option:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f8f9fa;
  border-color: #dee2e6;
}

.base-layer-option:disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: #dee2e6;
  background: #f8f9fa;
}

.base-layer-option:disabled .base-layer-name {
  color: #6c757d;
}

.base-layer-option:disabled .base-layer-icon {
  color: #6c757d;
}

.base-layer-name {
  font-size: 13px;
  color: #333;
  font-weight: 600;
  transition: color 0.2s ease;
}

.base-layer-icon {
  width: 16px;
  height: 16px;
  color: #666;
  transition: color 0.2s ease;
}

.layer-opacity-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.opacity-label {
  display: block;
  font-size: 12px;
  color: #666;
  font-weight: 500;
  margin-bottom: 6px;
}

.layer-opacity-slider {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: #e0e0e0;
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}

.layer-opacity-slider::-webkit-slider-thumb {
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

.layer-opacity-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.layer-opacity-slider:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
  opacity: 0.6;
}

.layer-opacity-slider:disabled::-webkit-slider-thumb {
  background: #6c757d;
  cursor: not-allowed;
}

.layer-opacity-slider:disabled::-moz-range-thumb {
  background: #6c757d;
  cursor: not-allowed;
}

.layer-opacity-section .opacity-label {
  color: #333;
}

.layer-control-item:has(.layer-opacity-slider:disabled) .opacity-label {
  color: #6c757d;
  opacity: 0.7;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .layer-controls-grid {
    grid-template-columns: 1fr;
  }
  
  .layer-controls-content {
    max-height: 200px;
  }
  
  .layer-controls-header {
    padding: 10px 12px;
  }
  
  .base-layer-options {
    flex-direction: column;
    gap: 8px;
  }
  
  .base-layer-option {
    padding: 10px 12px;
  }
  
  .base-layer-switcher {
    margin-left: 16px;
    padding: 10px;
  }
}

</style> 