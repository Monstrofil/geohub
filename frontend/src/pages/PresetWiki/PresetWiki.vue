<template>
  <div class="preset-wiki">
    <div class="wiki-header">
      <h1>{{ $t('presetWiki.title') }}</h1>
      <p class="wiki-description">{{ $t('presetWiki.description') }}</p>
    </div>

    <div class="wiki-content">
      <!-- Loading state -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>{{ $t('presetWiki.loading') }}</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <p>{{ $t('presetWiki.error') }}: {{ error }}</p>
        <button @click="loadPresets" class="retry-btn">{{ $t('presetWiki.retry') }}</button>
      </div>

      <!-- Presets content -->
      <div v-else class="presets-container">
        <!-- Search -->
        <div class="search-bar">
          <div class="search-box">
            <input 
              v-model="searchQuery" 
              :placeholder="$t('presetWiki.searchPlaceholder')"
              class="search-input"
              @keydown.enter="handleSearch"
              @input="handleSearchInput"
            />
            <Icon name="search" class="search-icon" />
          </div>
        </div>

        <!-- Presets grid -->
        <div class="presets-grid">
          <div 
            v-for="preset in filteredPresets" 
            :key="preset.key"
            class="preset-card"
            :tabindex="0"
            role="button"
            :aria-expanded="expandedPresets.has(preset.key)"
            :aria-label="`${$t(`presets.${preset.translationKey}.name`) || preset.name} preset details`"
            @click="togglePresetDetails(preset.key)"
            @keydown.enter="togglePresetDetails(preset.key)"
            @keydown.space.prevent="togglePresetDetails(preset.key)"
          >
            <div class="preset-header">
              <div class="preset-icon" v-html="preset.icon"></div>
              <div class="preset-info">
                <h3 class="preset-name">{{ $t(`presets.${preset.translationKey}.name`) || preset.name }}</h3>
                <p class="preset-description" v-if="preset.description">{{ preset.description }}</p>
                <div class="preset-meta">
                  <span class="field-count">{{ preset.fields.length }} {{ $t('presetWiki.fields') }}</span>
                </div>
              </div>
              <Icon 
                :name="expandedPresets.has(preset.key) ? 'chevron-up' : 'chevron-down'" 
                class="expand-icon"
              />
            </div>

            <!-- Expanded details -->
            <div v-if="expandedPresets.has(preset.key)" class="preset-details" @click.stop>
              <!-- Object types -->
              <div class="detail-section" v-if="preset.object_type">
                <h4>{{ $t('presetWiki.objectTypes') }}</h4>
                <div class="object-types">
                  <span 
                    v-for="type in preset.object_type" 
                    :key="type"
                    class="object-type-tag"
                  >
                    {{ formatObjectType(type) }}
                  </span>
                </div>
              </div>

              <!-- Fields -->
              <div class="detail-section">
                <h4>{{ $t('presetWiki.fieldsList') }}</h4>
                <div class="fields-list">
                  <div 
                    v-for="field in preset.resolvedFields" 
                    :key="field.key"
                    class="field-item"
                  >
                      <div class="field-header">
                        <div class="field-name-section">
                          <span class="field-label">{{ $t(`fields.${field.key}.label`, field.label || field.key) }}</span>
                          <div class="field-key-container">
                            <span class="field-key-label">{{ $t('presetWiki.fieldKey') }}:</span>
                            <span class="field-key">{{ field.key }}</span>
                          </div>
                        </div>
                        <span class="field-type">{{ $t(formatFieldType(field.type)) }}</span>
                      </div>
                    <p v-if="$t(`fields.${field.key}.description`, field.description)" class="field-description">{{ $t(`fields.${field.key}.description`, field.description) }}</p>
                    <div v-if="field.values" class="field-values">
                      <span class="values-label">{{ $t('presetWiki.possibleValues') }}:</span>
                      <div class="values-list">
                        <span 
                          v-for="value in field.values" 
                          :key="value"
                          class="value-tag"
                        >
                          {{ value }}
                        </span>
                        <span v-if="field.values.length > 5" class="more-values">
                          +{{ field.values.length - 5 }} {{ $t('presetWiki.more') }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Required Tags -->
              <div v-if="preset.tags && Object.keys(preset.tags).length > 0" class="detail-section">
                <h4>{{ $t('presetWiki.requiredTags') }}</h4>
                <p>{{ $t('presetWiki.tagsDescription') }}</p>
                <div class="required-tags">
                  <div class="required-tag-item">
                    <code>{{ generateTagsExample(preset.tags) }}</code>
                  </div>
                </div>
              </div>


              <!-- Terms -->
              <div v-if="preset.terms" class="detail-section">
                <h4>{{ $t('presetWiki.searchTerms') }}</h4>
                <div class="terms-list">
                  <span 
                    v-for="term in preset.terms" 
                    :key="term"
                    class="term-tag"
                  >
                    {{ term }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="filteredPresets.length === 0" class="empty-state">
          <Icon name="search" class="empty-icon" />
          <h3>{{ $t('presetWiki.noResults') }}</h3>
          <p>{{ $t('presetWiki.noResultsDescription') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { loadFieldDefinitions, resolveFields } from '../../utils/fieldResolver.js'
import { getAllPresets } from '../../utils/tagMatcher.js'
import Icon from '../../components/Icon.vue'

export default {
  name: 'PresetWiki',
  components: {
    Icon
  },
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const presets = ref([])
    const fieldDefinitions = ref({})
    const searchQuery = ref('')
    const expandedPresets = ref(new Set())

    // Load all presets and field definitions
    const loadPresets = async () => {
      try {
        loading.value = true
        error.value = null

        // Load field definitions
        fieldDefinitions.value = await loadFieldDefinitions()

        // Use the existing getAllPresets function
        const allPresets = getAllPresets()
        const loadedPresets = []

        allPresets.forEach((presetData) => {
          // Extract category from the preset data or use a default
          const category = presetData.category || 'generic'
          const fileName = presetData.translationKey || 'unknown'
          
          // Resolve fields for this preset
          const resolvedFields = resolveFields(presetData.fields || [], fieldDefinitions.value)
          
          loadedPresets.push({
            key: `${category}/${fileName}`,
            category,
            fileName,
            ...presetData,
            resolvedFields
          })
        })

        presets.value = loadedPresets.sort((a, b) => a.name.localeCompare(b.name))
      } catch (err) {
        console.error('Error loading presets:', err)
        error.value = err.message
      } finally {
        loading.value = false
      }
    }

    // Computed properties
    const filteredPresets = computed(() => {
      let filtered = presets.value

      // Filter by search query
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(p => 
          p.name.toLowerCase().includes(query) ||
          (p.description && p.description.toLowerCase().includes(query)) ||
          (p.terms && p.terms.some(term => term.toLowerCase().includes(query))) ||
          p.resolvedFields.some(field => 
            field.label.toLowerCase().includes(query) ||
            field.key.toLowerCase().includes(query)
          )
        )
      }

      return filtered
    })

    // Helper functions
    const formatObjectType = (type) => {
      return type.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    }

    const formatFieldType = (type) => {
      // Use translation for field types
      return getFieldTypeTranslation(type)
    }

    const getFieldTypeTranslation = (type) => {
      const typeMap = {
        'str': 'presetWiki.fieldTypes.str',
        'richtext': 'presetWiki.fieldTypes.richtext',
        'bool': 'presetWiki.fieldTypes.bool',
        'enum': 'presetWiki.fieldTypes.enum',
        'number': 'presetWiki.fieldTypes.number',
        'koatoth': 'presetWiki.fieldTypes.koatoth'
      }
      return typeMap[type] || type
    }

    const getFieldLabel = (fieldKey) => {
      const fieldDef = fieldDefinitions.value[fieldKey]
      return fieldDef?.label || fieldKey.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    }

    const generateTagsExample = (tags) => {
      const tagPairs = Object.entries(tags).map(([key, value]) => `${key}=${value}`)
      return tagPairs.join('\n')
    }


    const togglePresetDetails = (presetKey) => {
      if (expandedPresets.value.has(presetKey)) {
        expandedPresets.value.delete(presetKey)
      } else {
        expandedPresets.value.add(presetKey)
      }
    }

    // Search handling with debouncing
    let searchTimeout = null
    const handleSearchInput = () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
      searchTimeout = setTimeout(() => {
        // Search is handled by computed property
      }, 300)
    }

    const handleSearch = () => {
      // Immediate search on Enter key
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
    }

    // Lifecycle
    onMounted(() => {
      loadPresets()
    })

    return {
      loading,
      error,
      presets,
      searchQuery,
      expandedPresets,
      filteredPresets,
      formatObjectType,
      formatFieldType,
      getFieldLabel,
      generateTagsExample,
      togglePresetDetails,
      handleSearchInput,
      handleSearch,
      loadPresets
    }
  }
}
</script>

<style scoped>
.preset-wiki {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.wiki-header {
  text-align: center;
  margin-bottom: 3rem;
}

.wiki-header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.wiki-description {
  font-size: 1.1rem;
  color: #7f8c8d;
  max-width: 600px;
  margin: 0 auto;
}

.loading-state, .error-state {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.search-bar {
  margin-bottom: 2rem;
}

.search-box {
  position: relative;
  max-width: 400px;
}

.search-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: #3498db;
}

.search-icon {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #7f8c8d;
}


.presets-grid {
  display: grid;
  gap: 1.5rem;
}

.preset-card {
  background: white;
  border: 2px solid #e1e8ed;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
}

.preset-card:hover,
.preset-card:focus {
  border-color: #3498db;
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.1);
}

.preset-card:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

.preset-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.preset-icon {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.preset-info {
  flex: 1;
}

.preset-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 0.5rem 0;
}

.preset-description {
  color: #7f8c8d;
  margin: 0 0 0.75rem 0;
  line-height: 1.4;
}

.preset-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #95a5a6;
}

