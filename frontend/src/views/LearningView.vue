<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/composables/useApi'
import {
  AcademicCapIcon,
  ChartBarIcon,
  ClockIcon,
  ArrowPathIcon,
  SparklesIcon,
  TrashIcon,
  PencilIcon,
  AdjustmentsHorizontalIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  CheckCircleIcon
} from '@heroicons/vue/24/outline'

const stats = ref(null)
const patterns = ref([])
const loading = ref(true)
const refreshing = ref(false)
const searchQuery = ref('')
const sortBy = ref('last_used')
const sortOrder = ref('desc')
const showEditModal = ref(false)
const showConfidenceModal = ref(false)
const showImportModal = ref(false)
const selectedPattern = ref(null)
const importData = ref('')

const pagination = ref({
  total: 0,
  limit: 20,
  offset: 0
})

const sortOptions = [
  { value: 'last_used', label: 'Last Used' },
  { value: 'success_count', label: 'Success Count' },
  { value: 'execution_time', label: 'Execution Time' },
  { value: 'created_at', label: 'Created Date' }
]

async function loadStats() {
  try {
    const response = await api.get('/learning/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load learning stats:', error)
  }
}

async function loadPatterns() {
  loading.value = true
  try {
    const response = await api.get('/learning/patterns', {
      params: {
        limit: pagination.value.limit,
        offset: pagination.value.offset,
        sort_by: sortBy.value,
        sort_order: sortOrder.value
      }
    })
    patterns.value = response.data.patterns
    pagination.value.total = response.data.total
  } catch (error) {
    console.error('Failed to load patterns:', error)
    patterns.value = []
  } finally {
    loading.value = false
  }
}

async function refresh() {
  refreshing.value = true
  await Promise.all([loadStats(), loadPatterns()])
  refreshing.value = false
}

async function deletePattern(patternId) {
  if (!confirm('Are you sure you want to delete this pattern?')) return
  try {
    await api.delete(`/learning/patterns/${patternId}`)
    await loadPatterns()
    await loadStats()
  } catch (error) {
    console.error('Failed to delete pattern:', error)
  }
}

async function updatePattern() {
  if (!selectedPattern.value) return
  try {
    await api.put(`/learning/patterns/${selectedPattern.value.id}`, {
      query: selectedPattern.value.query,
      success_count: selectedPattern.value.success_count
    })
    showEditModal.value = false
    await loadPatterns()
  } catch (error) {
    console.error('Failed to update pattern:', error)
  }
}

async function adjustConfidence() {
  if (!selectedPattern.value) return
  try {
    await api.post(`/learning/patterns/${selectedPattern.value.id}/confidence`, {
      adjustment: selectedPattern.value.confidenceAdjustment
    })
    showConfidenceModal.value = false
    await loadPatterns()
  } catch (error) {
    console.error('Failed to adjust confidence:', error)
  }
}

async function bulkDeleteOldPatterns(days) {
  if (!confirm(`Delete all patterns older than ${days} days?`)) return
  try {
    const response = await api.post('/learning/patterns/bulk-delete', {
      older_than_days: days
    })
    alert(`Deleted ${response.data.deleted_count} patterns`)
    await loadPatterns()
    await loadStats()
  } catch (error) {
    console.error('Failed to bulk delete:', error)
  }
}

