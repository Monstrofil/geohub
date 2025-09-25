// Probe functions for preview components
// These functions determine if a component can handle a specific file type

export function probePdf(file) {
  if (!file) return false
  
  // Check if file has PDF mime type
  const mimeType = file.object_details?.mime_type || file.mime_type || file.type
  return mimeType === 'application/pdf'
}

export function probeImage(file) {
  if (!file) return false
  
  // Check if file has image mime type
  const mimeType = file.object_details?.mime_type || file.mime_type || file.type
  return mimeType === 'image/jpeg' || 
         mimeType === 'image/jpg' || 
         mimeType === 'image/png' ||
         mimeType === 'image/gif' ||
         mimeType === 'image/bmp' ||
         mimeType === 'image/webp'
}
