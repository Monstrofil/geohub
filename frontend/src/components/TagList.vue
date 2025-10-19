<template>
  <div class="section tag-editor">
    <h3>
      <span>Поля ({{ fields.length }})</span>
      <span v-if="currentFile" class="file-info"> - {{ currentFile.name }}</span>
    </h3>
    <div class="disclosure-wrap">
      <form class="pure-form pure-form-stacked">
        <!-- Preset-defined fields -->
        <div v-for="(field, idx) in fields" :key="field.name" class="field-row" :class="{ 'related-field': isRelatedField(field.name) }">
          <label :for="'field-' + field.name" class="field-label">
            <span class="label-text">{{ field.label || field.name }}</span>
            <span v-if="isRelatedField(field.name)" class="related-badge">автоматично</span>
            <button v-if="!isRelatedField(field.name)" type="button" class="remove-btn" title="вилучити" @click="clearField(field.name)">
              <svg width="16" height="16" viewBox="0 0 16 16">
                <line x1="4" y1="4" x2="12" y2="12" stroke="#c00" stroke-width="2"/>
                <line x1="12" y1="4" x2="4" y2="12" stroke="#c00" stroke-width="2"/>
              </svg>
            </button>
          </label>
          <FieldRenderer 
            :field="field" 
            :model-value="values[field.name]" 
            :disabled="isRelatedField(field.name)"
            @update:model-value="value => setField(field.name, value)"
            @update:related-fields="handleRelatedFields"
          />
          <div v-if="isRelatedField(field.name)" class="related-note">
            Це поле автоматично заповнюється при виборі {{ getRelatedFieldSource(field.name) }}
          </div>
        </div>

        <!-- Additional fields -->
        <div v-for="(moreField, idx) in activeMoreFields" :key="moreField.name" class="field-row additional-field">
          <label :for="'field-' + moreField.name" class="field-label">
            <span class="label-text">{{ moreField.label || moreField.name }}</span>
            <span class="additional-badge">додатково</span>
            <button type="button" class="remove-btn" title="вилучити" @click="clearField(moreField.name)">
              <svg width="16" height="16" viewBox="0 0 16 16">
                <line x1="4" y1="4" x2="12" y2="12" stroke="#c00" stroke-width="2"/>
                <line x1="12" y1="4" x2="4" y2="12" stroke="#c00" stroke-width="2"/>
              </svg>
            </button>
          </label>
          <FieldRenderer 
            :field="moreField" 
            :model-value="values[moreField.name]" 
            @update:model-value="value => setField(moreField.name, value)"
            @update:related-fields="handleRelatedFields"
          />
        </div>

        <!-- Add field button -->
        <div v-if="availableMoreFields.length > 0" class="add-field-section">
          <button type="button" class="add-field-btn" @click="showMoreFieldsDropdown = !showMoreFieldsDropdown">
            <svg width="16" height="16" viewBox="0 0 16 16">
              <line x1="8" y1="2" x2="8" y2="14" stroke="#007bff" stroke-width="2"/>
              <line x1="2" y1="8" x2="14" y2="8" stroke="#007bff" stroke-width="2"/>
            </svg>
            Додати поле
          </button>
          
          <!-- Dropdown for selecting additional fields -->
          <div v-if="showMoreFieldsDropdown" class="field-dropdown">
            <div class="dropdown-header">
              <span>Виберіть додаткове поле:</span>
              <button type="button" class="close-btn" @click="showMoreFieldsDropdown = false">×</button>
            </div>
            <div class="dropdown-options">
              <button 
                v-for="field in availableMoreFields" 
                :key="field.key" 
                type="button"
                class="dropdown-option"
                @click="addMoreField(field.key)"
              >
                <span class="option-label">{{ field.label || field.key }}</span>
                <span class="option-type">{{ getFieldTypeLabel(field.type) }}</span>
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>

  <!-- Raw Tag Editor for Experienced Users -->
  <div class="section raw-tag-editor">
    <h3>
      <button class="toggle-btn" :class="{ expanded: showRawEditor }" @click="showRawEditor = !showRawEditor" title="згорнути">
        <svg class="toggle-icon" width="12" height="12" viewBox="0 0 12 12">
          <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="toggle-text">Теґи ({{ allTagsCount }})</span>
      </button>
    </h3>
    
    <div v-if="showRawEditor" class="disclosure-wrap">
      <textarea 
        class="raw-textarea" 
        v-model="rawTagText"
        @input="parseRawTags"
        autocomplete="new-password" 
        autocorrect="off" 
        autocapitalize="off" 
        spellcheck="false" 
        placeholder="ключ=значення"
        style="height: 200px;"
      ></textarea>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch, nextTick, ref, computed } from 'vue'
