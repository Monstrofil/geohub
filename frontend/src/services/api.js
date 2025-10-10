import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL
    this.token = localStorage.getItem('auth_token')
    this.refreshToken = localStorage.getItem('refresh_token')
    this.isRefreshing = false
    this.failedQueue = []
    
    // Create axios instance
    this.axios = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    // Add request interceptor to automatically include auth token
    this.axios.interceptors.request.use(
      (config) => {
        const token = this.getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )
    
    // Add response interceptor for error handling and token refresh
    this.axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          // Token expired, try to refresh
          originalRequest._retry = true
          
          if (this.isRefreshing) {
            // If already refreshing, queue this request
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject })
            }).then(token => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              return this.axios(originalRequest)
            }).catch(err => {
              return Promise.reject(err)
            })
          }
          
          try {
            const newTokens = await this.refreshAccessToken()
            if (newTokens) {
              // Retry the original request with new token
              originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`
              
              // Process queued requests
              this.processQueue(null, newTokens.access_token)
              
              return this.axios(originalRequest)
            }
          } catch (refreshError) {
            // Refresh failed, logout user
            this.processQueue(refreshError, null)
            this.logout()
            // Emit logout event for auth store to handle
            window.dispatchEvent(new CustomEvent('auth-logout'))
            return Promise.reject(refreshError)
          }
        }
        
        const message = error.response?.data?.detail || error.message || 'Request failed'
        throw new Error(message)
      }
    )
  }

  setToken(token) {
    this.token = token
    if (token) {
      localStorage.setItem('auth_token', token)
    } else {
      localStorage.removeItem('auth_token')
    }
  }

  setRefreshToken(refreshToken) {
    this.refreshToken = refreshToken
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken)
    } else {
      localStorage.removeItem('refresh_token')
    }
  }

  getToken() {
    return this.token || localStorage.getItem('auth_token')
  }

  getRefreshToken() {
    return this.refreshToken || localStorage.getItem('refresh_token')
  }

  processQueue(error, token = null) {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error)
      } else {
        resolve(token)
      }
    })
    
    this.failedQueue = []
  }

  async refreshAccessToken() {
    if (!this.getRefreshToken()) {
      throw new Error('No refresh token available')
    }

    this.isRefreshing = true

    try {
      // Create a new axios instance without interceptors to avoid infinite loops
      const response = await axios.post(`${this.baseUrl}/auth/refresh`, {
        refresh_token: this.getRefreshToken()
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const { access_token, refresh_token } = response.data
      this.setToken(access_token)
      this.setRefreshToken(refresh_token)
      
      return response.data
    } finally {
      this.isRefreshing = false
    }
  }

  async request(endpoint, options = {}) {
    try {
      // Convert old fetch-style options to axios format
      const axiosConfig = {
        url: endpoint,
        method: options.method || 'GET',
        headers: options.headers || {},
        ...options
      }
      
      // Handle body -> data conversion for axios
      if (options.body) {
        // If body is a JSON string, parse it back to object for axios
        if (typeof options.body === 'string') {
          try {
            axiosConfig.data = JSON.parse(options.body)
          } catch (e) {
            // If not valid JSON, use as-is
            axiosConfig.data = options.body
          }
        } else {
          axiosConfig.data = options.body
        }
        delete axiosConfig.body
      }
      
      const response = await this.axios.request(axiosConfig)
      return response.data
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
    // Check if file is larger than 75MB and use chunked upload
    const CHUNK_SIZE_THRESHOLD = 75 * 1024 * 1024 // 100MB
    if (file.size > CHUNK_SIZE_THRESHOLD) {
      return await this.uploadFileChunked(file, tags, parentPath)
    }

    const formData = new FormData()
    formData.append('file', file)
    formData.append('tags', JSON.stringify(tags))
    formData.append('parent_path', parentPath)

    const response = await this.axios.post('/files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    return response.data
  }

  /**
   * Upload a file using chunked upload for large files
   * @param {File} file - The file to upload
   * @param {Object} tags - Tags to associate with the file
   * @param {string} parentPath - The LTREE path where the file should be placed (default: "root")
   * @param {Function} onProgress - Optional progress callback
   * @returns {Promise<Object>} The uploaded file response
   */
  async uploadFileChunked(file, tags = {}, parentPath = "root", onProgress = null) {

    // Initialize chunked upload
    const initResponse = await this.axios.post('/files/chunked/init', {
      filename: file.name,
      file_size: file.size,
      mime_type: file.type,
      tags: tags,
      parent_path: parentPath
    })
    
    const { upload_id, chunk_size, total_chunks } = initResponse.data
    
    try {
      // Upload chunks
      for (let chunkNumber = 0; chunkNumber < total_chunks; chunkNumber++) {
        const start = chunkNumber * chunk_size
        const end = Math.min(start + chunk_size, file.size)
        const chunk = file.slice(start, end)
        
        const formData = new FormData()
        formData.append('upload_id', upload_id)
        formData.append('chunk_number', chunkNumber)
        formData.append('chunk_data', chunk, `chunk_${chunkNumber}`)
        
        await this.axios.post('/files/chunked/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        // Report progress
        if (onProgress) {
          const progress = (chunkNumber + 1) / total_chunks
          onProgress(progress)
        }
      }
      
      // Complete the upload
      const completeResponse = await this.axios.post('/files/chunked/complete', {
        upload_id: upload_id
      })
      
      return completeResponse.data
      
    } catch (error) {
      // Cancel upload on error
      try {
        await this.axios.delete(`/files/chunked/${upload_id}`)
      } catch (cancelError) {
        console.warn('Failed to cancel upload:', cancelError)
      }
      throw error
    }
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
    const response = await this.axios.get(`/files/${fileId}/download`, {
      responseType: 'blob'
    })
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
    const response = await this.listTreeItemContents(collectionId, skip, limit)
    
    // Transform unified response to legacy format for backward compatibility
    return {
      files: response.items?.filter(item => item.type === 'file') || [],
      collections: response.items?.filter(item => item.type === 'collection') || [],
      total_files: response.items?.filter(item => item.type === 'file').length || 0,
      total_collections: response.items?.filter(item => item.type === 'collection').length || 0,
      leaf: response.leaf 
    }
  }

  /**
   * Get contents of the root (files and collections without parent) using unified endpoint
   * @param {number} skip - Number of items to skip
   * @param {number} limit - Number of items to return
   * @returns {Promise<Object>} Root contents response
   */
  async getRootContents(skip = 0, limit = 100) {
    const params = new URLSearchParams()
    params.append('skip', skip.toString())
    params.append('limit', limit.toString())
    params.append('collection_path', 'root')

    const response = await this.request(`/tree-items?${params.toString()}`)
    
    // Transform new unified response to legacy format for backward compatibility
    return {
      files: response.items?.filter(item => item.type === 'file') || [],
      collections: response.items?.filter(item => item.type === 'collection') || [],
      total_files: response.items?.filter(item => item.type === 'file').length || 0,
      total_collections: response.items?.filter(item => item.type === 'collection').length || 0,
      leaf: response.leaf || null
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
   * Get task records for a tree item
   * @param {string} itemId - The tree item ID
   * @returns {Promise<Array>} Task records data
   */
  async getItemTaskRecords(itemId, activeOnly = false) {
    const params = activeOnly ? '?active_only=true' : ''
    return await this.request(`/tree-items/${itemId}/task-records${params}`)
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
   * Get contents of a tree item (collection) using the unified tree-items endpoint
   * @param {string} path - The path to the collection
   * @param {number} skip - Number of items to skip
   * @param {number} limit - Number of items to return
   * @returns {Promise<Object>} Tree item contents response
   */
   async listTreeItemContents(path, skip = 0, limit = 100) {
    const params = new URLSearchParams()
    params.append('skip', skip.toString())
    params.append('limit', limit.toString())
    if (path !== '') {
      params.append('collection_path', path)
    }
    

    return await this.request(`/tree-items?${params.toString()}`)
  }


  // Health check
  async healthCheck() {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const response = await this.axios.get(`${baseUrl.replace('/api/v1', '')}/health`)
    return response.data
  }

  // ======================
  // AUTHENTICATION OPERATIONS
  // ======================

  /**
   * Login with username and password
   * @param {string} username - Username
   * @param {string} password - Password
   * @returns {Promise<Object>} Login response with tokens and user info
   */
  async login(username, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    })
    
    // Store both tokens
    if (response.access_token) {
      this.setToken(response.access_token)
    }
    if (response.refresh_token) {
      this.setRefreshToken(response.refresh_token)
    }
    
    return response
  }

  /**
   * Logout current user
   */
  logout() {
    this.setToken(null)
    this.setRefreshToken(null)
  }

  /**
   * Get current user information
   * @returns {Promise<Object>} Current user object
   */
  async getCurrentUser() {
    return await this.request('/auth/me')
  }

  /**
   * Check if user is currently authenticated
   * @returns {boolean} True if token exists
   */
  isAuthenticated() {
    return !!this.getToken()
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
    const response = await this.axios.post('/files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.lengthComputable) {
          const progress = progressEvent.loaded / progressEvent.total
          onProgress(progress)
        }
      }
    })
    
    return response.data
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
   * Convert a tree item to geo-raster format for georeferencing (background task)
   * @param {string} itemId - The tree item ID
   * @returns {Promise<Object>} Task response with task_id
   */
  async convertToGeoRaster(itemId) {
    return await this.request(`/tree-items/${itemId}/convert-to-geo-raster`, {
      method: 'POST'
    })
  }

  /**
   * Get the status of a background task
   * @param {string} taskId - The task ID
   * @returns {Promise<Object>} Task status information
   */
  async getTaskStatus(taskId) {
    return await this.request(`/tasks/${taskId}/status`, {
      method: 'GET'
    })
  }

  /**
   * Cancel a background task
   * @param {string} taskId - The task ID
   * @returns {Promise<Object>} Cancellation result
   */
  async cancelTask(taskId) {
    return await this.request(`/tasks/${taskId}/cancel`, {
      method: 'POST'
    })
  }

  /**
   * Get the conversion status for a tree item
   * @param {string} itemId - The tree item ID
   * @returns {Promise<Object>} Conversion status information
   */
  async getConversionStatus(itemId) {
    return await this.request(`/tree-items/${itemId}/conversion-status`, {
      method: 'GET'
    })
  }

  /**
   * Reset georeferencing by removing warped file and restoring original file path
   * @param {string} fileId - The file ID
   * @returns {Promise<Object>} Reset result
   */
  async resetGeoreferencing(fileId) {
    return await this.request(`/files/${fileId}/reset-georeferencing`, {
      method: 'POST'
    })
  }
}

const apiService = new ApiService()
export default apiService