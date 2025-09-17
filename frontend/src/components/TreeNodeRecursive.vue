<template>
  <div class="tree-node">
    <div 
      class="tree-item"
      :class="{ 
        selected: selectedPath === collection.path,
        disabled: disabledPaths.has(collection.path)
      }"
      :style="{ paddingLeft: level * 20 + 16 + 'px' }"
      @click="handleSelect"
    >
      <!-- Expand/collapse button -->
      <button 
        v-if="collection.hasChildren"
        class="expand-btn"
        @click.stop="handleToggle"
      >
        <svg width="12" height="12" viewBox="0 0 12 12">
          <path 
            :d="isExpanded ? 'M3 5L6 8L9 5' : 'M5 3L8 6L5 9'" 
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
      
      <!-- Collection name and path -->
      <span>{{ collection.name }}</span>
      <span class="path-indicator">(Level {{ level + 1 }})</span>
    </div>
    
    <!-- Child collections (loaded on demand) -->
    <div v-if="isExpanded" class="tree-children">
      <TreeNodeRecursive
        v-for="child in children"
        :key="child.id"
        :collection="child"
        :level="level + 1"
        :selected-path="selectedPath"
        :disabled-paths="disabledPaths"
        :expanded-nodes="expandedNodes"
        :children-cache="childrenCache"
        @select="$emit('select', $event)"
        @toggle="$emit('toggle', $event)"
        @load-children="$emit('load-children', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  collection: { type: Object, required: true },
  level: { type: Number, default: 0 },
  selectedPath: { type: String, default: '' },
  disabledPaths: { type: Set, default: () => new Set() },
  expandedNodes: { type: Set, default: () => new Set() },
  childrenCache: { type: Map, default: () => new Map() }
})

const emit = defineEmits(['select', 'toggle', 'load-children'])

const isExpanded = computed(() => {
  return props.expandedNodes.has(props.collection.path)
})

const children = computed(() => {
  return props.childrenCache.get(props.collection.path) || []
})

const handleSelect = () => {
  if (!props.disabledPaths.has(props.collection.path)) {
    emit('select', props.collection.path)
  }
}

const handleToggle = async () => {
  emit('toggle', props.collection)
  
  if (!isExpanded.value && children.value.length === 0) {
    // Load children
    await emit('load-children', props.collection.path)
  }
}
</script>

<style scoped>
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

.tree-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #eee;
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

.tree-children {
  border-left: 1px solid #ddd;
  margin-left: 8px;
}
</style>
