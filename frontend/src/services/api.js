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

  // File operations
  async uploadFile(file, tags = {}, commitId) {
    if (!commitId) throw new Error('commitId is required for upload')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('tags', JSON.stringify(tags))

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

  // Get objects (tree entries) for a commit
  async getObjects(commitId, skip = 0, limit = 100) {
    if (!commitId) throw new Error('commitId is required')
    const response = await this.request(`/${commitId}/objects?skip=${skip}&limit=${limit}`)
    // Return the objects array as files for compatibility
    return { files: response.objects, total: response.total, skip: response.skip, limit: response.limit }
  }

  async searchFiles(tags, skip = 0, limit = 100) {
    return await this.request('/files/search', {
      method: 'POST',
      body: JSON.stringify({ tags, skip, limit }),
    })
  }

  // Branch/Ref operations
  async getRefs() {
    return await this.request('/refs')
  }

  // Health check
  async healthCheck() {
    return await fetch('http://localhost:8000/health').then(res => res.json())
  }

  // Update a file object in a tree (by tree entry)
  async updateObjectInTree(commitId, treeEntryId, tags) {
    if (!commitId || !treeEntryId) throw new Error('commitId and treeEntryId are required')
    return await this.request(`/${commitId}/objects/${treeEntryId}`, {
      method: 'PUT',
      body: JSON.stringify({ tags }),
    })
  }
}

export default new ApiService() 