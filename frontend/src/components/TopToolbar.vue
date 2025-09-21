<template>
  <div class="top-toolbar">
    <!-- Left side: App branding and navigation -->
    <div class="toolbar-left">
      <router-link to="/" class="app-brand">
        <svg class="app-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14,2 14,8 20,8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10,9 9,9 8,9"/>
        </svg>
        <span class="app-title">GeoDocs Hub</span>
      </router-link>
      
      <!-- Collections button -->
      <router-link :to="{'name': 'FileList'}" class="collections-btn" title="Переглянути колекції">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 6a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V6z" stroke="currentColor" stroke-width="1.5" fill="none"/>
          <path d="M7 6v12M13 6v12" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        <span class="collections-text">Колекції</span>
      </router-link>
    </div>

    <!-- Right side: Auth -->
    <div class="toolbar-right">
      <AuthHeader />
    </div>
  </div>
</template>

<script setup>
import AuthHeader from './AuthHeader.vue'
</script>

<style scoped>
.top-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex: 1;
}

.toolbar-right {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
}

.app-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
  font-size: 1.1rem;
  text-decoration: none;
  color: white;
  transition: opacity 0.2s ease;
  cursor: pointer;
}

.app-brand:hover {
  opacity: 0.9;
  text-decoration: none;
}

.app-icon {
  width: 24px;
  height: 24px;
  color: rgba(255, 255, 255, 0.9);
}

.app-title {
  color: white;
  letter-spacing: 0.5px;
}

.collections-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: white;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
}

.collections-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
  text-decoration: none;
}

.collections-btn svg {
  width: 18px;
  height: 18px;
}

.collections-text {
  white-space: nowrap;
}

/* Mobile responsive styles */
@media (max-width: 768px) {
  .top-toolbar {
    padding: 0.5rem 0.75rem;
  }
  
  .toolbar-left {
    gap: 1rem;
  }
  
  .app-brand {
    font-size: 1rem;
  }
  
  .app-icon {
    width: 20px;
    height: 20px;
  }
  
  .collections-btn {
    padding: 0.4rem 0.75rem;
    font-size: 0.85rem;
  }
  
  .collections-btn svg {
    width: 16px;
    height: 16px;
  }
  
  .collections-text {
    display: none; /* Hide text on very small screens */
  }
}

</style> 