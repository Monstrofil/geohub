// Centralized preset loading
const presetModules = import.meta.glob('../data/presets/*/*.json', { eager: true })
let loadedPresets = null

/**
 * Get all loaded presets
 * @returns {Array} Array of preset objects with translation keys
 */
export function getAllPresets() {
  if (!loadedPresets) {
    loadedPresets = Object.entries(presetModules).map(([path, module]) => {
      const preset = module.default || module
      // Generate translation key from filename
      preset.translationKey = generateTranslationKey(path)
      return preset
    })
  }
  return loadedPresets
}

/**
 * Generate translation key from file path
 * @param {string} filePath - The file path
 * @returns {string} Translation key
 */
function generateTranslationKey(filePath) {
  if (!filePath) return ''
  
  // Extract filename without extension from path
  const filename = filePath.split('/').pop().replace(/\.json$/, '')
  return filename
}

export function matchTagsToPreset(fileTags, allPresets = null, objectType = null) {
  // Use centralized presets if none provided
  if (!allPresets) {
    allPresets = getAllPresets()
  }
  // Defensive programming: ensure allPresets is an array
  if (!Array.isArray(allPresets) || allPresets.length === 0) {
    return null
  }

  let bestMatch = null
  let bestScore = 0

  for (const preset of allPresets) {
    const presetTags = preset.tags || {}

    // Filter by object_type if provided
    if (objectType && preset.object_type) {
      if (!preset.object_type.includes(objectType)) {
        continue // Skip this preset as it doesn't match the object type
      }
    }

    // Check if all preset tags exist in fileTags with the same value
    let allMatch = true
    for (const [key, value] of Object.entries(presetTags)) {
      if (fileTags[key] !== value) {
        allMatch = false
        break
      }
    }

    if (allMatch) {
      // Use matchScore to break ties, or just pick the first match
      const score = preset.matchScore || 1
      if (!bestMatch || score > bestScore) {
        bestMatch = preset
        bestScore = score
      }
    }
  }

  return bestMatch
}

export function getFileType(file, allPresets = null) {
  // Use centralized presets if none provided
  if (!allPresets) {
    allPresets = getAllPresets()
  }
  
  // Defensive programming: ensure allPresets is an array
  if (!Array.isArray(allPresets) || allPresets.length === 0) {
    return 'binary' // fallback
  }

  const matchedPreset = matchTagsToPreset(file.tags, allPresets, file.object_type)
  
  // Map preset names to file types for the Card component
  if (matchedPreset) {
    if (matchedPreset.name === 'Generic Raster Graphic') return 'raster'
    if (matchedPreset.name === 'Generic Vector Graphic') return 'vector'
    if (matchedPreset.name === 'Generic File') return 'binary'
    // For military presets, determine type based on file extension or default to raster
    if (file.name.match(/\.(jpg|jpeg|png|gif|bmp|tiff)$/i)) return 'raster'
    if (file.name.match(/\.(svg|ai|eps|pdf)$/i)) return 'vector'
    if (file.name.match(/\.(txt|md|json|xml|html|css|js)$/i)) return 'text'
    return 'binary' // default fallback
  }
  
  return 'binary' // fallback
} 