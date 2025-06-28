import { ref, computed } from 'vue'

export function useChangeTracker() {
  const pendingChanges = ref({}) // Store only the latest state per object
  const isCommitting = ref(false)
  
  const hasChanges = computed(() => Object.keys(pendingChanges.value).length > 0)
  const changeCount = computed(() => Object.keys(pendingChanges.value).length)
  const canUndo = computed(() => false) // No undo/redo for now since we only store final state
  const canRedo = computed(() => false)
  
  function addChange(change) {
    // Store only the latest state for each object
    const key = `${change.type}-${change.fileId}`
    pendingChanges.value[key] = {
      id: Date.now(),
      timestamp: new Date(),
      ...change
    }
  }
  
  function undo() {
    // No undo functionality for now
    return null
  }
  
  function redo() {
    // No redo functionality for now
    return null
  }
  
  function clearChanges() {
    pendingChanges.value = {}
  }
  
  async function commitChanges(commitFunction) {
    if (!hasChanges.value || isCommitting.value) return
    
    isCommitting.value = true
    
    try {
      // Apply only the latest state for each object
      for (const change of Object.values(pendingChanges.value)) {
        await commitFunction(change)
      }
      
      // Clear changes after successful commit
      clearChanges()
      
      return { success: true }
    } catch (error) {
      console.error('Commit failed:', error)
      return { success: false, error }
    } finally {
      isCommitting.value = false
    }
  }
  
  function getPendingChanges() {
    return Object.values(pendingChanges.value)
  }
  
  return {
    // State
    pendingChanges,
    isCommitting,
    
    // Computed
    hasChanges,
    changeCount,
    canUndo,
    canRedo,
    
    // Methods
    addChange,
    undo,
    redo,
    clearChanges,
    commitChanges,
    getPendingChanges
  }
} 