async function exportPatterns() {
  try {
    const response = await api.get('/learning/export')
    const blob = new Blob([response.data.data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `patterns_export_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to export patterns:', error)
  }
}

async function importPatterns() {
  try {
    const data = JSON.parse(importData.value)
    const response = await api.post('/learning/import', {
      data,
      workspace_id: localStorage.getItem('l0l1_workspace_id') || 'default',
      overwrite: false
    })
    alert(`Imported ${response.data.imported} patterns, skipped ${response.data.skipped}`)
    showImportModal.value = false
    importData.value = ''
    await loadPatterns()
    await loadStats()
  } catch (error) {
    console.error('Failed to import patterns:', error)
    alert('Failed to import: Invalid JSON format')
  }
}

function openEditModal(pattern) {
  selectedPattern.value = { ...pattern }
  showEditModal.value = true
}

function openConfidenceModal(pattern) {
  selectedPattern.value = { ...pattern, confidenceAdjustment: 0 }
  showConfidenceModal.value = true
}

function changePage(direction) {
  if (direction === 'next' && pagination.value.offset + pagination.value.limit < pagination.value.total) {
    pagination.value.offset += pagination.value.limit
    loadPatterns()
  } else if (direction === 'prev' && pagination.value.offset > 0) {
    pagination.value.offset -= pagination.value.limit
    loadPatterns()
  }
}

function onSortChange() {
  pagination.value.offset = 0
  loadPatterns()
}

const filteredPatterns = computed(() => {
  if (!searchQuery.value) return patterns.value
  const query = searchQuery.value.toLowerCase()
  return patterns.value.filter(p =>
    p.query.toLowerCase().includes(query)
  )
})

const confidenceColor = (confidence) => {
  if (confidence >= 0.8) return 'text-green-400'
  if (confidence >= 0.5) return 'text-yellow-400'
  return 'text-red-400'
}

onMounted(() => {
  loadStats()
  loadPatterns()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-white">Learning & Patterns</h2>
        <p class="text-sm text-dark-400">Manage learned SQL patterns and view statistics</p>
      </div>
      <div class="flex items-center space-x-2">
        <button @click="exportPatterns" class="btn-secondary flex items-center">
          <ArrowDownTrayIcon class="w-4 h-4 mr-2" />
          Export
        </button>
        <button @click="showImportModal = true" class="btn-secondary flex items-center">
          <ArrowUpTrayIcon class="w-4 h-4 mr-2" />
          Import
        </button>
        <button @click="refresh" :disabled="refreshing" class="btn-primary flex items-center">
          <ArrowPathIcon :class="['w-4 h-4 mr-2', refreshing && 'animate-spin']" />
          Refresh
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div v-if="stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-3 bg-purple-500/10 rounded-lg">
            <AcademicCapIcon class="w-6 h-6 text-purple-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-dark-400">Total Patterns</p>
            <p class="text-2xl font-bold text-white">{{ stats.total_queries || 0 }}</p>
          </div>
        </div>
      </div>

      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-3 bg-green-500/10 rounded-lg">
            <SparklesIcon class="w-6 h-6 text-green-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-dark-400">Recent Activity</p>
            <p class="text-2xl font-bold text-white">{{ stats.recent_activity || 0 }}</p>
          </div>
        </div>
      </div>

      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-3 bg-primary-500/10 rounded-lg">
            <ChartBarIcon class="w-6 h-6 text-primary-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-dark-400">Avg. Execution</p>
            <p class="text-2xl font-bold text-white">
              {{ stats.avg_execution_time ? stats.avg_execution_time.toFixed(2) + 's' : 'N/A' }}
            </p>
          </div>
        </div>
      </div>

      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-3 bg-yellow-500/10 rounded-lg">
            <ClockIcon class="w-6 h-6 text-yellow-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-dark-400">Top Pattern</p>
            <p class="text-lg font-semibold text-white truncate max-w-[150px]" :title="stats.most_successful?.query">
              {{ stats.most_successful?.success_count || 0 }} uses
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="card p-4">
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex-1 min-w-[200px]">
          <div class="relative">
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search patterns..."
              class="input pl-9"
            />
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <FunnelIcon class="w-4 h-4 text-dark-400" />
          <select v-model="sortBy" @change="onSortChange" class="input w-40">
            <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
          <select v-model="sortOrder" @change="onSortChange" class="input w-24">
            <option value="desc">Desc</option>
            <option value="asc">Asc</option>
          </select>
        </div>

        <div class="flex items-center space-x-2">
          <button
            @click="bulkDeleteOldPatterns(30)"
            class="btn-secondary btn-sm text-red-400 hover:text-red-300"
          >
            <TrashIcon class="w-4 h-4 mr-1" />
            Delete 30+ days
          </button>
          <button
            @click="bulkDeleteOldPatterns(90)"
            class="btn-secondary btn-sm text-red-400 hover:text-red-300"
          >
            <TrashIcon class="w-4 h-4 mr-1" />
            Delete 90+ days
          </button>
        </div>
      </div>
    </div>

    <!-- Patterns List -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent"></div>
    </div>

    <div v-else-if="filteredPatterns.length" class="space-y-3">
      <div
        v-for="pattern in filteredPatterns"
        :key="pattern.id"
        class="card p-4"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <pre class="text-sm text-dark-200 font-mono whitespace-pre-wrap break-all bg-dark-900/50 p-3 rounded-lg">{{ pattern.query }}</pre>
          </div>
          <div class="ml-4 flex items-center space-x-1">
            <button
              @click="openConfidenceModal(pattern)"
              class="p-1.5 rounded text-dark-400 hover:text-primary-400 hover:bg-dark-700"
              title="Adjust Confidence"
            >
              <AdjustmentsHorizontalIcon class="w-4 h-4" />
            </button>
            <button
              @click="openEditModal(pattern)"
              class="p-1.5 rounded text-dark-400 hover:text-primary-400 hover:bg-dark-700"
              title="Edit"
            >
              <PencilIcon class="w-4 h-4" />
            </button>
            <button
              @click="deletePattern(pattern.id)"
              class="p-1.5 rounded text-dark-400 hover:text-red-400 hover:bg-dark-700"
              title="Delete"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div class="mt-3 flex flex-wrap items-center gap-4 text-sm">
          <div class="flex items-center">
            <span class="text-dark-400 mr-2">Confidence:</span>
            <span :class="confidenceColor(pattern.confidence)" class="font-medium">
              {{ (pattern.confidence * 100).toFixed(0) }}%
            </span>
          </div>
          <div>
            <span class="text-dark-400">Uses:</span>
            <span class="text-dark-200 ml-1">{{ pattern.success_count }}</span>
          </div>
          <div>
            <span class="text-dark-400">Exec Time:</span>
            <span class="text-dark-200 ml-1">{{ pattern.execution_time.toFixed(3) }}s</span>
          </div>
          <div>
            <span class="text-dark-400">Results:</span>
            <span class="text-dark-200 ml-1">{{ pattern.result_count }}</span>
          </div>
          <div>
            <span class="text-dark-400">Last Used:</span>
            <span class="text-dark-200 ml-1">
              {{ new Date(pattern.last_used).toLocaleDateString() }}
            </span>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between pt-4">
        <p class="text-sm text-dark-400">
          Showing {{ pagination.offset + 1 }} - {{ Math.min(pagination.offset + pagination.limit, pagination.total) }}
          of {{ pagination.total }} patterns
        </p>
        <div class="flex space-x-2">
          <button
            @click="changePage('prev')"
            :disabled="pagination.offset === 0"
            class="btn-secondary btn-sm"
          >
            Previous
          </button>
          <button
            @click="changePage('next')"
            :disabled="pagination.offset + pagination.limit >= pagination.total"
            class="btn-secondary btn-sm"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card p-12 text-center">
      <AcademicCapIcon class="w-12 h-12 text-dark-600 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-white mb-2">No Patterns Found</h3>
      <p class="text-dark-400">
        {{ searchQuery ? 'No patterns match your search.' : 'Start using the SQL Workbench to build your knowledge base.' }}
      </p>
    </div>

    <!-- Edit Modal -->
    <Teleport to="body">
      <div
        v-if="showEditModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showEditModal = false"
      >
        <div class="card w-full max-w-2xl mx-4 p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Edit Pattern</h2>

          <div class="space-y-4">
            <div>
              <label class="label">SQL Query</label>
              <textarea
                v-model="selectedPattern.query"
                class="sql-editor h-32"
              ></textarea>
            </div>

            <div>
              <label class="label">Success Count</label>
              <input
                v-model.number="selectedPattern.success_count"
                type="number"
                min="1"
                class="input w-32"
              />
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button @click="showEditModal = false" class="btn-secondary">Cancel</button>
            <button @click="updatePattern" class="btn-primary">Save Changes</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Confidence Modal -->
    <Teleport to="body">
      <div
        v-if="showConfidenceModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showConfidenceModal = false"
      >
        <div class="card w-full max-w-md mx-4 p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Adjust Confidence</h2>

          <div class="space-y-4">
            <div>
              <p class="text-sm text-dark-400 mb-2">Current Confidence:</p>
              <p :class="['text-2xl font-bold', confidenceColor(selectedPattern.confidence)]">
                {{ (selectedPattern.confidence * 100).toFixed(0) }}%
              </p>
            </div>

            <div>
              <label class="label">Adjustment (-1.0 to 1.0)</label>
              <input
                v-model.number="selectedPattern.confidenceAdjustment"
                type="range"
                min="-1"
                max="1"
                step="0.1"
                class="w-full"
              />
              <div class="flex justify-between text-xs text-dark-400">
                <span>Decrease</span>
                <span class="font-medium text-primary-400">{{ selectedPattern.confidenceAdjustment }}</span>
                <span>Increase</span>
              </div>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button @click="showConfidenceModal = false" class="btn-secondary">Cancel</button>
            <button @click="adjustConfidence" class="btn-primary">Apply</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Import Modal -->
    <Teleport to="body">
      <div
        v-if="showImportModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showImportModal = false"
      >
        <div class="card w-full max-w-2xl mx-4 p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Import Patterns</h2>

          <div>
            <label class="label">Paste exported JSON</label>
            <textarea
              v-model="importData"
              class="sql-editor h-64"
              placeholder='{"patterns": [...], "exported_at": "..."}'
            ></textarea>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button @click="showImportModal = false" class="btn-secondary">Cancel</button>
            <button @click="importPatterns" :disabled="!importData.trim()" class="btn-primary">
              Import Patterns
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
