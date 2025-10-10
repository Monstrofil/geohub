import { ref, computed, onUnmounted } from 'vue'
import apiService from '../services/api.js'

/**
 * Composable for managing background tasks
 * Provides reactive state and methods for task monitoring
 */
export function useBackgroundTasks() {
  const activeTasks = ref(new Map())
  const taskPollingIntervals = ref(new Map())

  /**
   * Start monitoring a background task
   * @param {string} taskId - The task ID to monitor
   * @param {Object} options - Configuration options
   * @returns {Object} Reactive task state
   */
  function startTaskMonitoring(taskId, options = {}) {
    const {
      onProgress = () => {},
      onComplete = () => {},
      onError = () => {},
      pollInterval = 2000, // 2 seconds
      maxPollingTime = 300000 // 5 minutes
    } = options

    // Initialize task state
    const taskState = ref({
      id: taskId,
      state: 'PENDING',
      status: 'Task is waiting to be processed',
      progress: 0,
      result: null,
      error: null,
      isActive: true
    })

    // Store task state
    activeTasks.value.set(taskId, taskState)

    // Start polling
    const startTime = Date.now()
    const poll = async () => {
      try {
        const status = await apiService.getTaskStatus(taskId)
        
        // Update task state
        taskState.value.state = status.state
        taskState.value.status = status.status
        taskState.value.progress = status.progress || 0
        taskState.value.result = status.result
        taskState.value.error = status.error

        // Call progress callback
        onProgress(taskState.value)

        // Check if task is complete
        if (status.state === 'SUCCESS') {
          taskState.value.isActive = false
          onComplete(taskState.value)
          stopTaskMonitoring(taskId)
          return
        } else if (status.state === 'FAILURE') {
          taskState.value.isActive = false
          onError(taskState.value)
          stopTaskMonitoring(taskId)
          return
        }

        // Check if we've exceeded max polling time
        if (Date.now() - startTime > maxPollingTime) {
          taskState.value.isActive = false
          taskState.value.error = 'Task monitoring timeout'
          onError(taskState.value)
          stopTaskMonitoring(taskId)
          return
        }

        // Continue polling if task is still active
        if (taskState.value.isActive) {
          const intervalId = setTimeout(poll, pollInterval)
          taskPollingIntervals.value.set(taskId, intervalId)
        }

      } catch (error) {
        console.error('Error monitoring task:', error)
        taskState.value.isActive = false
        taskState.value.error = error.message || 'Failed to monitor task'
        onError(taskState.value)
        stopTaskMonitoring(taskId)
      }
    }

    // Start initial poll
    poll()

    return taskState
  }

  /**
   * Stop monitoring a task
   * @param {string} taskId - The task ID to stop monitoring
   */
  function stopTaskMonitoring(taskId) {
    // Clear polling interval
    const intervalId = taskPollingIntervals.value.get(taskId)
    if (intervalId) {
      clearTimeout(intervalId)
      taskPollingIntervals.value.delete(taskId)
    }

    // Mark task as inactive
    const taskState = activeTasks.value.get(taskId)
    if (taskState) {
      taskState.value.isActive = false
    }
  }

  /**
   * Cancel a background task
   * @param {string} taskId - The task ID to cancel
   * @returns {Promise<Object>} Cancellation result
   */
  async function cancelTask(taskId) {
    try {
      const result = await apiService.cancelTask(taskId)
      stopTaskMonitoring(taskId)
      return result
    } catch (error) {
      console.error('Error cancelling task:', error)
      throw error
    }
  }

  /**
   * Get the current state of a task
   * @param {string} taskId - The task ID
   * @returns {Object|null} Task state or null if not found
   */
  function getTaskState(taskId) {
    return activeTasks.value.get(taskId)?.value || null
  }

  /**
   * Check if a task is currently being monitored
   * @param {string} taskId - The task ID
   * @returns {boolean} True if task is being monitored
   */
  function isTaskActive(taskId) {
    const taskState = activeTasks.value.get(taskId)
    return taskState?.value?.isActive || false
  }

  /**
   * Get all active tasks
   * @returns {Array} Array of active task states
   */
  function getActiveTasks() {
    return Array.from(activeTasks.value.values())
      .map(taskState => taskState.value)
      .filter(task => task.isActive)
  }

  /**
   * Stop monitoring all tasks
   */
  function stopAllTaskMonitoring() {
    for (const taskId of activeTasks.value.keys()) {
      stopTaskMonitoring(taskId)
    }
  }

  // Cleanup on unmount
  onUnmounted(() => {
    stopAllTaskMonitoring()
  })

  return {
    activeTasks,
    startTaskMonitoring,
    stopTaskMonitoring,
    cancelTask,
    getTaskState,
    isTaskActive,
    getActiveTasks,
    stopAllTaskMonitoring
  }
}

/**
 * Composable specifically for geo-raster conversion tasks
 */
