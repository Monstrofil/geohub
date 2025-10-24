<template>
  <VueFinalModal
    :click-to-close="true"
    :esc-to-close="true"
    classes="move-modal-wrapper"
    content-class="pure-g"
    overlay-transition="vfm-fade"
    content-transition="vfm-scale"
    @closed="handleClose"
  >
    <div class="pure-u-1 pure-u-md-1-4 pure-u-lg-1-3"></div>
    <div class="pure-u-1 pure-u-md-1-2 pure-u-lg-1-3">
      <div class="move-modal">
        <div class="move-modal-header">
          <h3>Move "{{ itemName }}"</h3>
          <button class="close-btn" @click="close">×</button>
        </div>
      
      <div class="move-modal-body">
        <div class="current-location">
          <strong>Current location:</strong> {{ currentPath || 'Root' }}
        </div>
        
        <div class="destination-section">
          <label>Choose destination:</label>
          <div class="tree-browser">
            <!-- Root option -->
            <div 
              class="tree-item root-item"
              :class="{ selected: selectedPath === 'root', disabled: currentPath === 'root' || currentPath === '' }"
              @click="selectPath('root')"
            >
              <div class="tree-item-icon">
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <path d="M2 2h12v12H2z" fill="none" stroke="#666" stroke-width="1"/>
                  <path d="M2 2h4l2 2h6" fill="none" stroke="#666" stroke-width="1"/>
                </svg>
              </div>
              <span>Root</span>
            </div>
            
            <!-- Loading state -->
            <div v-if="loading" class="loading-collections">
              <div class="spinner"></div>
              Loading collections...
            </div>
            
            <!-- Collections tree -->
            <div v-else class="collections-tree">
              <div 
                v-for="collection in rootCollections" 
                :key="collection.id"
                class="tree-node"
              >
                <!-- Root collection item -->
                <div 
                  class="tree-item"
                  :class="{ 
                    selected: selectedPath === collection.path,
                    disabled: disabledPaths.has(collection.path)
                  }"
                  @click="selectPath(collection.path)"
                >
                  <!-- Expand/collapse button -->
                  <button 
                    v-if="collection.hasChildren"
                    class="expand-btn"
                    @click.stop="toggleNode(collection)"
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12">
                      <path 
                        :d="expandedNodes.has(collection.path) ? 'M3 5L6 8L9 5' : 'M5 3L8 6L5 9'" 
                        fill="none" 
                        stroke="#666" 
                        stroke-width="1.5"
                      />
                    </svg>
                  </button>
                  <div v-else class="expand-spacer"></div>
                  
                  <!-- Folder icon -->
                  <div class="tree-item-icon">
                    <svg width="16" height="16" viewBox="0 0 16 16">
                      <path d="M2 4h12v8H2z" fill="#ffe082" stroke="#ffb300" stroke-width="1"/>
                      <path d="M2 4l2-2h4l2 2" fill="#ffe082" stroke="#ffb300" stroke-width="1"/>
                    </svg>
                  </div>
                  
                  <span>{{ collection.name }}</span>
                  <span class="path-indicator">(Level 1)</span>
                </div>
                
                <!-- Child collections (loaded on demand) -->
                <div v-if="expandedNodes.has(collection.path)" class="tree-children">
                  <TreeNodeRecursive
                    v-for="child in childrenCache.get(collection.path) || []"
                    :key="child.id"
                    :collection="child"
                    :level="1"
                    :selected-path="selectedPath"
                    :disabled-paths="disabledPaths"
                    :expanded-nodes="expandedNodes"
                    :children-cache="childrenCache"
                    @select="selectPath"
                    @toggle="toggleNode"
                    @load-children="loadChildren"
                  />
                </div>
              </div>
            </div>
            
            <!-- No collections message -->
            <div v-if="!loading && availableCollections.length === 0" class="no-collections">
              No other collections available
            </div>
          </div>
        </div>
      </div>
      
      <div class="move-modal-footer">
        <button class="btn btn-secondary" @click="close">Cancel</button>
        <button 
          class="btn btn-primary" 
          :disabled="!selectedPath || selectedPath === currentPath || isMoving"
          @click="confirmMove"
        >
          <span v-if="isMoving" class="button-spinner"></span>
          {{ isMoving ? 'Moving...' : 'Move Here' }}
        </button>
      </div>
      </div>
    </div>
  </VueFinalModal>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { VueFinalModal } from 'vue-final-modal'
import apiService from '../../services/api.js'
import TreeNodeRecursive from './TreeNodeRecursive.vue'

const props = defineProps({
  itemId: { type: String, required: false },
  itemName: { type: String, required: false },
  itemType: { type: String, required: false }, // 'file' or 'collection'
  currentPath: { type: String, required: false }
})

const emit = defineEmits(['close', 'moved'])

// State
const loading = ref(false)
const isMoving = ref(false)
const selectedPath = ref('')
const availableCollections = ref([])
const rootCollections = ref([])
const expandedNodes = ref(new Set())
const childrenCache = ref(new Map())

// Computed
const currentPathFormatted = computed(() => {
  if (!props.currentPath || props.currentPath === 'root') return 'Root'
  return props.currentPath.split('.').slice(1).map((_, i) => `Collection ${i + 1}`).join(' > ')
})

const disabledPaths = computed(() => {
  const disabled = new Set()
  
  // Disable current location
  if (props.currentPath) {
    disabled.add(props.currentPath)
  }
  
  // If moving a collection, disable its descendants to prevent circular moves
  if (props.itemType === 'collection' && props.currentPath) {
    availableCollections.value.forEach(collection => {
      if (collection.path.startsWith(props.currentPath + '.')) {
        disabled.add(collection.path)
      }
    })
  }
  
  return disabled
})

