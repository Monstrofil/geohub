<template>
  <div class="map-links-section">
    <div class="links-header">
      <h3>{{ $t('mapService.title') }}</h3>
      <p>{{ $t('mapService.description') }}</p>
    </div>
    
    <div class="links-grid">
      <!-- WMS Link -->
      <div class="link-item">
        <div class="link-header">
          <div class="link-main-content">
            <div class="link-icon">
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path d="M12 2L2 7v10c0 5.55 3.84 10 9 11 1.06.21 2.17.21 3.23 0 5.16-1 9-5.45 9-11V7l-10-5zM10 17l-5-5 1.41-1.41L10 14.17l7.59-7.58L19 8l-9 9z" fill="currentColor"/>
              </svg>
            </div>
            <div class="link-info">
              <h4>{{ $t('mapService.wms.title') }} <span class="type">wms</span></h4>
              <p>{{ $t('mapService.wms.description') }}</p>
            </div>
          </div>
        </div>
        <div class="link-url-container">
          <input 
            type="text" 
            :value="wmsUrl" 
            readonly 
            class="link-url"
            ref="wmsUrlInput"
          />
          <button @click="copyToClipboard(wmsUrl, $t('mapService.wms.copyUrl'))" class="copy-btn" :title="$t('mapService.wms.copyUrl')">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z" fill="currentColor"/>
            </svg>
          </button>
        </div>
        <div class="link-details">
          <div><strong>{{ $t('mapService.wms.layerName') }}</strong> {{ $t('mapService.wms.layerValue') }}</div>
          <div><strong>{{ $t('mapService.wms.bestFor') }}</strong> {{ $t('mapService.wms.bestForValue') }}</div>
        </div>
      </div>
      
      <!-- TMS Link -->
      <div class="link-item">
        <div class="link-header">
          <div class="link-main-content">
            <div class="link-icon">
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path d="M3 3v18h18V3H3zm16 16H5V5h14v14zm-8-2h2v-2h-2v2zm0-4h2V9h-2v2zm0-4h2V5h-2v2z" fill="currentColor"/>
              </svg>
            </div>
            <div class="link-info">
              <h4>{{ $t('mapService.tms.title') }} <span class="type">tms</span></h4>
              <p>{{ $t('mapService.tms.description') }}</p>
            </div>
          </div>
        </div>
        <div class="link-url-container">
          <input 
            type="text" 
            :value="tmsUrl" 
            readonly 
            class="link-url"
            ref="tmsUrlInput"
          />
          <button @click="copyToClipboard(tmsUrl, $t('mapService.tms.copyUrl'))" class="copy-btn" :title="$t('mapService.tms.copyUrl')">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z" fill="currentColor"/>
            </svg>
          </button>
        </div>
        <div class="link-details">
          <div><strong>{{ $t('mapService.tms.format') }}</strong> {{ $t('mapService.tms.formatValue') }}</div>
        </div>
      </div>
    </div>
    
    <!-- Copy status notification -->
    <div v-if="copyStatus" class="copy-status" :class="{ 'success': copyStatus.success, 'error': !copyStatus.success }">
      {{ copyStatus.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  mapUrl: {
    type: String,
    default: null
  }
})

// State
const copyStatus = ref(null)

// WMS URL computed property (GetCapabilities)
const wmsUrl = computed(() => {
  if (!props.mapUrl) return ''
  
  // Extract base URL and MAP parameter from the mapserver URL
  const baseUrl = props.mapUrl.split('?')[0] + '?'
  const mapParam = props.mapUrl.includes('map=') ? props.mapUrl.split('map=')[1].split('&')[0] : ''
  
  if (!mapParam) return ''
  
  // Generate WMS GetCapabilities URL
  return `${baseUrl}SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&MAP=${mapParam}`
})

// TMS URL computed property  
const tmsUrl = computed(() => {
  if (!props.mapUrl) return ''
  
  // Extract base URL and MAP parameter from the mapserver URL
  const baseUrl = props.mapUrl.split('?')[0] + '?'
  const mapParam = props.mapUrl.includes('map=') ? props.mapUrl.split('map=')[1].split('&')[0] : ''
  
  if (!mapParam) return ''
  
  // Generate TMS URL with tile placeholders
  return `${baseUrl}MAP=${mapParam}&MODE=tile&TILEMODE=gmap&TILE={x}+{y}+{z}&LAYERS=geotiff_layer`
})


// Methods
async function copyToClipboard(text, label) {
  if (!text) {
    copyStatus.value = { success: false, message: `${label} is not available` }
    setTimeout(() => { copyStatus.value = null }, 3000)
    return
  }
  
  try {
    await navigator.clipboard.writeText(text)
    copyStatus.value = { success: true, message: `${label} copied to clipboard!` }
  } catch (err) {
    // Fallback for older browsers
    try {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      copyStatus.value = { success: true, message: `${label} copied to clipboard!` }
    } catch (fallbackErr) {
      console.error('Failed to copy to clipboard:', fallbackErr)
      copyStatus.value = { success: false, message: `Failed to copy ${label}` }
    }
  }
  
  // Clear status after 3 seconds
  setTimeout(() => { copyStatus.value = null }, 3000)
}
</script>

<style scoped>
/* Map Links Section */
.map-links-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.links-header h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  color: #333;
  font-weight: 600;
}

.links-header p {
  margin: 0 0 1.5rem 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
}

.links-grid {
  display: grid;
  gap: 1.5rem;
}

.link-item {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1.25rem;
  background: #f8f9fa;
  transition: all 0.2s ease;
}

.link-item:hover {
  border-color: #007bff;
  background: #f0f7ff;
}

.link-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.link-main-content {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex: 1;
}

.link-info {
  flex: 1;
}

.link-icon {
  flex-shrink: 0;
  color: #007bff;
  background: white;
  padding: 0.5rem;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.link-info h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.link-info p {
  margin: 0;
  color: #666;
  font-size: 0.85rem;
  line-height: 1.3;
}

.link-url-container {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.link-url {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.8rem;
  color: #333;
  word-break: break-all;
  resize: none;
}

.link-url:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.copy-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 44px;
  height: 44px;
}

.copy-btn:hover {
  background: #0056b3;
  transform: translateY(-1px);
}

.copy-btn:active {
  transform: translateY(0);
}

.link-details {
  font-size: 0.8rem;
  color: #495057;
  background: white;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.link-details div {
  margin-bottom: 0.25rem;
}

.link-details div:last-child {
  margin-bottom: 0;
}

.copy-status {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  text-align: center;
  transition: all 0.3s ease;
}

.copy-status.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.copy-status.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}


/* Type badge styling */
.type {
  display: inline-block;
  background: #6c757d;
  color: white;
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  margin-left: 0.5rem;
  line-height: 1;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .links-grid {
    grid-template-columns: 1fr;
  }
  
  .link-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .link-icon {
    align-self: flex-start;
  }
  
  .copy-btn {
    width: 100%;
    height: auto;
    padding: 0.75rem 1rem;
  }
  
  .link-url-container {
    flex-direction: column;
  }
  
  .link-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .link-main-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
}
</style>
