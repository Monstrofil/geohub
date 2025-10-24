<template>
  <div class="interactive-map">
    <!-- Map container - always render this first -->
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
    <div v-else class="map-controls">
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
        
        // Initialize MapLibre map with a simpler configuration
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
      map
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

</style> 