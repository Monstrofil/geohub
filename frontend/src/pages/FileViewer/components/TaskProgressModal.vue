<template>
  <VueFinalModal
    :click-to-close="false"
    :esc-to-close="false"
    classes="task-progress-modal-wrapper"
    content-class="pure-g"
    overlay-transition="vfm-fade"
    content-transition="vfm-scale"
    @closed="handleClose"
  >

    <div class="pure-u-1 pure-u-md-1-4 pure-u-lg-1-3"></div>
      <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-1-3">
        <div class="task-progress-modal">
      <div class="modal-header">
        <h3>{{ title }}</h3>
      </div>
      
      <div class="modal-body">
        <TaskContent 
          v-if="currentTask"
          :task="currentTask" 
          :is-modal="true" 
          :refreshing="isRefreshing"
          @refresh="handleRefresh"
        />
        <div v-else class="loading-task">
          <div class="spinner"></div>
          <p>Starting task...</p>
        </div>
      </div>
      
      <div class="modal-footer">
        <button 
          v-if="isComplete || isError" 
          class="btn btn-primary" 
          @click="handleClose"
        >
          {{ isError ? 'Close' : 'Continue' }}
        </button>
      </div>
        </div>
      </div>
  </VueFinalModal>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { VueFinalModal } from 'vue-final-modal'
import TaskContent from './TaskContent.vue'
import apiService from '../../../services/api.js'

// Props
const props = defineProps({
  title: {
    type: String,
    default: 'Processing Task'
  },
  itemId: {
    type: String,
    default: null
  },
  taskId: {
    type: String,
    default: null // If provided, monitor existing task instead of starting new one
  },
  isModal: {
    type: Boolean,
    default: true
  },
  canCancel: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['close', 'complete', 'error', 'cancel', 'refresh'])

// State
const currentTask = ref(null)
const isRefreshing = ref(false)
const pollingInterval = ref(null)

// Computed
const isComplete = computed(() => currentTask.value?.state === 'SUCCESS')
const isError = computed(() => ['FAILURE', 'ERROR'].includes(currentTask.value?.state))

// Methods
const startTask = async () => {
  console.log('[TaskProgressModal] startTask called with itemId:', props.itemId, 'taskId:', props.taskId)
  
  // If we already have a taskId, fetch its status to get the real created_at time
  if (props.taskId) {
    console.log('[TaskProgressModal] Monitoring existing task:', props.taskId)
    try {
      // Fetch the actual task status to get the real created_at timestamp
      const status = await apiService.getTaskStatus(props.taskId)
      console.log('[TaskProgressModal] Existing task status:', status)
      
      currentTask.value = {
        task_id: props.taskId,
        progress: status.progress || 0,
        status: status.status || 'Processing...',
        state: status.state || 'PROGRESS',
        error: status.error || null,
        created_at: status.created_at || new Date().toISOString()
      }
      
      // Start polling
      startPolling(props.taskId)
    } catch (error) {
      console.error('[TaskProgressModal] Failed to fetch existing task status:', error)
      // Fallback to minimal task info and start polling anyway
      currentTask.value = {
        task_id: props.taskId,
        progress: 0,
        status: 'Loading task status...',
        state: 'PROGRESS',
        error: null,
        created_at: new Date().toISOString()
      }
      startPolling(props.taskId)
    }
    return
  }
  
  if (!props.itemId) {
    console.error('[TaskProgressModal] No itemId or taskId provided, cannot start/monitor task')
    return
  }
  
  try {
    // Start conversion task
    console.log('[TaskProgressModal] Calling convertToGeoRaster for itemId:', props.itemId)
    const response = await apiService.convertToGeoRaster(props.itemId)
    console.log('[TaskProgressModal] Conversion API response:', response)
    
    currentTask.value = {
      task_id: response.task_id,
      progress: response.progress || 0,
      status: response.status || 'Starting conversion...',
      state: response.state || 'PENDING',
      error: response.error || null,
      created_at: response.created_at || new Date().toISOString()
    }
    
    console.log('[TaskProgressModal] currentTask set to:', currentTask.value)
    
    // Start polling
    startPolling(response.task_id)
  } catch (error) {
    console.error('[TaskProgressModal] Failed to start task:', error)
    currentTask.value = {
      task_id: null,
      progress: 0,
      status: 'Failed to start task',
      state: 'ERROR',
      error: error.message,
      created_at: new Date().toISOString()
    }
  }
}

const startPolling = (taskId) => {
  console.log('[TaskProgressModal] Starting polling for taskId:', taskId)
  
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }
  
  pollingInterval.value = setInterval(async () => {
    try {
      const status = await apiService.getTaskStatus(taskId)
      console.log('[TaskProgressModal] Poll result:', status)
      
      currentTask.value = {
        task_id: taskId,
        progress: status.progress || 0,
        status: status.status || 'Processing...',
        state: status.state || 'PROGRESS',
        error: status.error,
        // Use created_at from API, fall back to existing value, then current time
        created_at: status.created_at || currentTask.value?.created_at || new Date().toISOString()
      }
      
      // Stop polling if task is complete
      if (status.state === 'SUCCESS' || status.state === 'FAILURE' || status.state === 'ERROR') {
        console.log('[TaskProgressModal] Task completed with state:', status.state)
        stopPolling()
      }
    } catch (error) {
      console.error('[TaskProgressModal] Failed to get task status:', error)
      currentTask.value.error = error.message
    }
  }, 2000) // Poll every 2 seconds
  
  console.log('[TaskProgressModal] Polling interval set:', pollingInterval.value)
}

const stopPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

const handleClose = () => {
  stopPolling()
  emit('close')
}

const handleRefresh = async () => {
  if (currentTask.value?.task_id) {
    isRefreshing.value = true
    try {
      const status = await apiService.getTaskStatus(currentTask.value.task_id)
      currentTask.value = {
        ...currentTask.value,
        progress: status.progress || 0,
        status: status.status || 'Processing...',
        state: status.state || 'PROGRESS',
        error: status.error,
        // Preserve or update created_at from API
        created_at: status.created_at || currentTask.value.created_at
      }
    } catch (error) {
      console.error('Failed to refresh task status:', error)
    } finally {
      isRefreshing.value = false
    }
  }
}

// Watchers
watch(isComplete, (newValue) => {
  if (newValue) {
    emit('complete', currentTask.value?.task_id)
  }
})

watch(isError, (newValue) => {
  if (newValue) {
    emit('error', currentTask.value?.error)
  }
})

watch([() => props.itemId, () => props.taskId], ([itemId, taskId], [oldItemId, oldTaskId]) => {
  console.log('[TaskProgressModal] Watcher triggered:', { itemId, taskId, oldItemId, oldTaskId, isModal: props.isModal })
  
  if ((itemId || taskId) && props.isModal) {
    console.log('[TaskProgressModal] Starting/monitoring task - itemId:', itemId, 'taskId:', taskId)
    startTask()
  }
}, { immediate: true })

// Lifecycle
onUnmounted(() => {
  console.log('[TaskProgressModal] Component unmounting, stopping polling')
  stopPolling()
})
</script>

<style scoped>

.task-progress-modal-wrapper {
  align-items: center;
}

/* Modal Styles */
.task-progress-modal {
  /* CSS Custom Properties for this component */
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --color-success: #28a745;
  --color-error: #dc3545;
  --color-warning: #f59e0b;
  
  --color-text-primary: #111827;
  --color-text-secondary: #6b7280;
  --color-text-tertiary: #9ca3af;
  --color-text-error: #7f1d1d;
  
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f8fafc;
  --color-bg-tertiary: #f9fafb;
  --color-bg-error: #fef2f2;
  --color-bg-success: #f0fdf4;
  
  --color-border: #e5e7eb;
  --color-border-hover: #9ca3af;
  --color-border-error: #fecaca;
  --color-border-success: #bbf7d0;
  
  --gradient-primary: linear-gradient(90deg, var(--color-primary), #1d4ed8);
  --gradient-error: linear-gradient(90deg, var(--color-error), #b91c1c);
  --gradient-success: linear-gradient(90deg, var(--color-success), #1e7e34);
  
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  
  --font-mono: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  
  --progress-height: 8px;
  --modal-z-index: 1000;
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.2);
  
  --transition-fast: 0.15s ease;
  --transition-normal: 0.2s ease;
  --transition-slow: 0.3s ease;
  
  background: var(--color-bg-primary);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-height: 100%;
  overflow-y: auto;

  margin-top: 10vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover:not(:disabled) {
  background-color: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.close-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-body {
  padding: var(--spacing-lg);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

/* Loading spinner */
.loading-task {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px;
}

.loading-task .spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-task p {
  color: #6b7280;
  font-size: 0.875rem;
}

/* Button Styles */
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid transparent;
  border-radius: var(--border-radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  text-decoration: none;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-secondary {
  background-color: var(--color-bg-primary);
  color: var(--color-text-primary);
  border-color: var(--color-border);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--color-bg-secondary);
  border-color: var(--color-border-hover);
}

.btn-sm {
  padding: 6px var(--spacing-sm);
  font-size: 0.75rem;
}

/* Animations */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}


/* Fade Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-normal);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}


/* Dark mode support (if needed) */
@media (prefers-color-scheme: dark) {
  :root {
    --color-text-primary: #f9fafb;
    --color-text-secondary: #d1d5db;
    --color-text-tertiary: #9ca3af;
    
    --color-bg-primary: #1f2937;
    --color-bg-secondary: #111827;
    --color-bg-tertiary: #374151;
    
    --color-border: #374151;
    --color-border-hover: #6b7280;
  }
}
</style>