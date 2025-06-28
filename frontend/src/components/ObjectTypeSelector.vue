<template>
  <div class="section section-feature-type">
    <h3>
      <span>Тип об'єкта</span>
    </h3>
    <div class="disclosure-wrap disclosure-wrap-feature_type preset-list-item">
      <div class="preset-list-button-wrap">
        <button class="preset-list-button preset-reset" @click="openMenu = true">
          <div class="preset-icon-container">
            <span v-if="currentType" v-html="currentType.icon" class="preset-icon"></span>
          </div>
          <div class="label">
            <div class="label-inner">
              <div class="namepart">{{ currentType ? currentType.name : '' }}</div>
            </div>
          </div>
        </button>
        <div class="accessory-buttons">
          <button class="tag-reference-button" title="інформація">
            <svg width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" stroke="#888" stroke-width="2" fill="none"/><text x="8" y="12" text-anchor="middle" font-size="10" fill="#888">i</text></svg>
          </button>
        </div>
      </div>
    </div>
    <div v-if="openMenu" class="type-search-area">
      <div class="type-modal-header">
        <h2>Пошук об'єктів</h2>
        <button class="close-btn" @click="closeMenu">×</button>
      </div>
      <div class="type-modal-search">
        <input type="search" v-model="search" placeholder="Пошук" class="pure-input-1" />
      </div>
      <div class="type-modal-list">
        <button v-for="(type, idx) in filteredTypes" :key="type.name" class="type-modal-item" @click="selectType(idx)">
          <span v-html="type.icon" class="preset-icon"></span>
          <span>{{ type.name }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { loadFieldDefinitions } from '../utils/fieldResolver.js'
import { matchTagsToPreset } from '../utils/tagMatcher.js'

const props = defineProps({
  modelValue: Object,
  selectedType: Object,
  currentFile: Object // Add currentFile prop to detect tag changes
})
const emit = defineEmits(['update:selectedType', 'menu-open', 'type-changed'])

const types = ref([])
const currentType = ref(null)
const selectedIndex = ref(0)
const openMenu = ref(false)
const search = ref('')

// Dynamically import all presets
const presetModules = import.meta.glob('../data/presets/*/*.json', { eager: true })

onMounted(async () => {
  // Load all preset JSONs into the types array
  types.value = Object.values(presetModules)
  
  // Load field definitions (for future use if needed)
  await loadFieldDefinitions()
  
  if (types.value.length > 0) {
    // Set current type to the first one as default, but allow override from props
    currentType.value = props.selectedType || types.value[0]
    selectedIndex.value = types.value.findIndex(t => t.name === currentType.value?.name) || 0
    emit('update:selectedType', currentType.value)
  }
})

// Watch for changes in selectedType prop
watch(() => props.selectedType, (newType) => {
  if (newType) {
    currentType.value = newType
  }
}, { immediate: true })

// Watch for changes in currentFile tags and auto-detect type
watch(() => props.currentFile?.tags, (newTags) => {
  if (newTags && types.value.length > 0) {
    const matchedPreset = matchTagsToPreset(newTags, types.value)
    if (matchedPreset && matchedPreset !== currentType.value) {
      currentType.value = matchedPreset
      emit('update:selectedType', currentType.value)
      emit('type-changed', matchedPreset)
    }
  }
}, { immediate: true })

function selectType(idx) {
  const newType = filteredTypes.value[idx]
  currentType.value = newType
  emit('update:selectedType', currentType.value)
  emit('type-changed', newType)
  openMenu.value = false
  emit('menu-open', false)
}

function closeMenu() {
  openMenu.value = false
  emit('menu-open', false)
}

watch(openMenu, (val) => {
  emit('menu-open', val)
})

const filteredTypes = computed(() => {
  if (!search.value) return types.value
  return types.value.filter(t => t.name.toLowerCase().includes(search.value.toLowerCase()))
})
</script>

<style scoped>
.section-feature-type {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}
.preset-list-button-wrap {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.preset-icon-container {
  margin-right: 0.5rem;
}
.preset-icon {
  display: inline-block;
  vertical-align: middle;
}
.label-inner {
  font-weight: bold;
  color: #333;
}
.pure-input-1-2 {
  min-width: 120px;
  max-width: 200px;
}
.accessory-buttons {
  margin-left: auto;
}
.preset-list-button {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  min-width: 160px;
  position: relative;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.type-search-area {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 1rem 0.5rem 1rem 0.5rem;
  margin-top: 1rem;
}
.type-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.type-modal-search {
  margin-bottom: 1rem;
}
.type-modal-list {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.type-modal-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #eee;
  border-radius: 4px;
  background: #fafbfc;
  cursor: pointer;
  transition: background 0.15s;
}
.type-modal-item:hover {
  background: #e6f0fa;
}
.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #888;
}
</style> 