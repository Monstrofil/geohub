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

  /**
   * Upload a file to a specific commit
   * @param {File} file - The file to upload
   * @param {Object} tags - Tags to associate with the file
   * @param {string} commitId - The commit ID to upload to
   * @param {string} path - The path where the file should be placed (optional)
   * @param {string} name - The name for the file (optional, defaults to file.name)
   * @returns {Promise<Object>} The uploaded file response
   */
  async uploadFile(file, tags = {}, commitId, path = '', name = '') {
    if (!commitId) throw new Error('commitId is required for upload')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('tags', JSON.stringify(tags))
    formData.append('path', path)
    formData.append('name', name || file.name)

    const response = await fetch(`${this.baseUrl}/${commitId}/objects`, {
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
   * Create a collection in a specific commit
   * @param {string} name - The name of the collection
   * @param {string} commitId - The commit ID to create the collection in
   * @param {string} path - The path where the collection should be placed (optional)
   * @param {Object} tags - Tags to associate with the collection (optional)
   * @returns {Promise<Object>} The created collection response
   */
  async createCollection(name, commitId, path = '', tags = {}) {
    if (!commitId) throw new Error('commitId is required for collection creation')
    if (!name) throw new Error('name is required for collection creation')
    
    const formData = new FormData()
    formData.append('name', name)
    formData.append('path', path)
    formData.append('tags', JSON.stringify(tags))

    const response = await fetch(`${this.baseUrl}/${commitId}/objects`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Collection creation failed! status: ${response.status}`)
    }

    return await response.json()
  }

  // Get objects (tree entries) for a commit
  async getObjects(commitId, path, skip = 0, limit = 100) {
    if (!commitId) throw new Error('commitId is required')
      if (!!path) {
        var response = await this.request(`/${commitId}/${path}/objects`)
      }
      else {
        var response = await this.request(`/${commitId}/objects`)
      }
    // Return the objects array as files for compatibility
    return { files: response.objects, total: response.total, skip: response.skip, limit: response.limit }
  }

  async searchFiles(tags, skip = 0, limit = 100) {
    return await this.request('/files/search', {
      method: 'POST',
      body: JSON.stringify({ tags, skip, limit }),
    })
  }

  async searchFilesByName(name, skip = 0, limit = 100) {
    return await this.request('/files/search-by-name', {
      method: 'POST',
      body: JSON.stringify({ name, skip, limit }),
    })
  }

  // Branch/Ref operations
  async getRefs() {
    return await this.request('/refs')
  }

  async createBranch(branchName, baseRefName) {
    return await this.request('/refs', {
      method: 'POST',
      body: JSON.stringify({ 
        branch_name: branchName,
        base_ref_name: baseRefName
      })
    })
  }

  // Health check
  async healthCheck() {
    return await fetch('http://localhost:8000/health').then(res => res.json())
  }

  // Update a file object in a tree (by tree entry)
  async updateObjectInTree(commitId, treeEntryId, tags) {
    if (!commitId || !treeEntryId) throw new Error('commitId and treeEntryId are required')
    return await this.request(`/${commitId}/${treeEntryId}`, {
      method: 'PUT',
      body: JSON.stringify({ tags }),
    })
  }

  // Get a single tree entry (file) by commitId and treeEntryId
  async getTreeEntry(commitId, treeEntryId) {
    if (!commitId || !treeEntryId) throw new Error('commitId and treeEntryId are required')
    const response = await this.request(`/${commitId}/${treeEntryId}`)

    return response;
  }

  // Remove an object from a tree (by tree entry)
  async removeObjectInTree(commitId, path) {
    if (!commitId || !path) throw new Error('commitId and path are required')
    return await this.request(`/${commitId}/${path}`, {
      method: 'DELETE',
    })
  }

  // Clone an object from one path to another (keeping the same object reference)
  async cloneObjectInTree(commitId, sourcePath, targetPath) {
    if (!commitId || !sourcePath || !targetPath) throw new Error('commitId, sourcePath, and targetPath are required')
    return await this.request(`/${commitId}/clone`, {
      method: 'POST',
      body: JSON.stringify({ 
        source_path: sourcePath,
        target_path: targetPath
      }),
    })
  }
}

export default new ApiService() 