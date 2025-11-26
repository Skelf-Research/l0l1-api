<script setup>
import { ref } from 'vue'
import { useApiStore } from '@/stores/api'
import {
  Cog6ToothIcon,
  ServerIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  AcademicCapIcon
} from '@heroicons/vue/24/outline'

const apiStore = useApiStore()

const settings = ref({
  apiEndpoint: '/api',
  theme: 'dark',
  autoSave: true,
  showLineNumbers: true
})

function saveSettings() {
  localStorage.setItem('l0l1_settings', JSON.stringify(settings.value))
}
</script>

<template>
  <div class="max-w-4xl space-y-6">
    <!-- API Configuration -->
    <div class="card p-6">
      <div class="flex items-center mb-4">
        <ServerIcon class="w-5 h-5 text-primary-400 mr-2" />
        <h2 class="text-lg font-semibold text-white">API Configuration</h2>
      </div>

      <div class="space-y-4">
        <div>
          <label class="label">API Endpoint</label>
          <input
            v-model="settings.apiEndpoint"
            type="text"
            class="input"
            placeholder="/api"
          />
          <p class="text-xs text-dark-500 mt-1">
            The base URL for API requests
          </p>
        </div>

        <div class="p-4 bg-dark-900/50 rounded-lg">
          <h4 class="text-sm font-medium text-dark-200 mb-3">Current Status</h4>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-dark-400">Connection:</span>
              <span :class="apiStore.isConnected ? 'text-green-400' : 'text-red-400'" class="ml-2">
                {{ apiStore.isConnected ? 'Connected' : 'Disconnected' }}
              </span>
            </div>
            <div v-if="apiStore.healthData">
              <span class="text-dark-400">Version:</span>
              <span class="text-dark-200 ml-2">{{ apiStore.healthData.version }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Provider Settings -->
    <div class="card p-6">
      <div class="flex items-center mb-4">
        <CpuChipIcon class="w-5 h-5 text-primary-400 mr-2" />
        <h2 class="text-lg font-semibold text-white">AI Provider</h2>
      </div>

      <div class="p-4 bg-dark-900/50 rounded-lg">
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-dark-400">Provider:</span>
            <span class="text-dark-200 ml-2">
              {{ apiStore.healthData?.ai_provider || 'Unknown' }}
            </span>
          </div>
          <div>
            <span class="text-dark-400">Model:</span>
            <span class="text-dark-200 ml-2">
              {{ apiStore.healthData?.completion_model || 'Unknown' }}
            </span>
          </div>
        </div>
        <p class="text-xs text-dark-500 mt-3">
          AI provider settings are configured on the server via environment variables.
        </p>
      </div>
    </div>

    <!-- Feature Settings -->
    <div class="card p-6">
      <div class="flex items-center mb-4">
        <ShieldCheckIcon class="w-5 h-5 text-primary-400 mr-2" />
        <h2 class="text-lg font-semibold text-white">Features</h2>
      </div>

      <div class="space-y-4">
        <div class="flex items-center justify-between p-4 bg-dark-900/50 rounded-lg">
          <div>
            <h4 class="text-sm font-medium text-dark-200">PII Detection</h4>
            <p class="text-xs text-dark-500">Automatically detect personally identifiable information</p>
          </div>
          <span :class="apiStore.healthData?.pii_enabled ? 'badge-success' : 'badge-warning'">
            {{ apiStore.healthData?.pii_enabled ? 'Enabled' : 'Disabled' }}
          </span>
        </div>

        <div class="flex items-center justify-between p-4 bg-dark-900/50 rounded-lg">
          <div>
            <h4 class="text-sm font-medium text-dark-200">Continuous Learning</h4>
            <p class="text-xs text-dark-500">Learn from successful queries to improve suggestions</p>
          </div>
          <span :class="apiStore.healthData?.learning_enabled ? 'badge-success' : 'badge-warning'">
            {{ apiStore.healthData?.learning_enabled ? 'Enabled' : 'Disabled' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Editor Settings -->
    <div class="card p-6">
      <div class="flex items-center mb-4">
        <Cog6ToothIcon class="w-5 h-5 text-primary-400 mr-2" />
        <h2 class="text-lg font-semibold text-white">Editor Settings</h2>
      </div>

      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h4 class="text-sm font-medium text-dark-200">Show Line Numbers</h4>
            <p class="text-xs text-dark-500">Display line numbers in SQL editor</p>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              v-model="settings.showLineNumbers"
              @change="saveSettings"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
          </label>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <h4 class="text-sm font-medium text-dark-200">Auto-save</h4>
            <p class="text-xs text-dark-500">Automatically save queries to local storage</p>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              v-model="settings.autoSave"
              @change="saveSettings"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-dark-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
          </label>
        </div>
      </div>
    </div>

    <!-- About -->
    <div class="card p-6">
      <div class="flex items-center mb-4">
        <AcademicCapIcon class="w-5 h-5 text-primary-400 mr-2" />
        <h2 class="text-lg font-semibold text-white">About l0l1</h2>
      </div>

      <div class="text-sm text-dark-400 space-y-2">
        <p>
          l0l1 is an AI-powered SQL analysis and validation platform that helps you write better SQL queries.
        </p>
        <p>
          Features include syntax validation, query explanation, auto-completion, error correction, PII detection, and continuous learning.
        </p>
        <div class="pt-4 border-t border-dark-700 mt-4">
          <p class="text-dark-500">
            Version: {{ apiStore.healthData?.version || '0.2.0' }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
