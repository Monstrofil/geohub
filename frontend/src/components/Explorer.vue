<template>
  <div class="pure-g app-grid">
    <!-- Branch Selector -->
    <BranchSelector v-model="currentBranch" :refs="refs" @onBranchChange="handleBranchChange" />
    <!-- File List View -->
    <div class="pure-u-1">
      <RouterView 
            :ref-name="currentBranch && currentBranch.name"
            :current-branch-name="currentBranch && currentBranch.name"
            :change-tracker="changeTracker"
            @branch-created="handleBranchCreated"
        />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BranchSelector from './BranchSelector.vue'
import { useChangeTracker } from '../composables/useChangeTracker.js'
import { loadFieldDefinitions } from '../utils/fieldResolver.js'
import apiService from '../services/api.js'

const route = useRoute()
const router = useRouter()

const allFieldDefinitions = ref({})

// Branch selector state
const currentBranch = ref(null)
const refs = ref([])

// Initialize change tracker
const changeTracker = useChangeTracker()

onMounted(async () => {
  // Load all field definitions
  allFieldDefinitions.value = await loadFieldDefinitions()
  // Load refs and set initial branch
  await loadRefsAndSetBranch()
})

function handleBranchChange(branch) {
  currentBranch.value = branch
  // Update the URL to reflect the new branch
  if (branch && branch.name !== route.params.branch) {
    router.push({
      name: 'FileList',
      params: { 
        ...route.params,
        branch: branch.name,
      },
      query: route.query
    })
  }
}

async function handleBranchCreated(newBranch) {
  // Refresh the refs list to show the new branch
  await loadRefsAndSetBranch()
  console.log('New branch created:', newBranch)
  // You might want to automatically switch to the new branch
  // currentBranch.value = newBranch
}

// Function to load refs and set the appropriate branch
async function loadRefsAndSetBranch() {
  try {
    const response = await apiService.getRefs()
    refs.value = response
    
    const routeBranchName = route.params.branch
    
    if (routeBranchName) {
      // Find the branch from route params
      const routeBranch = refs.value.find(ref => ref.name === routeBranchName)
      if (routeBranch) {
        currentBranch.value = routeBranch
      } else {
        // Fallback to first ref if route branch not found
        currentBranch.value = refs.value[0]
      }
    } else {
      // No route branch, use first ref
      currentBranch.value = refs.value[0]
    }
  } catch (err) {
    console.error('Failed to load refs:', err)
  }
}

// Watch for route changes to update the current branch
watch(() => route.params.branch, async (newBranchName) => {
  console.log("New branch route", newBranchName)
  if (newBranchName && refs.value.length > 0) {
    // Find the branch by name and set it as current
    const branch = refs.value.find(ref => ref.name === newBranchName)
    if (branch) {
      currentBranch.value = branch
    }
  }
}, { immediate: true })

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