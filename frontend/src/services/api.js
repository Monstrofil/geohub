const API_BASE_URL = 'http://localhost:8000/api/v1'

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        return await response.json()
      }
      
      return await response.text()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // ======================
  // FILE OPERATIONS
  // ======================

  /**
   * Upload a file
   * @param {File} file - The file to upload
   * @param {Object} tags - Tags to associate with the file
   * @param {string} parentPath - The LTREE path where the file should be placed (default: "root")
   * @returns {Promise<Object>} The uploaded file response
   */
  async uploadFile(file, tags = {}, parentPath = "root") {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('tags', JSON.stringify(tags))
    formData.append('parent_path', parentPath)

    const response = await fetch(`${this.baseUrl}/files`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Upload failed! status: ${response.status}`)
    }

    return await response.json()
  }

  /**
   * Get files with optional filters
   * @param {Object} filters - Filter options
   * @param {Object} filters.tags - Tags to filter by
   * @param {string} filters.base_type - File type filter (raster, vector, raw)
   * @param {string} filters.collection_path - LTREE path to filter by collection
   * @param {number} skip - Number of items to skip
   * @param {number} limit - Number of items to return
   * @returns {Promise<Object>} Files list response
   */
  async getFiles(filters = {}, skip = 0, limit = 100) {
    const response = await this.getTreeItems({ ...filters, type: 'file' }, skip, limit)
    
    // Transform unified response to legacy format for backward compatibility
    return {
      files: response.items || [],
      total: response.total,
      skip: response.skip,
      limit: response.limit
    }
  }

  /**
   * Get a single file by ID
   * @param {string} fileId - The file ID
   * @returns {Promise<Object>} File object
   */
  async getFile(fileId) {
    return await this.getTreeItem(fileId)
  }

  /**
   * Update file metadata
   * @param {string} fileId - The file ID
   * @param {Object} updates - Updates to apply
   * @param {Object} updates.tags - New tags
   * @param {string} updates.parent_path - New parent path
   * @returns {Promise<Object>} Updated file object
   */
  async updateFile(fileId, updates) {
    return await this.updateTreeItem(fileId, updates)
  }

  /**
   * Delete a file
   * @param {string} fileId - The file ID
   * @returns {Promise<Object>} Deletion confirmation
   */
  async deleteFile(fileId) {
    return await this.deleteTreeItem(fileId, false)
  }

  /**
   * Download a file
   * @param {string} fileId - The file ID
   * @returns {Promise<Response>} File download response
   */
  async downloadFile(fileId) {
    const response = await fetch(`${this.baseUrl}/files/${fileId}/download`)
    if (!response.ok) {
      throw new Error(`Download failed! status: ${response.status}`)
    }
    return response
  }

  // ======================
  // COLLECTION OPERATIONS
  // ======================

  /**
   * Create a new collection
   * @param {string} name - The name of the collection
   * @param {Object} tags - Tags to associate with the collection (optional)
   * @param {string} parentPath - The parent LTREE path (default: "root")
   * @returns {Promise<Object>} The created collection response
   */
  async createCollection(name, tags = {}, parentPath = "root") {
    if (!name) throw new Error('name is required for collection creation')
    
    return await this.createTreeItem(name, 'collection', tags, parentPath)
  }

  /**
   * Get collections with optional parent filter
   * @param {string} parentPath - Parent path to filter by (default: "root")
   * @param {number} skip - Number of items to skip
   * @param {number} limit - Number of items to return
   * @returns {Promise<Object>} Collections list response
   */
  async getCollections(parentPath = "root", skip = 0, limit = 100) {
    const response = await this.getTreeItems({ 
      type: 'collection',
      collection_path: parentPath 
    }, skip, limit)
    
    // Transform unified response to legacy format for backward compatibility
    return {
      collections: response.items || [],
      total: response.total,
      skip: response.skip,
      limit: response.limit
    }
  }

  /**
   * Get a single collection by ID
   * @param {string} collectionId - The collection ID
   * @returns {Promise<Object>} Collection object
   */
  async getCollection(collectionId) {
    return await this.getTreeItem(collectionId)
  }

  /**
   * Find a collection by its LTREE path
   * @param {string} path - The LTREE path to search for
   * @returns {Promise<Object|null>} Collection object or null if not found
   */
  async findCollectionByPath(path) {
    try {
      // Search through all collections recursively to find one with matching path
      // This is a simple implementation - in production you'd want a dedicated endpoint
      let allCollections = []
      
      // Get root collections first
      const rootCollections = await this.getCollections("root", 0, 1000)
      allCollections = [...rootCollections.collections]
      
      // For nested collections, we need to search through all possible parent paths
      // This is inefficient but works for the demo
      const pathParts = path.split('.')
      for (let i = 1; i < pathParts.length; i++) {
        const parentPath = pathParts.slice(0, i + 1).join('.')
        try {
          const childCollections = await this.getCollections(parentPath, 0, 1000)
          allCollections = [...allCollections, ...childCollections.collections]
        } catch (e) {
          // Parent path might not exist, continue searching
          continue
        }
      }
      
      return allCollections.find(c => c.path === path) || null
    } catch (error) {
      console.error('Error finding collection by path:', error)
      return null
    }
  }

  /**
   * Update collection metadata
   * @param {string} collectionId - The collection ID
   * @param {Object} updates - Updates to apply
   * @param {string} updates.name - New name
   * @param {Object} updates.tags - New tags
   * @param {string} updates.parent_path - New parent path
   * @returns {Promise<Object>} Updated collection object
   */
  async updateCollection(collectionId, updates) {
    return await this.updateTreeItem(collectionId, updates)
  }

  /**
   * Delete a collection
   * @param {string} collectionId - The collection ID
   * @param {boolean} force - Whether to force delete non-empty collection
   * @returns {Promise<Object>} Deletion confirmation
   */
  async deleteCollection(collectionId, force = false) {
    return await this.deleteTreeItem(collectionId, force)
  }

  /**
   * Get contents of a collection (files and subcollections)
   * @param {string} collectionId - The collection ID
   * @param {number} skip - Number of items to skip
   * @param {number} limit - Number of items to return
   * @returns {Promise<Object>} Collection contents response
   */
  async getCollectionContents(collectionId, skip = 0, limit = 100) {
    const response = await this.getTreeItemContents(collectionId, skip, limit)
    
    // Transform unified response to legacy format for backward compatibility
    return {
      files: response.items?.filter(item => item.type === 'file') || [],
      collections: response.items?.filter(item => item.type === 'collection') || [],
      total_files: response.items?.filter(item => item.type === 'file').length || 0,
      total_collections: response.items?.filter(item => item.type === 'collection').length || 0
    }
  }

  /**
   * Get contents of the root (files and collections without parent)
   * @param {number} skip - Number of items to skip
   * @param {number} limit - Number of items to return
   * @returns {Promise<Object>} Root contents response
   */
  async getRootContents(skip = 0, limit = 100) {
    const params = new URLSearchParams()
    params.append('skip', skip.toString())
    params.append('limit', limit.toString())

    const response = await this.request(`/root/contents?${params.toString()}`)
    
    // Transform new unified response to legacy format for backward compatibility
    return {
      files: response.items?.filter(item => item.type === 'file') || [],
      collections: response.items?.filter(item => item.type === 'collection') || [],
      total_files: response.items?.filter(item => item.type === 'file').length || 0,
      total_collections: response.items?.filter(item => item.type === 'collection').length || 0
    }
  }

  // ======================
  // MAPSERVER OPERATIONS
  // ======================

  /**
   * Get MapServer URL for a file
   * @param {string} fileId - The file ID
   * @returns {Promise<Object>} Map URL response
   */
  async getFileMap(fileId) {
    return await this.request(`/files/${fileId}/map`)
  }

  /**
   * Get file extent (bounding box)
   * @param {string} fileId - The file ID
   * @returns {Promise<Object>} File extent response
   */
  async getFileExtent(fileId) {
    return await this.request(`/files/${fileId}/extent`)
  }

  /**
   * Get file preview URL
   * @param {string} fileId - The file ID
   * @returns {Promise<Object>} Preview URL response
   */
  async getFilePreview(fileId) {
    return await this.request(`/files/${fileId}/preview`)
  }

  /**
   * Clean up old MapServer configurations
   * @param {number} maxAgeHours - Maximum age in hours
   * @returns {Promise<Object>} Cleanup response
   */
  async cleanupMapServer(maxAgeHours = 24) {
    return await this.request('/mapserver/cleanup', {
      method: 'POST',
      body: JSON.stringify({ max_age_hours: maxAgeHours }),
    })
  }

  // ======================
  // UNIFIED TREE ITEM OPERATIONS
  // ======================

  /**
   * Get tree items with optional filters
   * @param {Object} filters - Filter options
   * @param {string} filters.type - Item type filter ("file" or "collection")
   * @param {Object} filters.tags - Tags to filter by
   * @param {string} filters.base_type - Base file type filter ("raster", "vector", "raw")
   * @param {string} filters.collection_path - LTREE path to filter by collection
   * @param {number} skip - Number of items to skip
   * @param {number} limit - Number of items to return
   * @returns {Promise<Object>} Tree items response
   */
  async getTreeItems(filters = {}, skip = 0, limit = 100) {
    const params = new URLSearchParams()
    params.append('skip', skip.toString())
    params.append('limit', limit.toString())
    
    if (filters.type) {
      params.append('type', filters.type)
    }
    if (filters.tags) {
      params.append('tags', JSON.stringify(filters.tags))
    }
    if (filters.base_type) {
      params.append('base_type', filters.base_type)
    }
    if (filters.collection_path) {
      params.append('collection_path', filters.collection_path)
    }

    return await this.request(`/tree-items?${params.toString()}`)
  }

  /**
   * Create a new tree item (collection only - files via upload)
   * @param {string} name - The name of the item
   * @param {string} type - Item type ("collection" only)
   * @param {Object} tags - Tags to associate with the item
   * @param {string} parentPath - The parent LTREE path
   * @returns {Promise<Object>} The created item response
   */
  async createTreeItem(name, type, tags = {}, parentPath = "root") {
    if (type !== 'collection') {
      throw new Error('Use uploadFile for creating file tree items')
    }
    
    return await this.request('/tree-items', {
      method: 'POST',
      body: JSON.stringify({
        name,
        type,
        tags,
        parent_path: parentPath
      }),
    })
  }

  /**
   * Update a tree item
   * @param {string} itemId - The item ID
   * @param {Object} updates - Updates to apply
   * @returns {Promise<Object>} Updated item object
   */
  async updateTreeItem(itemId, updates) {
    return await this.request(`/tree-items/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  }

  /**
   * Delete a tree item
   * @param {string} itemId - The item ID
   * @param {boolean} force - Whether to force delete (for collections)
   * @returns {Promise<Object>} Deletion confirmation
   */
  async deleteTreeItem(itemId, force = false) {
    const params = force ? '?force=true' : ''
    return await this.request(`/tree-items/${itemId}${params}`, {
      method: 'DELETE',
    })
  }

  /**
   * Get a tree item by ID
   * @param {string} itemId - The item ID
   * @returns {Promise<Object>} Tree item object
   */
  async getTreeItem(itemId) {
    return await this.request(`/tree-items/${itemId}`)
  }

  /**
   * Get contents of a tree item (collection)
   * @param {string} itemId - The item ID
   * @param {number} skip - Number of items to skip
   * @param {number} limit - Number of items to return
   * @returns {Promise<Object>} Tree item contents response
   */
  async getTreeItemContents(itemId, skip = 0, limit = 100) {
    const params = new URLSearchParams()
    params.append('skip', skip.toString())
    params.append('limit', limit.toString())

    return await this.request(`/tree-items/${itemId}/contents?${params.toString()}`)
  }

  // Health check
  async healthCheck() {
    return await fetch('http://localhost:8000/health').then(res => res.json())
  }


  // ======================
  // GEOREFERENCING OPERATIONS
  // ======================



  /**
   * Validate control points
   * @param {string} fileId - The file ID
   * @param {Object} request - Control points request
   * @returns {Promise<Object>} Validation results
   */
  async validateControlPoints(fileId, request) {
    return await this.request(`/files/${fileId}/validate-control-points`, {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Apply georeferencing to a file
   * @param {string} fileId - The file ID
   * @param {Object} request - Georeferencing request
   * @returns {Promise<Object>} Apply result
   */
  async applyGeoreferencing(fileId, request) {
    return await this.request(`/files/${fileId}/apply-georeferencing`, {
      method: 'POST',
      body: JSON.stringify(request)
    })
  }

  /**
   * Upload file with progress tracking
   * @param {FormData} formData - Form data with file
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<Object>} Upload result
   */
  async uploadFileWithProgress(formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = event.loaded / event.total
          onProgress(progress)
        }
      })
      
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText)
            resolve(response)
          } catch (error) {
            reject(new Error('Failed to parse response'))
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText)
            reject(new Error(errorData.detail || `Upload failed! status: ${xhr.status}`))
          } catch (error) {
            reject(new Error(`Upload failed! status: ${xhr.status}`))
          }
        }
      })
      
      xhr.addEventListener('error', () => {
        reject(new Error('Network error occurred'))
      })
      
      xhr.open('POST', `${this.baseUrl}/files`)
      xhr.send(formData)
    })
  }

  /**
   * Clean up georeferencing temporary files
   * @param {number} maxAgeHours - Maximum age in hours
   * @returns {Promise<Object>} Cleanup result
   */
  async cleanupGeoreferencingFiles(maxAgeHours = 24) {
    return await this.request(`/georeferencing/cleanup?max_age_hours=${maxAgeHours}`, {
      method: 'POST'
    })
  }

  /**
   * Probe a tree item to check if it can be georeferenced
   * @param {string} itemId - The tree item ID
   * @returns {Promise<Object>} Probe result with can_georeference flag and other info
   */
  async probeTreeItem(itemId) {
    return await this.request(`/tree-items/${itemId}/probe`, {
      method: 'POST'
    })
  }

  /**
   * Convert a tree item to geo-raster format for georeferencing
   * @param {string} itemId - The tree item ID
   * @returns {Promise<Object>} Updated tree item object
   */
  async convertToGeoRaster(itemId) {
    return await this.request(`/tree-items/${itemId}/convert-to-geo-raster`, {
      method: 'POST'
    })
  }
}

export default new ApiService()