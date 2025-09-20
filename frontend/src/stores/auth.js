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

// Listen for logout events from API service
window.addEventListener('auth-logout', () => {
  logout()
})

// Proactive token refresh - check every 5 minutes
let tokenRefreshInterval = null

function startTokenRefreshTimer() {
  stopTokenRefreshTimer()
  
  tokenRefreshInterval = setInterval(async () => {
    if (apiService.getToken() && apiService.getRefreshToken()) {
      try {
        // Try to decode the token to check expiry (simple check)
        const token = apiService.getToken()
        const payload = JSON.parse(atob(token.split('.')[1]))
        const now = Math.floor(Date.now() / 1000)
        const exp = payload.exp
        
        // Refresh if token expires in the next 5 minutes
        if (exp - now < 300) {
          console.log('Proactively refreshing token...')
          await apiService.refreshAccessToken()
        }
      } catch (error) {
        console.error('Error in proactive token refresh:', error)
        // If refresh fails, logout
        logout()
      }
    }
  }, 5 * 60 * 1000) // Check every 5 minutes
}

function stopTokenRefreshTimer() {
  if (tokenRefreshInterval) {
    clearInterval(tokenRefreshInterval)
    tokenRefreshInterval = null
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
    
    // Start proactive token refresh
    startTokenRefreshTimer()
    
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
  
  // Stop proactive token refresh
  stopTokenRefreshTimer()
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
      // Start proactive token refresh if user is already logged in
      startTokenRefreshTimer()
    } catch (error) {
      // Token is invalid, clear it
      logout()
    }
  } else if (apiService.getToken() && user.value) {
    // User already loaded and has token, start timer
    startTokenRefreshTimer()
  }
}

export { isLoading }
