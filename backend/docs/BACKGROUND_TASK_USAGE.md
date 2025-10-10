# Background Task Usage Examples

This document provides practical examples of how to use the new background task system for geo-raster conversion.

## Frontend Integration Example

### 1. Start Conversion

```javascript
// Start the conversion process
async function startConversion(fileId) {
    try {
        const response = await fetch(`/api/v1/tree-items/${fileId}/convert-to-geo-raster`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            console.log('Conversion started:', result.task_id);
            return result.task_id;
        } else {
            throw new Error(result.detail || 'Failed to start conversion');
        }
    } catch (error) {
        console.error('Error starting conversion:', error);
        throw error;
    }
}
```

### 2. Monitor Progress

```javascript
// Monitor task progress with polling
async function monitorTaskProgress(taskId, onProgress, onComplete, onError) {
    const pollInterval = 2000; // Poll every 2 seconds
    
    const poll = async () => {
        try {
            const response = await fetch(`/api/v1/tasks/${taskId}/status`);
            const status = await response.json();
            
            if (response.ok) {
                // Call progress callback
                onProgress(status);
                
                // Check if task is complete
                if (status.state === 'SUCCESS') {
                    onComplete(status);
                    return; // Stop polling
                } else if (status.state === 'FAILURE') {
                    onError(status);
                    return; // Stop polling
                } else {
                    // Continue polling
                    setTimeout(poll, pollInterval);
                }
            } else {
                onError({ error: 'Failed to get task status' });
            }
        } catch (error) {
            onError({ error: error.message });
        }
    };
    
    // Start polling
    poll();
}
```

### 3. Complete Example with UI

```javascript
class GeoRasterConverter {
    constructor(fileId, token) {
        this.fileId = fileId;
        this.token = token;
        this.taskId = null;
    }
    
    async startConversion() {
        try {
            // Show loading state
            this.showProgress(0, 'Starting conversion...');
            
            // Start the conversion
            const result = await this.startConversionTask();
            this.taskId = result.task_id;
            
            // Start monitoring
            this.monitorProgress();
            
        } catch (error) {
            this.showError('Failed to start conversion: ' + error.message);
        }
    }
    
    async startConversionTask() {
        const response = await fetch(`/api/v1/tree-items/${this.fileId}/convert-to-geo-raster`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start conversion');
        }
        
        return await response.json();
    }
    
    monitorProgress() {
        const pollInterval = 2000;
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/v1/tasks/${this.taskId}/status`);
                const status = await response.json();
                
                if (response.ok) {
                    this.showProgress(status.progress, status.status);
                    
                    if (status.state === 'SUCCESS') {
                        this.showSuccess('Conversion completed successfully!');
                        this.onConversionComplete(status.result);
                    } else if (status.state === 'FAILURE') {
                        this.showError('Conversion failed: ' + (status.error || 'Unknown error'));
                    } else {
                        // Continue polling
                        setTimeout(poll, pollInterval);
                    }
                } else {
                    this.showError('Failed to get task status');
                }
            } catch (error) {
                this.showError('Error monitoring progress: ' + error.message);
            }
        };
        
        poll();
    }
    
    showProgress(progress, message) {
        // Update UI with progress
        const progressBar = document.getElementById('conversion-progress');
        const statusText = document.getElementById('conversion-status');
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }
        
        if (statusText) {
            statusText.textContent = message;
        }
    }
    
    showSuccess(message) {
        // Show success message
        console.log('SUCCESS:', message);
        // Update UI accordingly
    }
    
    showError(message) {
        // Show error message
        console.error('ERROR:', message);
        // Update UI accordingly
    }
    
    onConversionComplete(result) {
        // Handle successful conversion
        console.log('Conversion complete:', result);
        // Refresh file list, update UI, etc.
    }
    
    async cancelConversion() {
        if (!this.taskId) return;
        
        try {
            const response = await fetch(`/api/v1/tasks/${this.taskId}/cancel`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                this.showSuccess('Conversion cancelled');
            } else {
                this.showError('Failed to cancel conversion');
            }
        } catch (error) {
            this.showError('Error cancelling conversion: ' + error.message);
        }
    }
}

