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
  async uploadFile(file, tags = {}) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('tags', JSON.stringify(tags))

    const response = await fetch(`${this.baseUrl}/files/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `Upload failed! status: ${response.status}`)
    }

    return await response.json()
  }

  async getFiles(skip = 0, limit = 100) {
    return await this.request(`/files?skip=${skip}&limit=${limit}`)
  }

  async getFile(fileId) {
    return await this.request(`/files/${fileId}`)
  }

  async deleteFile(fileId) {
    return await this.request(`/files/${fileId}`, { method: 'DELETE' })
  }

  async searchFiles(tags, skip = 0, limit = 100) {
    return await this.request('/files/search', {
      method: 'POST',
      body: JSON.stringify({ tags, skip, limit }),
    })
  }

  // Tag operations
  async getFileTags(fileId) {
    const response = await this.request(`/files/${fileId}/tags`)
    return response.tags || {}
  }

  async updateFileTags(fileId, tags) {
    const response = await this.request(`/files/${fileId}/tags`, {
      method: 'PUT',
      body: JSON.stringify({ tags }),
    })
    return response.tags || {}
  }

  async addTag(fileId, key, value) {
    const response = await this.request(`/files/${fileId}/tags/${encodeURIComponent(key)}`, {
      method: 'POST',
      body: JSON.stringify({ value }),
    })
    return response.tags || {}
  }

  async removeTag(fileId, key) {
    const response = await this.request(`/files/${fileId}/tags/${encodeURIComponent(key)}`, {
      method: 'DELETE',
    })
    return response.tags || {}
  }

  // Health check
  async healthCheck() {
    return await fetch('http://localhost:8000/health').then(res => res.json())
  }
}

export default new ApiService() 