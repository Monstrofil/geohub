<template>
  <div v-if="selectedType || (file.tags && Object.keys(file.tags).length > 0)" class="unified-properties-section">
    <h3>{{ $t('fileInfo.objectInformation') }}</h3>
    
    <!-- Object type display -->
    <div v-if="selectedType" class="object-type-display">
      <div class="preset-icon-container">
        <span v-html="selectedType.icon" class="preset-icon"></span>
      </div>
      <div class="object-type-info">
        <div class="object-type-name">{{ $t(`presets.${selectedType.translationKey}.name`, selectedType.name) }}</div>
        <div class="object-type-description">
          {{ selectedType.description || $t('fileInfo.descriptionNotSet') }}
        </div>
      </div>
    </div>

    <!-- Object properties using field definitions -->
    <div v-if="file.tags && Object.keys(file.tags).length > 0" class="properties-section">
      <h4>{{ $t('fileInfo.properties') }}</h4>
      <div v-if="selectedFields.length > 0" class="properties-grid">
        <div v-for="field in selectedFields" :key="field.key" class="property-item">
          <span class="property-label">{{ $t(`fields.${field.key}.label`, field.label || field.key) }}:</span>
          <span class="property-value">{{ file.tags[field.key] || $t('fileInfo.notSet') }}</span>
        </div>
      </div>
      <div v-else class="tags-grid">
        <div v-for="(value, key) in file.tags" :key="key" class="tag-item">
          <span class="tag-key">{{ key }}:</span>
          <span class="tag-value">{{ value }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { resolveFields } from '../../../utils/fieldResolver.js'
import { matchTagsToPreset, getAllPresets } from '../../../utils/tagMatcher.js'
import { loadFieldDefinitions } from '../../../utils/fieldResolver.js'

const props = defineProps({
  file: {
    type: Object,
    required: true
  }
})

// Local state for field definitions and presets
const allPresets = ref([])
const allFieldDefinitions = ref({})
const selectedType = ref(null)

// Resolve field keys to full field definitions
const selectedFields = computed(() => {
  if (!selectedType.value || !selectedType.value.fields) {
    return []
  }
  return resolveFields(selectedType.value.fields, allFieldDefinitions.value)
})

// Initialize data and match preset
onMounted(async () => {
  // Load all field definitions and presets
  allPresets.value = getAllPresets()
  allFieldDefinitions.value = await loadFieldDefinitions()
  
  // Match preset based on file tags
  if (props.file && props.file.tags) {
    selectedType.value = matchTagsToPreset(props.file.tags, allPresets.value, props.file.object_type)
  }
})
</script>

<style scoped>
.unified-properties-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  top: 1rem;
}

.unified-properties-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
}

.object-type-display {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.preset-icon-container {
  flex-shrink: 0;
}

.preset-icon {
  display: block;
  width: 32px;
  height: 32px;
}

.object-type-info {
  flex: 1;
}

.object-type-name {
  font-weight: 600;
  font-size: 1.1rem;
  color: #212529;
  margin-bottom: 0.25rem;
}

.object-type-description {
  font-size: 0.9rem;
  color: #6c757d;
}

.properties-section {
  margin-top: 1.5rem;
}

.properties-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.properties-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.property-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.property-label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.property-value {
  color: #666;
  word-break: break-word;
  font-size: 1rem;
  flex-grow: 1;
  text-align: right;
}

.tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.tag-item {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.tag-key {
  font-weight: 500;
  color: #495057;
  min-width: 80px;
}

.tag-value {
  color: #333;
  word-break: break-word;
}
</style>
