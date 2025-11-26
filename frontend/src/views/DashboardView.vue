<script setup>
import { ref, onMounted, computed } from 'vue'
import { useApiStore } from '@/stores/api'
import api, { learningApi } from '@/composables/useApi'
import {
  ServerIcon,
  CpuChipIcon,
  CircleStackIcon,
  AcademicCapIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon
} from '@heroicons/vue/24/outline'

const apiStore = useApiStore()
const learningStats = ref(null)
const loading = ref(true)

const stats = computed(() => [
  {
    name: 'API Status',
    value: apiStore.isConnected ? 'Connected' : 'Disconnected',
    icon: ServerIcon,
    color: apiStore.isConnected ? 'text-green-400' : 'text-red-400',
    bgColor: apiStore.isConnected ? 'bg-green-500/10' : 'bg-red-500/10'
  },
  {
    name: 'AI Provider',
    value: apiStore.healthData?.ai_provider || 'Unknown',
    icon: CpuChipIcon,
    color: 'text-primary-400',
    bgColor: 'bg-primary-500/10'
  },
  {
    name: 'Learned Patterns',
    value: learningStats.value?.total_patterns || '0',
    icon: AcademicCapIcon,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10'
  },
  {
    name: 'PII Detection',
    value: apiStore.healthData?.pii_enabled ? 'Enabled' : 'Disabled',
    icon: CircleStackIcon,
    color: apiStore.healthData?.pii_enabled ? 'text-green-400' : 'text-yellow-400',
    bgColor: apiStore.healthData?.pii_enabled ? 'bg-green-500/10' : 'bg-yellow-500/10'
  }
])

const features = [
  {
    name: 'SQL Validation',
    description: 'Validate SQL syntax and semantics with AI-powered analysis',
    status: 'active'
  },
  {
    name: 'Query Explanation',
    description: 'Get natural language explanations for complex SQL queries',
    status: 'active'
  },
  {
    name: 'Auto-Completion',
    description: 'AI-powered query completion based on context and schema',
    status: 'active'
  },
  {
    name: 'Error Correction',
    description: 'Automatically fix common SQL syntax and logical errors',
    status: 'active'
  },
  {
    name: 'PII Detection',
    description: 'Detect and anonymize personally identifiable information',
    status: 'active'
  },
  {
    name: 'Continuous Learning',
    description: 'Learn from successful queries to improve suggestions',
    status: 'active'
  }
]

async function loadStats() {
  loading.value = true
  try {
    const response = await learningApi.getStats()
    learningStats.value = response.data
  } catch (error) {
    console.error('Failed to load learning stats:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="stat in stats"
        :key="stat.name"
        class="card p-5"
      >
        <div class="flex items-center">
          <div :class="['p-3 rounded-lg', stat.bgColor]">
            <component :is="stat.icon" :class="['w-6 h-6', stat.color]" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-dark-400">{{ stat.name }}</p>
            <p class="text-lg font-semibold text-white">{{ stat.value }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Features Status -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-white mb-4">Platform Features</h2>
        <div class="space-y-3">
          <div
            v-for="feature in features"
            :key="feature.name"
            class="flex items-center justify-between p-3 bg-dark-900/50 rounded-lg"
          >
            <div>
              <p class="text-sm font-medium text-dark-100">{{ feature.name }}</p>
              <p class="text-xs text-dark-400">{{ feature.description }}</p>
            </div>
            <CheckCircleIcon
              v-if="feature.status === 'active'"
              class="w-5 h-5 text-green-400"
            />
            <ExclamationTriangleIcon
              v-else-if="feature.status === 'warning'"
              class="w-5 h-5 text-yellow-400"
            />
            <XCircleIcon
              v-else
              class="w-5 h-5 text-red-400"
            />
          </div>
        </div>
      </div>

      <!-- Quick Start -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-white mb-4">Quick Start</h2>
        <div class="space-y-4">
          <div class="p-4 bg-dark-900/50 rounded-lg">
            <h3 class="text-sm font-medium text-primary-400 mb-2">1. Open SQL Workbench</h3>
            <p class="text-sm text-dark-400">
              Navigate to the SQL Workbench to start analyzing, validating, and improving your SQL queries.
            </p>
          </div>
          <div class="p-4 bg-dark-900/50 rounded-lg">
            <h3 class="text-sm font-medium text-primary-400 mb-2">2. Create a Workspace</h3>
            <p class="text-sm text-dark-400">
              Organize your work by creating workspaces. Each workspace can have its own schema and settings.
            </p>
          </div>
          <div class="p-4 bg-dark-900/50 rounded-lg">
            <h3 class="text-sm font-medium text-primary-400 mb-2">3. Start Learning</h3>
            <p class="text-sm text-dark-400">
              As you use the platform, it learns from your successful queries to provide better suggestions.
            </p>
          </div>
        </div>

        <div class="mt-6 flex space-x-3">
          <RouterLink to="/workbench" class="btn-primary">
            Open Workbench
          </RouterLink>
          <RouterLink to="/workspaces" class="btn-secondary">
            Manage Workspaces
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- API Health Details -->
    <div v-if="apiStore.healthData" class="card p-6">
      <h2 class="text-lg font-semibold text-white mb-4">API Health Details</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="p-4 bg-dark-900/50 rounded-lg">
          <p class="text-xs text-dark-400 uppercase tracking-wide">Version</p>
          <p class="text-lg font-semibold text-white">{{ apiStore.healthData.version || 'N/A' }}</p>
        </div>
        <div class="p-4 bg-dark-900/50 rounded-lg">
          <p class="text-xs text-dark-400 uppercase tracking-wide">Status</p>
          <p class="text-lg font-semibold text-green-400">{{ apiStore.healthData.status || 'N/A' }}</p>
        </div>
        <div class="p-4 bg-dark-900/50 rounded-lg">
          <p class="text-xs text-dark-400 uppercase tracking-wide">Learning Enabled</p>
          <p class="text-lg font-semibold text-white">
            {{ apiStore.healthData.learning_enabled ? 'Yes' : 'No' }}
          </p>
        </div>
        <div class="p-4 bg-dark-900/50 rounded-lg">
          <p class="text-xs text-dark-400 uppercase tracking-wide">Last Check</p>
          <p class="text-lg font-semibold text-white">
            {{ apiStore.lastCheck ? new Date(apiStore.lastCheck).toLocaleTimeString() : 'Never' }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
