<template>
  <div class="collection-details">
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading collection details...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <!-- Collection details -->
    <div v-else-if="collection" class="collection-content">
      <!-- Unified Object Type and Properties section -->
      <div class="unified-properties-section">
        <div class="section-header">
          <h3>Collection Information</h3>
          <button 
            v-if="collection.id" 
            class="edit-btn" 
            @click="editCollection"
            title="Edit collection"
          >
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path d="M11 1L15 5L5 15H1V11L11 1Z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M8 4L12 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Edit
          </button>
        </div>
        
        <!-- Object type display -->
        <div v-if="selectedType" class="object-type-display">
          <div class="preset-icon-container">
            <span v-html="selectedType.icon" class="preset-icon"></span>
          </div>
          <div class="object-type-info">
            <div class="object-type-name">{{ selectedType.name }}</div>
            <div class="object-type-description">
              Collection matched based on tags and properties
            </div>
          </div>
        </div>

        <!-- Object properties using field definitions -->
        <div v-if="collection.tags && Object.keys(collection.tags).length > 0" class="properties-section">
          <h4>Properties</h4>
          <div v-if="selectedFields.length > 0" class="properties-grid">
            <div v-for="field in selectedFields" :key="field.key || field.name" class="property-item">
              <span class="property-label">{{ field.label || field.key || field.name }}:</span>
              <div class="property-value">
                <span class="field-display" :class="getFieldDisplayClass(field)">
                  {{ formatFieldValue(field, collection.tags[field.key || field.name]) }}
                </span>
              </div>
            </div>
          </div>
          <!-- Show other tags that aren't defined in the preset -->
          <div v-if="otherTags && Object.keys(otherTags).length > 0" class="other-tags-section">
            <h5>Other Tags</h5>
            <div class="tags-grid">
              <div v-for="(value, key) in otherTags" :key="key" class="tag-item">
                <span class="tag-key">{{ key }}:</span>
                <span class="tag-value">{{ value }}</span>
              </div>
            </div>
          </div>
          <!-- Fallback for when no preset is matched -->
          <div v-else-if="selectedFields.length === 0" class="tags-grid">
            <div v-for="(value, key) in collection.tags" :key="key" class="tag-item">
              <span class="tag-key">{{ key }}:</span>
              <span class="tag-value">{{ value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Permissions and Ownership section -->
      <div class="permissions-section">
        <h3>Permissions & Ownership</h3>
        
        <!-- Permissions Table -->
        <div class="permissions-table-container">
          <table class="permissions-table">
            <thead>
              <tr>
                <th>Role</th>
                <th>Read</th>
                <th>Write</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="role-label">Owner</td>
                <td :class="getPermissionClass(collection.permissions, 'owner', 'read')">
                  {{ getPermissionText(collection.permissions, 'owner', 'read') }}
                </td>
                <td :class="getPermissionClass(collection.permissions, 'owner', 'write')">
                  {{ getPermissionText(collection.permissions, 'owner', 'write') }}
                </td>
              </tr>
              <tr>
                <td class="role-label">Group</td>
                <td :class="getPermissionClass(collection.permissions, 'group', 'read')">
                  {{ getPermissionText(collection.permissions, 'group', 'read') }}
                </td>
                <td :class="getPermissionClass(collection.permissions, 'group', 'write')">
                  {{ getPermissionText(collection.permissions, 'group', 'write') }}
                </td>
              </tr>
              <tr>
                <td class="role-label">Others</td>
                <td :class="getPermissionClass(collection.permissions, 'others', 'read')">
                  {{ getPermissionText(collection.permissions, 'others', 'read') }}
                </td>
                <td :class="getPermissionClass(collection.permissions, 'others', 'write')">
                  {{ getPermissionText(collection.permissions, 'others', 'write') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Ownership Info -->
        <div class="ownership-info">
          <div class="ownership-item" v-if="collection.owner_user_id">
            <span class="ownership-label">Owner:</span>
            <span class="ownership-value">{{ formatOwner(collection.owner_user_id) }}</span>
          </div>
          <div class="ownership-item" v-if="collection.owner_group_id">
            <span class="ownership-label">Group:</span>
            <span class="ownership-value">{{ formatGroup(collection.owner_group_id) }}</span>
          </div>
        </div>
      </div>

      <!-- Collection Statistics section -->
      <div class="collection-stats-section">
        <h3>Collection Statistics</h3>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">Total Items:</span>
            <span class="stat-value">{{ totalItems }}</span>
          </div>
          <div class="stat-item" v-if="fileCount > 0">
            <span class="stat-label">Files:</span>
            <span class="stat-value">{{ fileCount }}</span>
          </div>
          <div class="stat-item" v-if="collectionCount > 0">
            <span class="stat-label">Sub-collections:</span>
            <span class="stat-value">{{ collectionCount }}</span>
          </div>
          <div class="stat-item" v-if="collection.created_at">
            <span class="stat-label">Created:</span>
            <span class="stat-value">{{ formatDate(collection.created_at) }}</span>
          </div>
          <div class="stat-item" v-if="collection.updated_at">
            <span class="stat-label">Modified:</span>
            <span class="stat-value">{{ formatDate(collection.updated_at) }}</span>
          </div>
        </div>
      </div>

      
    </div>

    <!-- No collection state (for root) -->
    <div v-else class="no-collection-state">
      <div class="empty-icon">📁</div>
      <h3>Root Directory</h3>
      <p>You are viewing the root directory. Create collections to organize your files.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { matchTagsToPreset, getAllPresets } from '../utils/tagMatcher.js'
import { loadFieldDefinitions, resolveFields } from '../utils/fieldResolver.js'
import apiService from '../services/api.js'

const props = defineProps({
  item: {
    type: Object,
    default: {}
  },
  files: {
    type: Array,
    default: () => []
  }
})

// Router instance
const router = useRouter()

// State
const collection = ref(null)
const loading = ref(false)
const error = ref(null)

// Type matching state (reused from FileViewer)
const allPresets = ref([])
const allFieldDefinitions = ref({})
const selectedType = ref(null)


// Computed properties
const selectedFields = computed(() => {
  if (!selectedType.value || !selectedType.value.fields) {
    return []
  }
  return resolveFields(selectedType.value.fields, allFieldDefinitions.value)
})

const otherTags = computed(() => {
  if (!collection.value?.tags || !selectedType.value?.fields) {
    return collection.value?.tags || {}
  }
  
  // Get field names from the selected preset
  const presetFieldNames = new Set(selectedFields.value.map(field => field.key || field.name))
  
  // Return tags that aren't in the preset
  const other = {}
  Object.entries(collection.value.tags).forEach(([key, value]) => {
    if (!presetFieldNames.has(key)) {
      other[key] = value
    }
  })
  
  return other
})

const totalItems = computed(() => {
  return props.files.length
})

const fileCount = computed(() => {
  return props.files.filter(item => item.object_type === 'file').length
})

const collectionCount = computed(() => {
  return props.files.filter(item => item.object_type === 'tree').length
})

// Methods
function getDisplayName() {
  if (!collection.value) return 'Root Directory'
  return collection.value.tags?.name || collection.value.name || 'Untitled Collection'
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown'
  return new Date(dateString).toLocaleDateString()
}

function getPermissionText(permissions, role, type) {
  if (!permissions) return '✗'
  
  let bit
  if (role === 'owner' && type === 'read') bit = 0o400
  else if (role === 'owner' && type === 'write') bit = 0o200
  else if (role === 'group' && type === 'read') bit = 0o040
  else if (role === 'group' && type === 'write') bit = 0o020
  else if (role === 'others' && type === 'read') bit = 0o004
  else if (role === 'others' && type === 'write') bit = 0o002
  
  return (permissions & bit) ? '✓' : '✗'
}

function getPermissionClass(permissions, role, type) {
  if (!permissions) return 'permission-denied'
  
  let bit
  if (role === 'owner' && type === 'read') bit = 0o400
  else if (role === 'owner' && type === 'write') bit = 0o200
  else if (role === 'group' && type === 'read') bit = 0o040
  else if (role === 'group' && type === 'write') bit = 0o020
  else if (role === 'others' && type === 'read') bit = 0o004
  else if (role === 'others' && type === 'write') bit = 0o002
  
  return (permissions & bit) ? 'permission-granted' : 'permission-denied'
}

function formatOwner(ownerId) {
  if (!ownerId) return 'No owner'
  // For now, just show the ID. In the future, we could lookup user info
  return ownerId
}

function formatGroup(groupId) {
  if (!groupId) return 'No group'
  // For now, just show the ID. In the future, we could lookup group info  
  return groupId
}

function formatFieldValue(field, value) {
  if (value === null || value === undefined || value === '') {
    return 'Not set'
  }
  
  switch (field.type) {
    case 'bool':
      return value === 'yes' || value === true || value === '1' ? 'Yes' : 'No'
    case 'number':
      return value.toString()
    case 'enum':
      // If field has options, try to find the label for the value
      if (field.options) {
        const option = field.options.find(opt => 
          (typeof opt === 'string' ? opt : opt.value) === value
        )
        if (option) {
          return typeof option === 'string' ? option : (option.label || option.value)
        }
      }
      return value.toString()
    default:
      return value.toString()
  }
}

function getFieldDisplayClass(field) {
  return {
    'bool-field': field.type === 'bool',
    'number-field': field.type === 'number',
    'enum-field': field.type === 'enum',
    'text-field': field.type === 'str' || !field.type
  }
}

// Navigation methods
function editCollection() {
  if (collection.value?.id) {
    router.push({
      name: 'FileEditor',
      query: { id: collection.value.id }
    })
  }
}

// Lifecycle
onMounted(async () => {
  // Load all field definitions and presets using centralized loading
  allPresets.value = getAllPresets()
  allFieldDefinitions.value = await loadFieldDefinitions()
  collection.value = props.item
})

</script>

<style scoped>
.collection-details {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  width: 350px;
  flex-shrink: 0;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: #666;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-state i {
  font-size: 2rem;
  color: #dc3545;
  margin-bottom: 1rem;
}

.collection-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Unified properties section */
.unified-properties-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.unified-properties-section h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.edit-btn:hover {
  background: #0056b3;
}

.edit-btn svg {
  width: 16px;
  height: 16px;
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

.other-tags-section {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
}

.other-tags-section h5 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: #666;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
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
  text-align: right;
  max-width: 150px;
}

.field-display {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  font-size: 0.9rem;
}

.field-display.bool-field {
  background: #d4edda;
  color: #155724;
  border-color: #c3e6cb;
}

.field-display.bool-field:has-text("No") {
  background: #f8d7da;
  color: #721c24;
  border-color: #f5c6cb;
}

.field-display.number-field {
  background: #e2e6ea;
  color: #383d41;
  border-color: #d6d8db;
  font-family: monospace;
}

.field-display.enum-field {
  background: #fff3cd;
  color: #856404;
  border-color: #ffeaa7;
}

.tags-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tag-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.tag-key {
  font-weight: 500;
  color: #495057;
  min-width: 80px;
}

.tag-value {
  color: #333;
  word-break: break-word;
  text-align: right;
  max-width: 150px;
}

/* Permissions section */
.permissions-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.permissions-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
}

/* Permissions table */
.permissions-table-container {
  margin-bottom: 1.5rem;
}

.permissions-table {
  width: 100%;
  border-collapse: collapse;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

.permissions-table th {
  background: #f8f9fa;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.9rem;
  color: #495057;
  border-bottom: 1px solid #e9ecef;
}

.permissions-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #f1f3f4;
  font-size: 0.9rem;
  text-align: center;
}

.permissions-table .role-label {
  text-align: left;
  font-weight: 500;
  color: #495057;
}

.permissions-table tbody tr:last-child td {
  border-bottom: none;
}

/* Permission status styling */
.permission-granted {
  background-color: #d4edda;
  color: #155724;
  font-weight: bold;
  border-radius: 4px;
}

.permission-denied {
  background-color: #f8d7da;
  color: #721c24;
  font-weight: bold;
  border-radius: 4px;
}

/* Ownership info */
.ownership-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ownership-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.ownership-label {
  font-size: 0.9rem;
  color: #495057;
  font-weight: 500;
}

.ownership-value {
  font-size: 0.9rem;
  color: #212529;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

/* Collection statistics section */
.collection-stats-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.collection-stats-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
}

.stats-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.stat-label {
  font-size: 0.9rem;
  color: #495057;
  font-weight: 500;
}

.stat-value {
  font-size: 0.9rem;
  color: #212529;
  font-weight: 600;
}

/* Collection info section */
.collection-info-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.collection-info-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.info-label {
  font-size: 0.9rem;
  color: #495057;
  font-weight: 500;
  min-width: 80px;
}

.info-value {
  font-size: 0.9rem;
  color: #212529;
  text-align: right;
  word-break: break-word;
  max-width: 200px;
}

/* No collection state */
.no-collection-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #666;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-collection-state h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.no-collection-state p {
  margin: 0;
  font-size: 1rem;
  line-height: 1.5;
  color: #666;
}
</style>