import { resolveFields } from '../utils/fieldResolver.js'
import FieldRenderer from './fields/FieldRenderer.vue'
import apiService from '../services/api.js'

const props = defineProps({
  fields: {
    type: Array,
    default: () => []
  },
  currentFile: {
    type: Object,
    default: null
  },
  selectedType: {
    type: Object,
    default: null
  },
  allFieldDefinitions: {
    type: Object,
    default: () => ({})
  },
  changeTracker: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['tags-updated'])

const values = reactive({})
const showMoreFieldsDropdown = ref(false)
const addedMoreFields = ref(new Set())

// Raw tag editor state
const showRawEditor = ref(false)
const rawTagText = ref('')
const isEditingRawTags = ref(false) // Flag to prevent watcher interference

// Computed properties
const allTagsCount = computed(() => {
  return Object.keys(values).filter(key => values[key] !== null && values[key] !== '').length
})

const allMoreFields = computed(() => {
  if (!props.selectedType || !props.selectedType.moreFields) {
    return []
  }
  return resolveFields(props.selectedType.moreFields, props.allFieldDefinitions)
})

const activeMoreFields = computed(() => {
  return allMoreFields.value.filter(field => {
    const value = values[field.name]
    const hasValue = value !== null && value !== '' && value !== undefined
    const wasAdded = addedMoreFields.value.has(field.name)
    return hasValue || wasAdded
  })
})

const availableMoreFields = computed(() => {
  if (!props.selectedType || !props.selectedType.moreFields) {
    return []
  }
  
  const usedFieldNames = new Set([
    ...props.fields.map(f => f.name),
    ...activeMoreFields.value.map(f => f.name)
  ])
  
  return props.selectedType.moreFields
    .filter(fieldKey => !usedFieldNames.has(fieldKey))
    .map(fieldKey => {
      const fieldDef = props.allFieldDefinitions[fieldKey]
      return {
        key: fieldKey,
        label: fieldDef?.label || formatFieldLabel(fieldKey),
        type: fieldDef?.type || 'text'
      }
    })
})

// Utility functions
function formatFieldLabel(key) {
  return key
    .split('/')
    .map(part => 
      part
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    )
    .join(' / ')
}

function getFieldTypeLabel(fieldType) {
  const typeLabels = {
    'text': 'текст',
    'number': 'число',
    'check': 'так/ні',
    'combo': 'вибір',
    'textarea': 'текст'
  }
  return typeLabels[fieldType] || 'текст'
}

// Raw tag editor functions
function updateRawTagText() {
  if (isEditingRawTags.value) return // Don't update if user is editing
  
  const tags = Object.entries(values)
    .filter(([key, value]) => value !== null && value !== '')
    .map(([key, value]) => `${key}=${value}`)
    .join('\n')
  rawTagText.value = tags
}

function parseRawTags() {
  isEditingRawTags.value = true
  
  const lines = rawTagText.value.split('\n')
  const newValues = {}
  
  lines.forEach(line => {
    const trimmed = line.trim()
    if (trimmed && trimmed.includes('=')) {
      const [key, ...valueParts] = trimmed.split('=')
      const value = valueParts.join('=')
      if (key.trim()) {
        newValues[key.trim()] = value.trim()
      }
    }
  })
  
  // Clear all existing values first
  Object.keys(values).forEach(key => {
    values[key] = null
  })
  
  // Set new values from parsed text
  Object.entries(newValues).forEach(([key, value]) => {
    values[key] = value
  })
  
  // Reset the flag after a short delay to allow the change to propagate
  setTimeout(() => {
    isEditingRawTags.value = false
  }, 100)
  
  emitTagsUpdate()
}

// Field management functions
function clearField(name) {
  values[name] = null
  if (props.selectedType?.moreFields?.includes(name)) {
    addedMoreFields.value.delete(name)
  }
  updateRawTagText()
  emitTagsUpdate()
}

function setField(name, value) {
  values[name] = value === '' ? null : value
  updateRawTagText()
  emitTagsUpdate()
}

function handleRelatedFields({ fieldName, relatedData }) {
  // Find the field definition to get relatedFields mapping
  const fieldDef = props.allFieldDefinitions[fieldName]
  if (!fieldDef || !fieldDef.relatedFields) {
    return
  }
  
  // Update related fields based on the mapping
  Object.entries(fieldDef.relatedFields).forEach(([sourceKey, targetFieldName]) => {
    if (relatedData[sourceKey] !== undefined) {
      setField(targetFieldName, relatedData[sourceKey])
    }
  })
}

function isRelatedField(fieldName) {
  // Only check fields that are actually present in the current preset
  const currentFieldNames = props.fields.map(f => f.name)
  
  // Check if this field is controlled by any other field's relatedFields
  return currentFieldNames.some(sourceFieldName => {
    const fieldDef = props.allFieldDefinitions[sourceFieldName]
    if (!fieldDef || !fieldDef.relatedFields) {
      return false
    }
    
    // Check if this field is mapped by the source field
    const isMapped = Object.values(fieldDef.relatedFields).includes(fieldName)
    
    // Only disable if the source field has a value
    if (isMapped) {
      const sourceValue = values[sourceFieldName]
      return sourceValue !== null && sourceValue !== '' && sourceValue !== undefined
    }
    
    return false
  })
}

function getRelatedFieldSource(fieldName) {
  // Find which field controls this related field (only from current preset)
  const currentFieldNames = props.fields.map(f => f.name)
  
  for (const sourceFieldName of currentFieldNames) {
    const fieldDef = props.allFieldDefinitions[sourceFieldName]
    if (fieldDef && fieldDef.relatedFields && Object.values(fieldDef.relatedFields).includes(fieldName)) {
      return fieldDef.label || sourceFieldName
    }
  }
  return 'іншого поля'
}

function addMoreField(fieldKey) {
  values[fieldKey] = ''
  addedMoreFields.value.add(fieldKey)
  showMoreFieldsDropdown.value = false
  updateRawTagText()
  emitTagsUpdate()
}

async function emitTagsUpdate() {
  const tags = {}
  Object.entries(values).forEach(([key, value]) => {
    if (value !== null && value !== '') {
      tags[key] = value
    }
  })
  
  // Emit the tags update event for local state management
  emit('tags-updated', tags)
  
  // Add change to tracker instead of making immediate API calls
  if (props.currentFile) {
    props.changeTracker.addChange({
      type: 'tags',
      fileId: props.currentFile.id,
      data: tags
    })
  }
}

// Watchers
watch(
  () => props.fields,
  (fields) => {
    if (isEditingRawTags.value) return // Don't interfere if user is editing raw tags
    
    fields.forEach(field => {
      if (!(field.name in values)) {
        values[field.name] = null
      }
    })
  },
  { immediate: true }
)

watch(
  () => props.currentFile,
  (file) => {
    if (isEditingRawTags.value) return // Don't interfere if user is editing raw tags
    
    if (file && file.tags) {
      // Clear all existing values first
      Object.keys(values).forEach(key => {
        values[key] = null
      })
      
      // Don't clear addedMoreFields - let user-added fields persist
      // addedMoreFields.value.clear()
      
      // Set new values from file tags
      Object.entries(file.tags).forEach(([key, value]) => {
        values[key] = value
        if (props.selectedType?.moreFields?.includes(key)) {
          addedMoreFields.value.add(key)
        }
      })
      
      updateRawTagText()
    }
  },
  { immediate: true, deep: true }
)

// Also watch for changes in the file's tags specifically
watch(
  () => props.currentFile?.tags,
  (newTags) => {
    if (isEditingRawTags.value) return // Don't interfere if user is editing raw tags
    
    if (newTags) {
      // Clear all existing values first
      Object.keys(values).forEach(key => {
        values[key] = null
      })
      
      // Don't clear addedMoreFields - let user-added fields persist
      // addedMoreFields.value.clear()
      
      // Set new values from file tags
      Object.entries(newTags).forEach(([key, value]) => {
        values[key] = value
        if (props.selectedType?.moreFields?.includes(key)) {
          addedMoreFields.value.add(key)
        }
      })
      
      updateRawTagText()
    }
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
.section {
  padding: 1rem;
  border-right: 1px solid #eee;
  min-width: 260px;
  background: #f8f9fa;
}

.tag-editor {
  border-bottom: 1px solid #eee;
}

.raw-tag-editor {
  background: #f5f5f5;
}

.file-info {
  font-size: 0.9em;
  color: #666;
  font-weight: normal;
}

.disclosure-wrap {
  margin-top: 0.5rem;
}

/* Field styling */
.field-row {
  margin-bottom: 1rem;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.related-field {
  opacity: 0.7;
  pointer-events: none;
}

.related-field .field-label {
  color: #666;
}

.related-field input,
.related-field select,
.related-field textarea {
  background-color: #f8f9fa !important;
  color: #495057 !important;
  border-color: #dee2e6 !important;
}

.related-field input:disabled,
.related-field select:disabled,
.related-field textarea:disabled {
  background-color: #f8f9fa !important;
  color: #495057 !important;
  opacity: 1 !important;
}

.related-badge {
  font-size: 0.7em;
  background: #6c757d;
  color: white;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  margin-left: 0.5rem;
}

.related-note {
  font-size: 0.8em;
  color: #666;
  font-style: italic;
  margin-top: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: #f8f9fa;
  border-radius: 3px;
  border-left: 3px solid #6c757d;
}

.label-text {
  flex: 1;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.1rem;
  color: #c00;
  opacity: 0.7;
  transition: opacity 0.15s;
}

.remove-btn:hover {
  opacity: 1;
}

.additional-field {
  border-left: 3px solid #007bff;
  padding-left: 0.5rem;
  background: #f0f8ff;
}

.additional-badge {
  font-size: 0.7em;
  background: #007bff;
  color: white;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  margin-left: 0.5rem;
}

/* Add field section */
.add-field-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
  position: relative;
}

.add-field-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: 1px dashed #007bff;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  color: #007bff;
  cursor: pointer;
  width: 100%;
  transition: all 0.15s;
}

.add-field-btn:hover {
  background: #f0f8ff;
  border-color: #0056b3;
  color: #0056b3;
}

.field-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 1000;
  margin-top: 0.5rem;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
  font-size: 0.9em;
  font-weight: bold;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2em;
  color: #666;
}

.dropdown-options {
  max-height: 200px;
  overflow-y: auto;
}

.dropdown-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0.5rem 1rem;
  background: none;
  border: none;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}

.dropdown-option:hover {
  background: #f8f9fa;
}

.dropdown-option:last-child {
  border-bottom: none;
}

.option-label {
  font-weight: 500;
}

.option-type {
  font-size: 0.8em;
  color: #666;
  font-style: italic;
}

/* Raw tag editor */
.toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  padding: 0.5rem 0;
  width: 100%;
  text-align: left;
}

.toggle-btn.expanded .toggle-icon {
  transform: rotate(180deg);
}

.toggle-icon {
  transition: transform 0.2s;
}

.toggle-text {
  font-weight: 500;
}

.raw-textarea {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem;
  font-family: monospace;
  font-size: 0.9em;
  resize: vertical;
}
</style> 