export function useGeoRasterConversion() {
  const { startTaskMonitoring, stopTaskMonitoring, cancelTask } = useBackgroundTasks()
  
  const conversionTasks = ref(new Map())

  /**
   * Start a geo-raster conversion task
   * @param {string} itemId - The tree item ID to convert
   * @param {Object} options - Configuration options
   * @returns {Promise<Object>} Task state
   */
  async function startConversion(itemId, options = {}) {
    try {
      // Start the conversion task
      const taskResponse = await apiService.convertToGeoRaster(itemId)
      const taskId = taskResponse.task_id

      // Start monitoring the task
      const taskState = startTaskMonitoring(taskId, {
        onProgress: (state) => {
          console.log(`Conversion progress: ${state.progress}% - ${state.status}`)
          options.onProgress?.(state)
        },
        onComplete: (state) => {
          console.log('Conversion completed successfully')
          conversionTasks.value.delete(itemId)
          options.onComplete?.(state)
        },
        onError: (state) => {
          console.error('Conversion failed:', state.error)
          conversionTasks.value.delete(itemId)
          options.onError?.(state)
        },
        ...options
      })

      // Store the task state
      conversionTasks.value.set(itemId, taskState)

      return taskState
    } catch (error) {
      console.error('Failed to start conversion:', error)
      throw error
    }
  }

  /**
   * Cancel a conversion task
   * @param {string} itemId - The tree item ID
   * @returns {Promise<Object>} Cancellation result
   */
  async function cancelConversion(itemId) {
    const taskState = conversionTasks.value.get(itemId)
    if (taskState && taskState.value.isActive) {
      const result = await cancelTask(taskState.value.id)
      conversionTasks.value.delete(itemId)
      return result
    }
    throw new Error('No active conversion task found for this item')
  }

  /**
   * Get the conversion status for an item
   * @param {string} itemId - The tree item ID
   * @returns {Object|null} Conversion task state or null
   */
  function getConversionStatus(itemId) {
    return conversionTasks.value.get(itemId)?.value || null
  }

  /**
   * Check if an item is currently being converted
   * @param {string} itemId - The tree item ID
   * @returns {boolean} True if conversion is in progress
   */
  function isConverting(itemId) {
    const taskState = conversionTasks.value.get(itemId)
    return taskState?.value?.isActive || false
  }

  /**
   * Get a computed property for checking if any conversion is active
   * @returns {Object} Computed property that returns true if any conversion is active
   */
  function getIsConvertingComputed() {
    return computed(() => {
      return Array.from(conversionTasks.value.values())
        .some(taskState => taskState.value?.isActive)
    })
  }

  return {
    conversionTasks,
    startConversion,
    cancelConversion,
    getConversionStatus,
    isConverting,
    getIsConvertingComputed
  }
}

/**
 * Composable specifically for georeferencing tasks
 */
export function useGeoreferencing() {
  const { startTaskMonitoring, stopTaskMonitoring, cancelTask } = useBackgroundTasks()
  
  const georeferencingTasks = ref(new Map())

  /**
   * Start a georeferencing task
   * @param {string} fileId - The file ID to georeference
   * @param {Object} request - Georeferencing request data
   * @param {Object} options - Configuration options
   * @returns {Promise<Object>} Task state
   */
  async function startGeoreferencing(fileId, request, options = {}) {
    try {
      // Start the georeferencing task
      const taskResponse = await apiService.applyGeoreferencing(fileId, request)
      const taskId = taskResponse.task_id

      // Start monitoring the task
      const taskState = startTaskMonitoring(taskId, {
        onProgress: (state) => {
          console.log(`Georeferencing progress: ${state.progress}% - ${state.status}`)
          options.onProgress?.(state)
        },
        onComplete: (state) => {
          console.log('Georeferencing completed successfully')
          georeferencingTasks.value.delete(fileId)
          options.onComplete?.(state)
        },
        onError: (state) => {
          console.error('Georeferencing failed:', state.error)
          georeferencingTasks.value.delete(fileId)
          options.onError?.(state)
        },
        ...options
      })

      // Store the task state
      georeferencingTasks.value.set(fileId, taskState)

      return taskState
    } catch (error) {
      console.error('Failed to start georeferencing:', error)
      throw error
    }
  }

  /**
   * Cancel a georeferencing task
   * @param {string} fileId - The file ID
   * @returns {Promise<Object>} Cancellation result
   */
  async function cancelGeoreferencing(fileId) {
    const taskState = georeferencingTasks.value.get(fileId)
    if (taskState && taskState.value.isActive) {
      const result = await cancelTask(taskState.value.id)
      georeferencingTasks.value.delete(fileId)
      return result
    }
    throw new Error('No active georeferencing task found for this file')
  }

  /**
   * Get the georeferencing status for a file
   * @param {string} fileId - The file ID
   * @returns {Object|null} Georeferencing task state or null
   */
  function getGeoreferencingStatus(fileId) {
    return georeferencingTasks.value.get(fileId)?.value || null
  }

  /**
   * Check if a file is currently being georeferenced
   * @param {string} fileId - The file ID
   * @returns {boolean} True if georeferencing is in progress
   */
  function isGeoreferencing(fileId) {
    const taskState = georeferencingTasks.value.get(fileId)
    return taskState?.value?.isActive || false
  }

  /**
   * Get a computed property for checking if any georeferencing is active
   * @returns {Object} Computed property that returns true if any georeferencing is active
   */
  function getIsGeoreferencingComputed() {
    return computed(() => {
      return Array.from(georeferencingTasks.value.values())
        .some(taskState => taskState.value?.isActive)
    })
  }

  return {
    georeferencingTasks,
    startGeoreferencing,
    cancelGeoreferencing,
    getGeoreferencingStatus,
    isGeoreferencing,
    getIsGeoreferencingComputed
  }
}
