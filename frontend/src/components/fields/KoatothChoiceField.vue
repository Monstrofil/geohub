<template>
  <div class="koatoth-field">
    <div class="input-container">
      <input 
        :id="fieldId" 
        type="text"
        class="pure-input-1"
        :value="displayValue"
        :placeholder="field.placeholder || 'Search locations...'"
        @input="handleInput"
        @focus="showDropdown = true"
        @blur="handleBlur"
        :disabled="disabled"
        autocomplete="off"
      />
      <div v-if="selectedOption" class="decoded-value">
        {{ selectedOption.name }} ({{ selectedOption.type }})
      </div>
    </div>
    
    <div v-if="showDropdown && filteredOptions.length > 0" class="dropdown">
      <div 
        v-for="option in filteredOptions" 
        :key="option.id"
        class="dropdown-item"
        @mousedown="selectOption(option)"
      >
        <div class="option-id">{{ option.id }}</div>
        <div class="option-name-row">
          <span class="option-name">{{ option.name }}</span>
          <span class="option-type">{{ option.type }}</span>
        </div>
        <div v-if="option.parents" class="option-parents">{{ option.parents }}</div>
      </div>
    </div>
    
    <div v-if="showDropdown && searchTerm && filteredOptions.length === 0" class="no-results">
      No locations found
    </div>
    
    <div v-if="field.description" class="field-description">
      {{ $t(`fields.${field.key}.description`, field.description) }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
  field: {
    type: Object,
    required: true
  },
  modelValue: {
    type: String,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'update:relatedFields'])

const fieldId = `field-${props.field.name}`
const koatothData = ref([])
const searchTerm = ref('')
const showDropdown = ref(false)
const selectedOption = ref(null)

const displayValue = computed(() => {
  if (selectedOption.value) {
    return selectedOption.value.id
  }
  return searchTerm.value
})

const filteredOptions = computed(() => {
  if (!searchTerm.value || searchTerm.value.length < 2) {
    return []
  }
  
  const term = searchTerm.value.toLowerCase()
  const results = koatothData.value.filter(item => 
    item.name.toLowerCase().includes(term) ||
    item.type.toLowerCase().includes(term) ||
    item.id.toLowerCase().includes(term) ||
    item.parents.toLowerCase().includes(term)
  )
  
  // Sort by relevance: exact matches first, then by match type priority
  return results.sort((a, b) => {
    const aScore = calculateRelevanceScore(a, term)
    const bScore = calculateRelevanceScore(b, term)
    return bScore - aScore // Higher score first
  }).slice(0, 50)
})

function calculateRelevanceScore(item, term) {
  let score = 0
  const name = item.name.toLowerCase()
  const type = item.type.toLowerCase()
  const id = item.id.toLowerCase()
  const parents = item.parents.toLowerCase()
  
  // Exact name match gets highest priority
  if (name === term) {
    score += 1000
  }
  // Name starts with search term
  else if (name.startsWith(term)) {
    score += 500
  }
  // Name contains search term
  else if (name.includes(term)) {
    score += 300
  }
  
  // ID exact match
  if (id === term) {
    score += 800
  }
  // ID starts with search term
  else if (id.startsWith(term)) {
    score += 400
  }
  // ID contains search term
  else if (id.includes(term)) {
    score += 200
  }
  
  // Type match (lower priority)
  if (type.includes(term)) {
    score += 100
  }
  
  // Parents match (lowest priority)
  if (parents.includes(term)) {
    score += 50
  }
  
  return score
}

onMounted(async () => {
  try {
    const koatothModule = await import('../../data/static/koatoth.json')
    koatothData.value = koatothModule.default || koatothModule
    
    // Initialize selectedOption if modelValue is already set
    if (props.modelValue) {
      const existingOption = koatothData.value.find(item => item.id === props.modelValue)
      if (existingOption) {
        selectedOption.value = existingOption
        searchTerm.value = existingOption.id
      }
    }
  } catch (error) {
    console.error('Error loading koatoth data:', error)
    koatothData.value = []
  }
})

// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
  if (newValue && koatothData.value.length > 0) {
    const existingOption = koatothData.value.find(item => item.id === newValue)
    if (existingOption) {
      selectedOption.value = existingOption
      searchTerm.value = existingOption.id
    } else {
      // If the ID doesn't exist in our data, clear the selection
      selectedOption.value = null
      searchTerm.value = newValue || ''
    }
  } else if (!newValue) {
    // Clear selection when modelValue is null/empty
    selectedOption.value = null
    searchTerm.value = ''
  }
}, { immediate: true })

function handleInput(event) {
  if (props.disabled) return
  searchTerm.value = event.target.value
  selectedOption.value = null
  showDropdown.value = true
  emit('update:modelValue', null)
}

function selectOption(option) {
  if (props.disabled) return
  selectedOption.value = option
  searchTerm.value = option.id
  showDropdown.value = false
  emit('update:modelValue', option.id)
  
  // Emit related field updates
  emit('update:relatedFields', {
    name: option.name,
    location: option.parents || option.name
  })
}

function handleBlur() {
  // Delay hiding dropdown to allow for option selection
  setTimeout(() => {
    showDropdown.value = false
  }, 150)
}
</script>

<style scoped>
.koatoth-field {
  position: relative;
  width: 100%;
}

.input-container {
  position: relative;
}

.koatoth-field input {
  width: 100%;
  font-size: 14px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
}

.koatoth-field input:focus {
  outline: none;
  border-color: #0078d4;
  box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.2);
}

.decoded-value {
  background-color: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-top: none;
  border-radius: 0 0 4px 4px;
  padding: 6px 12px;
  font-size: 12px;
  color: #666;
  margin-top: -1px;
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-top: none;
  border-radius: 0 0 4px 4px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.dropdown-item {
  padding: 12px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.option-id {
  font-size: 11px;
  color: #666;
  font-family: monospace;
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 500;
  margin-bottom: 2px;
}

.option-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.option-name {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.option-type {
  font-size: 12px;
  color: #0078d4;
  background-color: #e3f2fd;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.option-parents {
  font-size: 11px;
  color: #888;
  line-height: 1.3;
  font-style: italic;
  margin-top: 2px;
}

.no-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-top: none;
  border-radius: 0 0 4px 4px;
  padding: 12px;
  color: #666;
  font-style: italic;
  z-index: 1000;
}

/* Custom scrollbar */
.dropdown::-webkit-scrollbar {
  width: 6px;
}

.dropdown::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.dropdown::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.dropdown::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.field-description {
  font-size: 0.85em;
  color: #666;
  margin-top: 0.25rem;
  line-height: 1.3;
}
</style>