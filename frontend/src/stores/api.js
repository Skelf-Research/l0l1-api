import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/useApi'

export const useApiStore = defineStore('api', () => {
  const isConnected = ref(false)
  const healthData = ref(null)
  const lastCheck = ref(null)
  const error = ref(null)

  async function checkHealth() {
    try {
      const response = await api.get('/health')
      healthData.value = response.data
      isConnected.value = true
      lastCheck.value = new Date()
      error.value = null
      return response.data
    } catch (err) {
      isConnected.value = false
      error.value = err.message
      return null
    }
  }

  // Check health on startup and every 30 seconds
  function startHealthCheck() {
    checkHealth()
    setInterval(checkHealth, 30000)
  }

  return {
    isConnected,
    healthData,
    lastCheck,
    error,
    checkHealth,
    startHealthCheck
  }
})
