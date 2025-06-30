export function matchTagsToPreset(fileTags, allPresets) {
  // Defensive programming: ensure allPresets is an array
  if (!Array.isArray(allPresets) || allPresets.length === 0) {
    return null
  }

  let bestMatch = null
  let bestScore = 0

  for (const preset of allPresets) {
    const presetTags = preset.tags || {}

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

export function getFileType(file, allPresets) {
  // Defensive programming: ensure allPresets is an array
  if (!Array.isArray(allPresets) || allPresets.length === 0) {
    return 'binary' // fallback
  }

  const matchedPreset = matchTagsToPreset(file.tags, allPresets)
  
  // Map preset names to file types for the FileCard component
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