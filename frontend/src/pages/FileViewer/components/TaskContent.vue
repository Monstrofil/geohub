<template>
  <div class="task-content">
    <!-- Modal Mode: Prominent Progress Display -->
    <div v-if="isModal" class="modal-progress">
      <div class="progress-header">
        <h4>Background Task in Progress</h4>
        <p>This file is currently being processed. Please wait for the task to complete.</p>
      </div>
      
      <div class="progress-container">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: progress + '%' }"
            :class="progressClass"
          />
        </div>
        <div class="progress-text">{{ progress }}%</div>
      </div>
      
      <div class="status-text" :class="statusClass">
        {{ status }}
      </div>

      <!-- Task Details -->
      <div v-if="task" class="task-details">
        <div v-if="task.created_at" class="detail-item">
          <span class="label">Started:</span>
          <span class="value">{{ formatDate(task.created_at) }}</span>
        </div>
        <div v-if="isError && task.task_id" class="detail-item">
          <span class="label">Reference:</span>
          <span class="value task-id">{{ task.task_id.slice(0, 8) }}...</span>
        </div>
      </div>
    </div>

    <!-- Inline Mode: Compact Progress Display -->
    <div v-else class="inline-progress">
      <div class="progress-container">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: progress + '%' }"
            :class="progressClass"
          />
        </div>
        <div class="progress-text">{{ progress }}%</div>
      </div>
      
      <div class="status-text" :class="statusClass">
        {{ status }}
      </div>

      <!-- Task Details -->
      <div v-if="task" class="task-details">
        <div v-if="task.created_at" class="detail-item">
          <span class="label">Started:</span>
          <span class="value">{{ formatDate(task.created_at) }}</span>
        </div>
        <div v-if="isError && task.task_id" class="detail-item">
          <span class="label">Reference:</span>
          <span class="value task-id">{{ task.task_id.slice(0, 8) }}...</span>
        </div>
      </div>
    </div>

    <!-- Error Details -->
    <div v-if="isError && error" class="error-section">
      <div class="error-header">
        <Icon name="error" />
        <span>Task Failed</span>
      </div>
      <div class="error-message">{{ error }}</div>
    </div>

    <!-- Success Message -->
    <div v-if="isComplete && !isError" class="success-section">
      <div class="success-header">
        <Icon name="success" />
        <span>Task Completed Successfully</span>
      </div>
    </div>

    <!-- Inline Actions -->
    <div v-if="!isModal" class="task-actions">
      <button 
        class="btn btn-secondary btn-sm" 
        @click="handleRefresh"
        :disabled="refreshing"
      >
        <Icon :name="refreshing ? 'spinner' : 'refresh'" :class="{ 'spinning': refreshing }" />
        Refresh
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Icon from '../../../components/Icon.vue'

const props = defineProps({
  task: {
    type: Object,
    required: true
  },
  isModal: {
    type: Boolean,
    default: false
  },
  refreshing: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['refresh'])

// Computed properties
const progress = computed(() => props.task?.progress || 0)
const status = computed(() => {
  const rawStatus = props.task?.status || 'Unknown'
  
  // Make status more user-friendly
  const statusMap = {
    'PENDING': 'Waiting to start...',
    'PROGRESS': 'Processing...',
    'SUCCESS': 'Completed successfully',
    'FAILURE': 'Failed to process',
    'ERROR': 'An error occurred',
    'RETRY': 'Retrying...',
    'REVOKED': 'Cancelled'
  }
  
  return statusMap[rawStatus] || rawStatus
})
const state = computed(() => props.task?.state || 'UNKNOWN')
const error = computed(() => props.task?.error)

const isError = computed(() => ['FAILURE', 'ERROR'].includes(state.value))
const isComplete = computed(() => state.value === 'SUCCESS')

// CSS classes
const progressClass = computed(() => ({
  'error': isError.value,
  'success': isComplete.value
}))

const statusClass = computed(() => ({
  'error': isError.value,
  'success': isComplete.value
}))

const stateClass = computed(() => state.value.toLowerCase())

// Methods
const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString()
}

const handleRefresh = () => {
  emit('refresh', props.task.task_id)
}
</script>

<style scoped>
/* CSS Custom Properties for this component */
.task-content {
  --color-primary-hover: #2563eb;
  --color-success: #28a745;
  --color-primary: #3b82f6;
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
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.2);
  
  --transition-fast: 0.15s ease;
  --transition-normal: 0.2s ease;
  --transition-slow: 0.3s ease;

  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* Progress Styles */
.modal-progress {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  text-align: center;
}

.inline-progress {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.progress-header h4 {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.progress-header p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.4;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.modal-progress .progress-container {
  flex-direction: column;
  gap: var(--spacing-sm);
}

.progress-bar {
  flex: 1;
  height: var(--progress-height);
  background-color: var(--color-bg-secondary);
  border-radius: var(--border-radius-sm);
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.modal-progress .progress-bar {
  width: 100%;
  max-width: 400px;
  height: 12px;
}

.progress-fill {
  height: 100%;
  background: var(--gradient-primary);
  transition: width 0.3s ease;
  border-radius: var(--border-radius-sm);
}

.progress-fill.error {
  background: var(--gradient-error);
}

.progress-fill.success {
  background: var(--gradient-success);
}

.progress-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary);
  min-width: 40px;
  text-align: right;
}

.modal-progress .progress-text {
  font-size: 1.5rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.status-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.modal-progress .status-text {
  font-size: 1rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

.status-text.error {
  color: var(--color-error);
}

.status-text.success {
  color: var(--color-success);
}

/* Task Details */
.task-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background-color: var(--color-bg-tertiary);
  border-radius: var(--border-radius-sm);
  border: 1px solid var(--color-border);
}

.modal-progress .task-details {
  padding: var(--spacing-md);
  text-align: left;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.value {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
}

.value.task-id {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.value.pending {
  color: var(--color-warning);
}

.value.progress {
  color: var(--color-primary);
}

.value.success {
  color: var(--color-success);
}

.value.failure,
.value.error {
  color: var(--color-error);
}

/* Status Sections */
.error-section,
.success-section {
  padding: var(--spacing-sm);
  border-radius: var(--border-radius-sm);
}

.error-section {
  background-color: var(--color-bg-error);
  border: 1px solid var(--color-border-error);
}

.success-section {
  background-color: var(--color-bg-success);
  border: 1px solid var(--color-border-success);
}

.error-header,
.success-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xs);
  font-size: 0.875rem;
  font-weight: 500;
}

.error-header {
  color: var(--color-error);
}

.success-header {
  color: var(--color-success);
}

.error-message {
  font-size: 0.875rem;
  color: var(--color-text-error);
  font-family: var(--font-mono);
  background-color: white;
  padding: var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  border: 1px solid var(--color-border-error);
}

/* Actions */
.task-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-xs);
}

/* Button Styles */
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid transparent;
  border-radius: var(--border-radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: white;
  color: var(--color-text-primary);
  border-color: var(--color-border);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--color-bg-secondary);
  border-color: var(--color-border-hover);
}

.btn-sm {
  padding: 6px 12px;
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
</style>
