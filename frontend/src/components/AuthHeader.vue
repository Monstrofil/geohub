<template>
  <div class="auth-header">
    <div v-if="isAuthenticated" class="user-info">
      <div class="user-details">
        <span class="username">{{ currentUser?.username }}</span>
        <span v-if="currentUser?.is_admin" class="admin-badge">Admin</span>
      </div>
      <button @click="handleLogout" class="logout-button">
        <svg class="logout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
          <polyline points="16,17 21,12 16,7"/>
          <line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        Logout
      </button>
    </div>
    <div v-else class="login-prompt">
      <router-link :to="loginUrl" class="login-link">Login</router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isAuthenticated, currentUser, logout } from '../stores/auth.js'

const router = useRouter()
const route = useRoute()

// Create login URL with current path as redirect
const loginUrl = computed(() => {
  const redirectParam = encodeURIComponent(route.fullPath)
  return `/login?redirect=${redirectParam}`
})

async function handleLogout() {
  logout()
  router.push('/')
}
</script>

<style scoped>
.auth-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-details {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.admin-badge {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.logout-button {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.logout-icon {
  width: 16px;
  height: 16px;
}

.login-prompt {
  display: flex;
  align-items: center;
}

.login-link {
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-weight: 500;
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  transition: all 0.2s ease;
  background: rgba(255, 255, 255, 0.1);
}

.login-link:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}
</style>