// Usage example
const converter = new GeoRasterConverter('file-uuid-here', 'auth-token');
converter.startConversion();
```

## Vue.js Component Example

```vue
<template>
  <div class="conversion-panel">
    <div v-if="!isConverting && !isCompleted" class="start-section">
      <button @click="startConversion" :disabled="!canConvert">
        Convert to Geo-Raster
      </button>
    </div>
    
    <div v-if="isConverting" class="progress-section">
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: progress + '%' }"
        ></div>
      </div>
      <p class="status-text">{{ statusMessage }}</p>
      <button @click="cancelConversion" class="cancel-btn">
        Cancel
      </button>
    </div>
    
    <div v-if="isCompleted" class="completed-section">
      <p class="success-message">✅ Conversion completed successfully!</p>
      <button @click="reset">Convert Another File</button>
    </div>
    
    <div v-if="error" class="error-section">
      <p class="error-message">❌ {{ error }}</p>
      <button @click="reset">Try Again</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GeoRasterConverter',
  props: {
    fileId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      taskId: null,
      progress: 0,
      statusMessage: '',
      isConverting: false,
      isCompleted: false,
      error: null,
      pollInterval: null
    }
  },
  computed: {
    canConvert() {
      return this.fileId && !this.isConverting && !this.isCompleted;
    }
  },
  methods: {
    async startConversion() {
      try {
        this.isConverting = true;
        this.error = null;
        this.progress = 0;
        this.statusMessage = 'Starting conversion...';
        
        const response = await this.$api.post(`/tree-items/${this.fileId}/convert-to-geo-raster`);
        this.taskId = response.data.task_id;
        
        this.monitorProgress();
        
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to start conversion';
        this.isConverting = false;
      }
    },
    
    monitorProgress() {
      this.pollInterval = setInterval(async () => {
        try {
          const response = await this.$api.get(`/tasks/${this.taskId}/status`);
          const status = response.data;
          
          this.progress = status.progress;
          this.statusMessage = status.status;
          
          if (status.state === 'SUCCESS') {
            this.isConverting = false;
            this.isCompleted = true;
            this.clearPolling();
            this.$emit('conversion-complete', status.result);
          } else if (status.state === 'FAILURE') {
            this.error = status.error || 'Conversion failed';
            this.isConverting = false;
            this.clearPolling();
          }
          
        } catch (error) {
          this.error = 'Failed to monitor progress';
          this.isConverting = false;
          this.clearPolling();
        }
      }, 2000);
    },
    
    async cancelConversion() {
      if (!this.taskId) return;
      
      try {
        await this.$api.post(`/tasks/${this.taskId}/cancel`);
        this.isConverting = false;
        this.clearPolling();
        this.statusMessage = 'Conversion cancelled';
      } catch (error) {
        this.error = 'Failed to cancel conversion';
      }
    },
    
    clearPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }
    },
    
    reset() {
      this.taskId = null;
      this.progress = 0;
      this.statusMessage = '';
      this.isConverting = false;
      this.isCompleted = false;
      this.error = null;
      this.clearPolling();
    }
  },
  
  beforeUnmount() {
    this.clearPolling();
  }
}
</script>

<style scoped>
.conversion-panel {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background-color: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
  margin: 10px 0;
}

.progress-fill {
  height: 100%;
  background-color: #4CAF50;
  transition: width 0.3s ease;
}

.status-text {
  margin: 10px 0;
  font-weight: bold;
}

.cancel-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.success-message {
  color: #4CAF50;
  font-weight: bold;
}

.error-message {
  color: #f44336;
  font-weight: bold;
}
</style>
```

## Backend Testing Example

```python
import asyncio
import requests
import time

def test_background_conversion():
    """Test the background conversion process"""
    
    # 1. Start conversion
    print("Starting conversion...")
    response = requests.post(
        "http://localhost:8000/api/v1/tree-items/your-file-id/convert-to-geo-raster",
        headers={"Authorization": "Bearer your-token"}
    )
    
    if response.status_code != 200:
        print(f"Failed to start conversion: {response.text}")
        return
    
    task_data = response.json()
    task_id = task_data["task_id"]
    print(f"Conversion started with task ID: {task_id}")
    
    # 2. Monitor progress
    print("Monitoring progress...")
    while True:
        status_response = requests.get(
            f"http://localhost:8000/api/v1/tasks/{task_id}/status"
        )
        
        if status_response.status_code != 200:
            print(f"Failed to get status: {status_response.text}")
            break
        
        status = status_response.json()
        print(f"Progress: {status['progress']}% - {status['status']}")
        
        if status["state"] == "SUCCESS":
            print("✅ Conversion completed successfully!")
            print(f"Result: {status['result']}")
            break
        elif status["state"] == "FAILURE":
            print(f"❌ Conversion failed: {status['error']}")
            break
        
        time.sleep(2)  # Poll every 2 seconds

if __name__ == "__main__":
    test_background_conversion()
```

## Error Handling Best Practices

1. **Always handle network errors** when polling for status
2. **Implement exponential backoff** for retry logic
3. **Set reasonable timeouts** for API calls
4. **Provide user feedback** for all states (pending, progress, success, failure)
5. **Allow task cancellation** for long-running operations
6. **Clean up resources** when components unmount

## Performance Tips

1. **Poll every 2-3 seconds** to balance responsiveness and server load
2. **Stop polling** when task completes or fails
3. **Cache task status** briefly to avoid redundant API calls
4. **Use WebSockets** for real-time updates in production (future enhancement)
5. **Implement task queuing** on the frontend to avoid overwhelming the server