// Methods
const loadCollections = async () => {
  loading.value = true
  try {
    // Load only root level collections initially
    const response = await apiService.getCollections('root', 0, 1000)
    const collections = response.collections || []
    
    rootCollections.value = collections
    availableCollections.value = [...collections]
    
    // Check if root collections have children (for expand/collapse icons)
    for (const collection of collections) {
      try {
        const childResponse = await apiService.getCollections(collection.path, 0, 1)
        collection.hasChildren = (childResponse.collections?.length || 0) > 0
      } catch (error) {
        collection.hasChildren = false
      }
    }
  } catch (error) {
    console.error('Failed to load collections:', error)
    rootCollections.value = []
    availableCollections.value = []
  } finally {
    loading.value = false
  }
}

const loadChildren = async (parentPath) => {
  // Check cache first
  if (childrenCache.value.has(parentPath)) {
    return childrenCache.value.get(parentPath)
  }
  
  try {
    const response = await apiService.getCollections(parentPath, 0, 1000)
    const children = response.collections || []
    
    // Check if children have their own children
    for (const child of children) {
      try {
        const grandchildResponse = await apiService.getCollections(child.path, 0, 1)
        child.hasChildren = (grandchildResponse.collections?.length || 0) > 0
      } catch (error) {
        child.hasChildren = false
      }
    }
    
    // Cache the children
    childrenCache.value.set(parentPath, children)
    
    // Add to availableCollections for disabled path checking
    availableCollections.value.push(...children)
    
    return children
  } catch (error) {
    console.error('Failed to load children for', parentPath, error)
    return []
  }
}

const toggleNode = async (collection) => {
  const path = collection.path
  
  if (expandedNodes.value.has(path)) {
    expandedNodes.value.delete(path)
  } else {
    expandedNodes.value.add(path)
    // Load children if not already loaded
    if (!childrenCache.value.has(path)) {
      await loadChildren(path)
    }
  }
}

const isDisabled = (path) => {
  // Disable current location
  if (path === props.currentPath) return true
  
  // If moving a collection, disable its descendants to prevent circular moves
  if (props.itemType === 'collection' && props.currentPath) {
    return path.startsWith(props.currentPath + '.')
  }
  
  return false
}

const selectPath = (path) => {
  if (isDisabled(path)) return
  selectedPath.value = path
}

const getIndentationLevel = (path) => {
  if (!path || path === 'root') return 0
  const parts = path.split('.')
  return Math.max(0, parts.length - 1) // -1 because root is level 0
}

const formatPath = (path) => {
  if (!path || path === 'root') return ''
  const parts = path.split('.')
  if (parts.length <= 1) return ''
  return `(Level ${parts.length - 1})`
}

const confirmMove = async () => {
  if (!selectedPath.value || !props.itemId) return
  
  isMoving.value = true
  try {
    await apiService.updateTreeItem(props.itemId, {
      parent_path: selectedPath.value
    })
    
    emit('moved', {
      itemId: props.itemId,
      newPath: selectedPath.value
    })
    
    close()
  } catch (error) {
    console.error('Failed to move item:', error)
    alert(`Failed to move item: ${error.message}`)
  } finally {
    isMoving.value = false
  }
}

const close = () => {
  selectedPath.value = ''
  expandedNodes.value.clear()
  childrenCache.value.clear()
  emit('close')
}

const handleClose = () => {
  close()
}

// Load collections when component mounts
loadCollections()
</script>


<style scoped>
.move-modal-wrapper {
  align-items: center;
}

.move-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.move-modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.move-modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: #f0f0f0;
}

.move-modal-body {
  padding: 1.5rem;
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.current-location {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  color: #666;
  font-size: 0.9rem;
}

.destination-section label {
  display: block;
  margin-bottom: 1rem;
  font-weight: 600;
  color: #333;
}

.tree-browser {
  border: 1px solid #ddd;
  border-radius: 6px;
  max-height: 300px;
  overflow-y: auto;
  background: #fafafa;
}

.tree-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #eee;
}

.tree-item:last-child {
  border-bottom: none;
}

.tree-item:hover:not(.disabled) {
  background: #e3f2fd;
}

.tree-item.selected {
  background: #2196f3;
  color: white;
}

.tree-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f5f5f5;
}

.tree-item-icon {
  margin-right: 0.75rem;
  display: flex;
  align-items: center;
}

.tree-item span {
  flex: 1;
}

.path-indicator {
  font-size: 0.8rem;
  color: #999;
  margin-left: 0.5rem;
}

.tree-item.selected .path-indicator {
  color: rgba(255, 255, 255, 0.8);
}

.expand-btn {
  background: none;
  border: none;
  padding: 2px;
  margin-right: 4px;
  cursor: pointer;
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
}

.expand-btn:hover {
  background: #f0f0f0;
}

.expand-spacer {
  width: 20px;
  height: 16px;
}

.tree-children {
  border-left: 1px solid #ddd;
  margin-left: 8px;
}

.root-item {
  font-weight: 600;
  background: #f0f0f0;
}

.root-item.selected {
  background: #2196f3;
  color: white;
}

.loading-collections {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #666;
  gap: 0.5rem;
}

.no-collections {
  padding: 2rem;
  text-align: center;
  color: #999;
  font-style: italic;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #ddd;
  border-top: 2px solid #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.move-modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn {
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn-primary {
  background: #2196f3;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1976d2;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-spinner {
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
