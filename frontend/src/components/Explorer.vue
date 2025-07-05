<template>
  <div class="pure-g app-grid">
    <!-- Branch Selector -->
    <BranchSelector ref="branchSelectorRef" v-model="currentBranch" @onBranchChange="handleBranchChange" />
    <!-- File List View -->
    <div class="pure-u-1">
      <RouterView 
            :commit-id="currentBranch && currentBranch.commit_id"
            :current-branch-name="currentBranch && currentBranch.name"
            :change-tracker="changeTracker"
            @branch-created="handleBranchCreated"
        />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BranchSelector from './BranchSelector.vue'
import { useChangeTracker } from '../composables/useChangeTracker.js'
import { loadFieldDefinitions } from '../utils/fieldResolver.js'

const branchSelectorRef = ref(null)

const allFieldDefinitions = ref({})

// Branch selector state
const currentBranch = ref(null)

// Initialize change tracker
const changeTracker = useChangeTracker()

onMounted(async () => {
  // Load all field definitions
  allFieldDefinitions.value = await loadFieldDefinitions()
})

function handleBranchChange(branch) {
  currentBranch.value = branch
}

async function handleBranchCreated(newBranch) {
  // Refresh the branch selector to show the new branch
  if (branchSelectorRef.value) {
    await branchSelectorRef.value.loadRefs()
  }
  console.log('New branch created:', newBranch)
  // You might want to automatically switch to the new branch
  // currentBranch.value = newBranch
}

</script>

<style scoped>
.app-grid {
  min-height: 100vh;
  background: #fafbfc;
}

.section-feature-list {
  padding: 1rem;
  background: #f8f9fa;
}

.section-feature-list h3 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.file-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.15s;
}

.action-btn:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn {
  color: #666;
}

.refresh-btn:hover:not(:disabled) {
  border-color: #2196f3;
  color: #2196f3;
}

.upload-btn {
  color: #666;
}

.upload-btn:hover:not(:disabled) {
  border-color: #4caf50;
  color: #4caf50;
}

.feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-start;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.error {
  text-align: center;
  padding: 1rem;
  color: #d32f2f;
  background: #ffebee;
  border-radius: 4px;
  margin: 1rem 0;
}

.section-branch-selector {
  padding: 1rem;
  background: #e9f5ff;
  border-bottom: 1px solid #b3d8fd;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.current-branch {
  font-weight: bold;
  color: #1976d2;
}
</style> 