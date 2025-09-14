import { ref, computed } from 'vue'
import apiService from '../services/api.js'

// Global reactive state
const user = ref(null)
const isLoading = ref(false)

// Initialize from localStorage if available
const storedUser = localStorage.getItem('user')
if (storedUser) {
  try {
    user.value = JSON.parse(storedUser)
  } catch (e) {
    console.error('Error parsing stored user data:', e)
    localStorage.removeItem('user')
  }
}

// Computed properties
export const isAuthenticated = computed(() => {
  return !!user.value && !!apiService.getToken()
})

export const currentUser = computed(() => user.value)

// Actions
export async function login(username, password) {
  isLoading.value = true
  try {
    const response = await apiService.login(username, password)
    user.value = response.user
    localStorage.setItem('user', JSON.stringify(response.user))
    return response
  } catch (error) {
    throw error
  } finally {
    isLoading.value = false
  }
}

export function logout() {
  user.value = null
  apiService.logout()
  localStorage.removeItem('user')
}

export async function refreshUser() {
  if (!apiService.getToken()) {
    return null
  }
  
  try {
    const userData = await apiService.getCurrentUser()
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
    return userData
  } catch (error) {
    console.error('Failed to refresh user data:', error)
    // If token is invalid, clear everything
    logout()
    throw error
  }
}

// Initialize user data if we have a token but no user data
export async function initializeAuth() {
  if (apiService.getToken() && !user.value) {
    try {
      await refreshUser()
    } catch (error) {
      // Token is invalid, clear it
      logout()
    }
  }
}

export { isLoading }
