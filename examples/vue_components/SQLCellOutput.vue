<template>
  <div class="sql-cell-output">
    <!-- Display Data Output -->
    <div v-if="output.output_type === 'display_data'" class="display-output">
      <!-- HTML Output -->
      <div
        v-if="output.data['text/html']"
        class="html-output p-4"
        v-html="output.data['text/html']"
      />

      <!-- JSON Output -->
      <div v-else-if="output.data['application/json']" class="json-output p-4">
        <SQLAnalysisResults :results="output.data['application/json']" />
      </div>

      <!-- Plain Text Fallback -->
      <div v-else-if="output.data['text/plain']" class="text-output p-4 bg-gray-50 font-mono text-sm">
        {{ output.data['text/plain'] }}
      </div>
    </div>

    <!-- Stream Output -->
    <div v-else-if="output.output_type === 'stream'" class="stream-output p-4 bg-gray-900 text-gray-100 font-mono text-sm">
      <pre class="whitespace-pre-wrap">{{ output.data.text }}</pre>
    </div>

    <!-- Error Output -->
    <div v-else-if="output.output_type === 'error'" class="error-output p-4 bg-red-50 border border-red-200 rounded">
      <div class="error-header flex items-center space-x-2 mb-2">
        <Icon name="exclamation-triangle" class="w-4 h-4 text-red-500" />
        <span class="font-semibold text-red-700">{{ output.data.ename }}</span>
      </div>
      <div class="error-message text-red-600 text-sm mb-2">
        {{ output.data.evalue }}
      </div>
      <details v-if="output.data.traceback && output.data.traceback.length > 1" class="mt-2">
        <summary class="text-red-500 text-xs cursor-pointer hover:text-red-700">
          Show traceback
        </summary>
        <pre class="mt-2 text-xs text-red-500 whitespace-pre-wrap">{{ output.data.traceback.join('\n') }}</pre>
      </details>
    </div>

    <!-- Metadata Display (if enabled) -->
    <div v-if="showMetadata && output.metadata && Object.keys(output.metadata).length > 0"
         class="metadata-display p-2 bg-gray-50 border-t border-gray-200">
      <details>
        <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
          Metadata
        </summary>
        <pre class="mt-2 text-xs text-gray-600">{{ JSON.stringify(output.metadata, null, 2) }}</pre>
      </details>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Icon } from '@skeletonlabs/skeleton'
import SQLAnalysisResults from './SQLAnalysisResults.vue'

const props = defineProps({
  output: {
    type: Object,
    required: true
  },
  showMetadata: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
/* Sanitize HTML output styles */
:deep(.html-output) {
  /* Override any potentially dangerous styles */
  max-width: 100%;
  overflow-x: auto;
}

:deep(.html-output script) {
  display: none !important;
}

:deep(.html-output iframe) {
  display: none !important;
}

/* Style l0l1 analysis output components */
:deep(.l0l1-analysis-output) {
  font-family: inherit;
}

:deep(.l0l1-analysis-output pre code) {
  font-family: 'JetBrains Mono', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
}

:deep(.l0l1-analysis-output .query-display) {
  background-color: rgb(248 250 252);
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

:deep(.l0l1-analysis-output .pii-results) {
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

:deep(.l0l1-analysis-output .validation-results) {
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

:deep(.l0l1-analysis-output .explanation-results) {
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

:deep(.l0l1-analysis-output .suggestions-results) {
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}

:deep(.l0l1-analysis-output .learning-stats) {
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 1rem;
}
</style>