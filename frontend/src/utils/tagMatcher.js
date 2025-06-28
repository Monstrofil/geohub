export function matchTagsToPreset(fileTags, allPresets) {
  // Defensive programming: ensure allPresets is an array
  if (!Array.isArray(allPresets) || allPresets.length === 0) {
    return null
  }

  let bestMatch = null
  let bestScore = 0

  for (const preset of allPresets) {
    const presetTags = preset.tags || {}
    let score = 0
    let totalPossibleMatches = Object.keys(presetTags).length

    // If preset has no tags, it's a generic fallback
    if (totalPossibleMatches === 0) {
      if (preset.name === 'Generic File') {
        bestMatch = preset
        bestScore = preset.matchScore || 0.1
      }
      continue
    }

    // Check how many tags match
    for (const [key, value] of Object.entries(presetTags)) {
      if (fileTags[key] === value) {
        score += 1
      }
    }

    // Calculate match percentage
    const matchPercentage = score / totalPossibleMatches

    if (matchPercentage > bestScore) {
      bestScore = matchPercentage
      bestMatch = preset
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