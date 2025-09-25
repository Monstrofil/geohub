import PdfPreview from './PdfPreview.vue'
import ImagePreview from './ImagePreview.vue'
import { probePdf, probeImage } from './probeFunctions.js'

// Array of all preview components with their probe functions
export const previewComponents = [
  {
    name: 'PdfPreview',
    component: PdfPreview,
    probe: probePdf
  },
  {
    name: 'ImagePreview', 
    component: ImagePreview,
    probe: probeImage
  }
]

// Function to find the appropriate preview component for a file
export function findPreviewComponent(file) {
  if (!file) return null
  
  // Try each component's probe function
  for (const preview of previewComponents) {
    if (preview.probe(file)) {
      return preview
    }
  }
  
  return null
}

// Export individual components
export { PdfPreview, ImagePreview }
