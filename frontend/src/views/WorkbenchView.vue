<script setup>
import { ref, computed } from 'vue'
import { sqlApi } from '@/composables/useApi'
import {
  PlayIcon,
  CheckCircleIcon,
  LightBulbIcon,
  WrenchScrewdriverIcon,
  ShieldExclamationIcon,
  DocumentMagnifyingGlassIcon,
  ClipboardDocumentIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'

const query = ref('')
const activeTab = ref('validate')
const loading = ref(false)
const result = ref(null)
const error = ref(null)

const tabs = [
  { id: 'validate', name: 'Validate', icon: CheckCircleIcon },
  { id: 'explain', name: 'Explain', icon: LightBulbIcon },
  { id: 'complete', name: 'Complete', icon: DocumentMagnifyingGlassIcon },
  { id: 'correct', name: 'Correct', icon: WrenchScrewdriverIcon },
  { id: 'pii', name: 'Check PII', icon: ShieldExclamationIcon }
]

const sampleQueries = [
  {
    name: 'Simple Select',
    query: 'SELECT id, name, email FROM users WHERE status = \'active\' ORDER BY created_at DESC LIMIT 10'
  },
  {
    name: 'Join Query',
    query: 'SELECT o.id, u.name, o.total FROM orders o JOIN users u ON o.user_id = u.id WHERE o.created_at > \'2024-01-01\''
  },
  {
    name: 'With PII',
    query: 'SELECT name, email, phone, ssn FROM customers WHERE email = \'john@example.com\''
  },
  {
    name: 'Broken Query',
    query: 'SELEC * FORM users WHER id = 1'
  }
]

async function runAnalysis() {
  if (!query.value.trim()) return

  loading.value = true
  result.value = null
  error.value = null

  try {
    let response
    switch (activeTab.value) {
      case 'validate':
        response = await sqlApi.validate(query.value)
        break
      case 'explain':
        response = await sqlApi.explain(query.value)
        break
      case 'complete':
        response = await sqlApi.complete(query.value)
        break
      case 'correct':
        response = await sqlApi.correct(query.value)
        break
      case 'pii':
        response = await sqlApi.checkPii(query.value)
        break
    }
    result.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'An error occurred'
  } finally {
    loading.value = false
  }
}

function loadSample(sample) {
  query.value = sample.query
}

function clearAll() {
  query.value = ''
  result.value = null
  error.value = null
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
}

function applySuggestion(newQuery) {
  query.value = newQuery
}
</script>

<template>
  <div class="flex flex-col h-full space-y-4">
    <!-- Toolbar -->
    <div class="flex items-center justify-between">
      <!-- Tabs -->
      <div class="flex bg-dark-800 rounded-lg p-1">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors',
            activeTab === tab.id
              ? 'bg-primary-600 text-white'
              : 'text-dark-400 hover:text-dark-100'
          ]"
        >
          <component :is="tab.icon" class="w-4 h-4 mr-2" />
          {{ tab.name }}
        </button>
      </div>

      <!-- Actions -->
      <div class="flex items-center space-x-2">
        <button
          @click="clearAll"
          class="btn-secondary btn-sm flex items-center"
        >
          <TrashIcon class="w-4 h-4 mr-1" />
          Clear
        </button>
        <button
          @click="runAnalysis"
          :disabled="!query.trim() || loading"
          class="btn-primary flex items-center"
        >
          <PlayIcon class="w-4 h-4 mr-2" />
          {{ loading ? 'Analyzing...' : 'Run Analysis' }}
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
      <!-- Editor Panel -->
      <div class="card flex flex-col">
        <div class="flex items-center justify-between px-4 py-3 border-b border-dark-700">
          <h3 class="text-sm font-medium text-dark-200">SQL Query</h3>
          <div class="flex items-center space-x-2">
            <button
              @click="copyToClipboard(query)"
              class="p-1.5 rounded text-dark-400 hover:text-dark-100 hover:bg-dark-700 transition-colors"
              title="Copy to clipboard"
            >
              <ClipboardDocumentIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
        <div class="flex-1 p-4">
          <textarea
            v-model="query"
            @keydown.ctrl.enter="runAnalysis"
            class="sql-editor h-full"
            placeholder="Enter your SQL query here...