.expand-icon {
  color: #7f8c8d;
  transition: transform 0.2s ease;
}

.preset-details {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e1e8ed;
  cursor: default;
}

.detail-section {
  margin-bottom: 1.5rem;
}

.detail-section h4 {
  font-size: 1rem;
  font-weight: 600;
  color: #34495e;
  margin: 0 0 0.75rem 0;
}

.object-types, .preview-fields, .terms-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.object-type-tag, .preview-field-tag, .term-tag {
  background: #ecf0f1;
  color: #2c3e50;
  padding: 0.25rem 0.75rem;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 500;
}

.fields-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field-item {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid #3498db;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.field-name-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.field-label {
  font-weight: 600;
  color: #2c3e50;
  font-size: 1rem;
}

.field-key-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.field-key-label {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: 500;
}

.field-key {
  font-size: 0.8rem;
  color: #495057;
  font-family: 'Courier New', monospace;
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  display: inline-block;
  width: fit-content;
  font-weight: 500;
}

.field-type {
  background: #3498db;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.field-description {
  color: #7f8c8d;
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
}

.field-values {
  margin-top: 0.5rem;
}

.values-label {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin-right: 0.5rem;
}

.values-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
}

.value-tag {
  background: #e8f4fd;
  color: #2980b9;
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
}

.more-values {
  color: #7f8c8d;
  font-size: 0.8rem;
  font-style: italic;
}

.tags-description {
  color: #6c757d;
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
  line-height: 1.5;
  background: #f8f9fa;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border-left: 4px solid #3498db;
}

.required-tags {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.required-tag-item {
  background: #2c3e50;
  color: #ecf0f1;
  padding: 1rem;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  overflow-x: auto;
  border: 1px solid rgba(255, 255, 255, 0.1);
  white-space: pre-line;
  cursor: text;
  user-select: text;
}

.required-tag-item code {
  background: none;
  color: inherit;
  padding: 0;
  font-family: inherit;
}

.tags-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tag-item {
  background: #f8f9fa;
  padding: 0.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

@media (max-width: 768px) {
  .preset-wiki {
    padding: 1rem;
  }
  
  .preset-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .preset-meta {
    flex-direction: column;
    gap: 0.25rem;
  }
}
</style>
