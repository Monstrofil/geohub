// Cache for loaded field definitions
let fieldDefinitions = null

// Load all field definitions
export async function loadFieldDefinitions() {
  if (fieldDefinitions) {
    return fieldDefinitions
  }

  try {
    // Dynamically import all field JSONs
    const fieldModules = import.meta.glob('../data/fields/*.json', { eager: true })
    fieldDefinitions = {}
    
    Object.entries(fieldModules).forEach(([path, module]) => {
      const fieldKey = path.split('/').pop().replace('.json', '')
      fieldDefinitions[fieldKey] = module.default || module
    })
    
    return fieldDefinitions
  } catch (error) {
    console.error('Error loading field definitions:', error)
    return {}
  }
}

// Resolve field keys to full field definitions
export function resolveFields(fieldKeys, allFieldDefinitions) {
  if (!Array.isArray(fieldKeys)) {
    return []
  }

  return fieldKeys.map(key => {
    const fieldDef = allFieldDefinitions[key]
    if (!fieldDef) {
      // Auto-create a simple text field for undefined fields
      return {
        name: key,
        key: key,
        type: 'str',
        label: formatFieldLabel(key)
      }
    }

    // Map field definition format to our component format
    return {
      name: fieldDef.key,
      key: fieldDef.key,
      type: mapFieldType(fieldDef.type),
      label: fieldDef.label,
      values: fieldDef.strings?.options ? Object.keys(fieldDef.strings.options) : undefined,
      placeholder: fieldDef.placeholder
    }
  })
}

// Format field key into a readable label
function formatFieldLabel(key) {
  // Handle OSM-style keys with slashes and underscores
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

// Map field types from the new format to our component format
function mapFieldType(fieldType) {
  const typeMap = {
    'text': 'str',
    'textarea': 'richtext',
    'check': 'bool',
    'combo': 'enum',
    'number': 'number'
  }
  
  return typeMap[fieldType] || 'str'
}

// Get field definition by key
export function getFieldDefinition(key, allFieldDefinitions) {
  return allFieldDefinitions[key]
} 