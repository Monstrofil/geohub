/**
 * Helper functions for working with file objects in both old and new unified TreeItem structure
 */

/**
 * Get file property value, handling both old direct properties and new tags structure
 * @param {Object} file - File object (old structure or new TreeItem)
 * @param {string} property - Property name
 * @param {*} defaultValue - Default value if property not found
 * @returns {*} Property value
 */
export function getFileProperty(file, property, defaultValue = null) {
  if (!file) return defaultValue
  
  // Try new tags structure first, then fallback to old direct properties
  return file.tags?.[property] ?? file[property] ?? defaultValue
}

/**
 * Get original filename, handling both structures
 * @param {Object} file - File object
 * @returns {string} Original filename
 */
export function getOriginalName(file) {
  return getFileProperty(file, 'original_name') || file?.name || 'Untitled'
}

/**
 * Get file size, handling both structures
 * @param {Object} file - File object
 * @returns {number} File size in bytes
 */
export function getFileSize(file) {
  return getFileProperty(file, 'file_size', 0)
}

/**
 * Get MIME type, handling both structures
 * @param {Object} file - File object
 * @returns {string} MIME type
 */
export function getMimeType(file) {
  return getFileProperty(file, 'mime_type', 'application/octet-stream')
}

/**
 * Get base file type, handling both structures
 * @param {Object} file - File object
 * @returns {string} Base file type (raster, vector, raw)
 */
export function getBaseFileType(file) {
  return getFileProperty(file, 'base_file_type', 'raw')
}

/**
 * Get SHA1 hash, handling both structures
 * @param {Object} file - File object
 * @returns {string|null} SHA1 hash
 */
export function getSha1(file) {
  return getFileProperty(file, 'sha1')
}

/**
 * Get display name for a file or collection, prioritizing custom tags
 * @param {Object} item - File or collection object
 * @returns {string} Display name
 */
export function getDisplayName(item) {
  if (!item) return 'Untitled'
  
  // For files, check tags first, then original_name, then name
  if (item.type === 'file' || item.object_type === 'file') {
    return item.tags?.name || getOriginalName(item) || item.name || 'Untitled File'
  }
  
  // For collections, use name or tags.name
  return item.tags?.name || item.name || 'Untitled Collection'
}

/**
 * Format file size in human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * Check if an item is a file (works with both old and new structure)
 * @param {Object} item - File or collection object
 * @returns {boolean} True if item is a file
 */
export function isFile(item) {
  return item?.type === 'file' || item?.object_type === 'file'
}

/**
 * Check if an item is a collection (works with both old and new structure)
 * @param {Object} item - File or collection object
 * @returns {boolean} True if item is a collection
 */
export function isCollection(item) {
  return item?.type === 'collection' || item?.object_type === 'tree' || item?.object_type === 'collection'
}