Example: SELECT * FROM users WHERE created_at > '2024-01-01'"
          ></textarea>
        </div>

        <!-- Sample Queries -->
        <div class="px-4 py-3 border-t border-dark-700">
          <p class="text-xs text-dark-400 mb-2">Sample Queries:</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="sample in sampleQueries"
              :key="sample.name"
              @click="loadSample(sample)"
              class="px-2 py-1 text-xs bg-dark-700 hover:bg-dark-600 rounded text-dark-300 transition-colors"
            >
              {{ sample.name }}
            </button>
          </div>
        </div>
      </div>

      <!-- Results Panel -->
      <div class="card flex flex-col overflow-hidden">
        <div class="flex items-center justify-between px-4 py-3 border-b border-dark-700">
          <h3 class="text-sm font-medium text-dark-200">Results</h3>
          <span class="badge-info" v-if="result">
            {{ activeTab.charAt(0).toUpperCase() + activeTab.slice(1) }}
          </span>
        </div>

        <div class="flex-1 overflow-auto p-4">
          <!-- Loading -->
          <div v-if="loading" class="flex items-center justify-center h-full">
            <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent"></div>
          </div>

          <!-- Error -->
          <div v-else-if="error" class="p-4 bg-red-900/20 border border-red-800 rounded-lg">
            <p class="text-red-400 text-sm">{{ error }}</p>
          </div>

          <!-- Results -->
          <div v-else-if="result" class="space-y-4">
            <!-- Validation Result -->
            <template v-if="activeTab === 'validate'">
              <div
                :class="[
                  'p-4 rounded-lg border',
                  result.is_valid
                    ? 'bg-green-900/20 border-green-800'
                    : 'bg-red-900/20 border-red-800'
                ]"
              >
                <div class="flex items-center">
                  <CheckCircleIcon
                    v-if="result.is_valid"
                    class="w-5 h-5 text-green-400"
                  />
                  <ShieldExclamationIcon v-else class="w-5 h-5 text-red-400" />
                  <span
                    :class="[
                      'ml-2 font-medium',
                      result.is_valid ? 'text-green-400' : 'text-red-400'
                    ]"
                  >
                    {{ result.is_valid ? 'Valid SQL' : 'Invalid SQL' }}
                  </span>
                </div>
                <p v-if="result.message" class="mt-2 text-sm text-dark-300">
                  {{ result.message }}
                </p>
              </div>

              <div v-if="result.suggestions?.length" class="space-y-2">
                <p class="text-sm font-medium text-dark-300">Suggestions:</p>
                <div
                  v-for="(suggestion, i) in result.suggestions"
                  :key="i"
                  class="p-3 bg-dark-900/50 rounded-lg text-sm text-dark-200"
                >
                  {{ suggestion }}
                </div>
              </div>
            </template>

            <!-- Explanation Result -->
            <template v-else-if="activeTab === 'explain'">
              <div class="prose prose-invert prose-sm max-w-none">
                <p class="text-dark-200 whitespace-pre-wrap">{{ result.explanation }}</p>
              </div>
            </template>

            <!-- Completion Result -->
            <template v-else-if="activeTab === 'complete'">
              <div class="space-y-3">
                <p class="text-sm text-dark-400">Suggested completions:</p>
                <div
                  v-for="(completion, i) in (result.completions || [result.completion])"
                  :key="i"
                  class="p-3 bg-dark-900 rounded-lg"
                >
                  <pre class="text-sm text-primary-300 font-mono whitespace-pre-wrap">{{ completion }}</pre>
                  <button
                    @click="applySuggestion(completion)"
                    class="mt-2 text-xs text-primary-400 hover:text-primary-300"
                  >
                    Apply this suggestion
                  </button>
                </div>
              </div>
            </template>

            <!-- Correction Result -->
            <template v-else-if="activeTab === 'correct'">
              <div class="space-y-4">
                <div class="p-4 bg-green-900/20 border border-green-800 rounded-lg">
                  <p class="text-sm text-dark-400 mb-2">Corrected Query:</p>
                  <pre class="text-sm text-green-300 font-mono whitespace-pre-wrap">{{ result.corrected_query }}</pre>
                  <button
                    @click="applySuggestion(result.corrected_query)"
                    class="mt-3 btn-sm btn-success"
                  >
                    Apply Correction
                  </button>
                </div>
                <div v-if="result.changes?.length" class="space-y-2">
                  <p class="text-sm font-medium text-dark-300">Changes made:</p>
                  <ul class="list-disc list-inside space-y-1">
                    <li
                      v-for="(change, i) in result.changes"
                      :key="i"
                      class="text-sm text-dark-400"
                    >
                      {{ change }}
                    </li>
                  </ul>
                </div>
              </div>
            </template>

            <!-- PII Check Result -->
            <template v-else-if="activeTab === 'pii'">
              <div class="space-y-4">
                <div
                  :class="[
                    'p-4 rounded-lg border',
                    result.has_pii
                      ? 'bg-yellow-900/20 border-yellow-800'
                      : 'bg-green-900/20 border-green-800'
                  ]"
                >
                  <div class="flex items-center">
                    <ShieldExclamationIcon
                      :class="[
                        'w-5 h-5',
                        result.has_pii ? 'text-yellow-400' : 'text-green-400'
                      ]"
                    />
                    <span
                      :class="[
                        'ml-2 font-medium',
                        result.has_pii ? 'text-yellow-400' : 'text-green-400'
                      ]"
                    >
                      {{ result.has_pii ? 'PII Detected' : 'No PII Detected' }}
                    </span>
                  </div>
                </div>

                <div v-if="result.pii_entities?.length" class="space-y-2">
                  <p class="text-sm font-medium text-dark-300">Detected Entities:</p>
                  <div class="flex flex-wrap gap-2">
                    <span
                      v-for="(entity, i) in result.pii_entities"
                      :key="i"
                      class="badge-warning"
                    >
                      {{ entity.type }}: {{ entity.value }}
                    </span>
                  </div>
                </div>

                <div v-if="result.anonymized_query" class="p-4 bg-dark-900 rounded-lg">
                  <p class="text-sm text-dark-400 mb-2">Anonymized Query:</p>
                  <pre class="text-sm text-dark-200 font-mono whitespace-pre-wrap">{{ result.anonymized_query }}</pre>
                  <button
                    @click="applySuggestion(result.anonymized_query)"
                    class="mt-3 btn-sm btn-secondary"
                  >
                    Use Anonymized Query
                  </button>
                </div>
              </div>
            </template>
          </div>

          <!-- Empty State -->
          <div v-else class="flex flex-col items-center justify-center h-full text-center">
            <DocumentMagnifyingGlassIcon class="w-12 h-12 text-dark-600 mb-3" />
            <p class="text-dark-400">Enter a SQL query and click "Run Analysis"</p>
            <p class="text-sm text-dark-500 mt-1">
              Use Ctrl+Enter as a shortcut
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
