<template>
  <div class="top-toolbar">
    <!-- Left side: App branding -->
    <div class="toolbar-left">
      <div class="app-brand">
        <svg class="app-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14,2 14,8 20,8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10,9 9,9 8,9"/>
        </svg>
        <span class="app-title">GeoDocs Hub</span>
      </div>
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

</style> 