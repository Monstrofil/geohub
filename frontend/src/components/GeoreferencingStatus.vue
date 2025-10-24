<template>
  <div v-if="shouldShow" class="georeferencing-status">
    <!-- Probing status -->
    <div v-if="probeLoading" class="probe-status">
      <div class="spinner"></div>
      <h3>{{ $t('fileInfo.checkingCompatibility') }}</h3>
      <p>{{ $t('fileInfo.analyzingGeoreference') }}</p>
    </div>

    <!-- Probe error -->
    <div v-else-if="probeError" class="probe-error">
      <div class="georef-icon">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="30" fill="#dc3545"/>
          <path d="M20 20l24 24M44 20l-24 24" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
        </svg>
      </div>
      <h3>{{ $t('fileInfo.fileAnalysisFailed') }}</h3>
      <p>{{ probeError }}</p>
    </div>

    <!-- File cannot be georeferenced -->
    <div v-else-if="probeResult && !probeResult.can_georeference" class="cannot-georeference">
      <div class="no-preview-message">
        <div class="georef-icon">
          <svg width="64" height="64" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="30" fill="#6c757d"/>
            <path d="M20 20l24 24M44 20l-24 24" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
          </svg>
        </div>
        <h3>Cannot Be Georeferenced</h3>
        <p>{{ probeResult.error || 'This file is not compatible with georeferencing tools.' }}</p>
      </div>
    </div>

    <!-- Regular file that can be converted and georeferenced -->
    <div v-else-if="file.object_type === 'raw_file' && probeResult && probeResult.can_georeference && !isFileGeoreferenced" class="can-georeference">
      <div class="georef-icon">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="30" fill="#28a745"/>
          <path d="M20 32l8 8 16-16" stroke="white" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <h3>Ready for Georeferencing</h3>
      <p>This file can be prepared for georeferencing. We'll convert it to a geo-raster format and then open the georeferencing interface where you can add control points.</p>
      
      <div class="georef-actions">
        <button class="btn btn-success convert-btn" @click="$emit('startConversion')">
          <svg width="24" height="24" viewBox="0 0 24 24">
            <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
          </svg>
          Convert & Start Georeferencing
        </button>
      </div>
      
      <div class="file-info">
        <p><strong>{{ $t('fileInfo.fileDetails') }}</strong> {{ probeResult.image_info?.width }}×{{ probeResult.image_info?.height }} pixels, {{ probeResult.image_info?.bands }} bands</p>
      </div>
    </div>

    <!-- Geo-raster file that needs georeferencing (no conversion needed) -->
    <div v-else-if="file.object_type === 'geo_raster_file' && probeResult && probeResult.can_georeference && !isFileGeoreferenced" class="needs-georeferencing">
      <div class="georef-icon">
        <svg width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="30" fill="#ffc107"/>
          <path d="M32 16v16M32 40h0" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
          <circle cx="32" cy="32" r="2" fill="white"/>
        </svg>
      </div>
      <h3>Georeferencing Required {{ isFileGeoreferenced }} 12 3</h3>
      <p>This geo-raster file is ready for georeferencing. Add control points to georeference it to a map coordinate system.</p>
      
      <div class="georef-actions">
        <button class="btn btn-primary georef-btn" @click="$emit('startGeoreferencing')">
          <svg width="24" height="24" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="12" r="2" fill="currentColor"/>
            <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" stroke-width="2"/>
          </svg>
          Start Georeferencing
        </button>
      </div>
      
      <div class="file-info">
        <p><strong>{{ $t('fileInfo.fileDetails') }}</strong> {{ probeResult.image_info?.width }}×{{ probeResult.image_info?.height }} pixels, {{ probeResult.image_info?.bands }} bands</p>
      </div>
    </div>

    <!-- File is already georeferenced (fallback case) -->
    <div v-else-if="isFileGeoreferenced" class="already-georeferenced">
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
        <h3>Georeferencing Required {{ isFileGeoreferenced }}</h3>
        <p>This raster file needs georeferencing to be displayed on a map. Add control points to georeference it.</p>
      </div>
      
      <div class="georef-actions">
        <button class="btn btn-primary georef-btn" @click="$emit('startGeoreferencing')">
          <svg width="24" height="24" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
            <circle cx="12" cy="12" r="2" fill="currentColor"/>
            <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" stroke-width="2"/>
          </svg>
          Start Georeferencing
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import apiService from '../services/api.js'

const props = defineProps({
  file: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['startConversion', 'startGeoreferencing'])

// Probe state for checking if file can be georeferenced
const probeResult = ref(null)
const probeLoading = ref(false)
const probeError = ref(null)


// Check if file is georeferenced
const isFileGeoreferenced = computed(() => {
  // For geo_raster_file objects, check the is_georeferenced field from the database;
  if (props.file && props.file.object_type === 'geo_raster_file' && props.file.object_details) {
    return props.file.object_details.is_georeferenced === true
  }
  
  // Default to false if no conclusive information
  return false
})

const shouldShow = computed(() => {
  return props.file && !isFileGeoreferenced.value
})

// Probe functions
async function probeFile() {
  if (!props.file?.id) return

  probeLoading.value = true
  probeError.value = null
  
  try {
    const result = await apiService.probeTreeItem(props.file.id)
    probeResult.value = result
  } catch (err) {
    console.error('Failed to probe file:', err)
    probeError.value = err.message || 'Failed to probe file'
  } finally {
    probeLoading.value = false
  }
}

// Watch for file changes and probe when needed
watch(() => props.file, (newFile) => {
  if (newFile && newFile.type === 'file' && !isFileGeoreferenced) {
    // Clear previous probe results
    probeResult.value = null
    probeError.value = null
    // Probe the file in the background
    probeFile()
  }
}, { immediate: true })
</script>

<style scoped>
.georeferencing-status {
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

/* Georeferencing section when in right panel */
.content-sidebar .georeferencing-status {
  padding: 1.5rem;
  margin: 1.5rem 0 0 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Adjust georef icon size for right panel */
.content-sidebar .georef-icon {
  margin-bottom: 1rem;
}

.content-sidebar .georef-icon svg {
  width: 48px;
  height: 48px;
}

/* Adjust text sizing for right panel */
.content-sidebar .georeferencing-status h3 {
  font-size: 1.1rem;
  margin-bottom: 0.75rem;
}

.content-sidebar .georeferencing-status p {
  font-size: 0.9rem;
  line-height: 1.4;
  margin-bottom: 1rem;
}

/* Adjust button sizing for right panel */
.content-sidebar .georef-actions {
  width: 100%;
  display: flex;
  justify-content: center;
}

.content-sidebar .georef-actions .btn {
  width: 100%;
  font-size: 0.9rem;
  padding: 0.75rem 1rem;
}

/* Adjust file info for right panel */
.content-sidebar .file-info {
  margin-top: 1rem;
  font-size: 0.85rem;
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
  padding: 2rem;
}

.no-preview-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
}

.no-preview-note {
  color: #6c757d;
  font-size: 0.9rem;
  font-style: italic;
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
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
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

/* General button styles */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 0.875rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-success {
  background: #28a745;
  color: white;
  border: 1px solid #28a745;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
  border-color: #1e7e34;
}

.btn-primary {
  background: #007bff;
  color: white;
  border: 1px solid #007bff;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
  border-color: #004085;
}
</style>
