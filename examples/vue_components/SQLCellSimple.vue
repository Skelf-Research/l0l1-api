<template>
  <div class="card">
    <!-- Cell Header -->
    <header class="card-header flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <iconify-icon icon="mdi:database" class="text-primary-500"></iconify-icon>
        <span class="font-bold">SQL Cell</span>
        <span v-if="executionCount" class="badge variant-soft">[{{ executionCount }}]</span>
      </div>

      <div class="flex items-center space-x-2">
        <!-- Options Toggle -->
        <button
          class="btn btn-sm variant-ghost-surface"
          @click="showOptions = !showOptions"
        >
          <iconify-icon icon="mdi:cog"></iconify-icon>
          <span>Options</span>
        </button>

        <!-- Execute Button -->
        <button
          class="btn btn-sm variant-filled-primary"
          @click="executeCell"
          :disabled="isExecuting || !source.trim()"
        >
          <iconify-icon v-if="isExecuting" icon="mdi:loading" class="animate-spin"></iconify-icon>
          <iconify-icon v-else icon="mdi:play"></iconify-icon>
          <span>Run</span>
        </button>
      </div>
    </header>

    <!-- Options Panel -->
    <div v-if="showOptions" class="p-4 bg-surface-100-800-token border-b border-surface-300-600-token">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <label class="flex items-center space-x-2">
          <input
            class="checkbox"
            type="checkbox"
            v-model="options.validate"
          />
          <span>Validate</span>
        </label>

        <label class="flex items-center space-x-2">
          <input
            class="checkbox"
            type="checkbox"
            v-model="options.explain"
          />
          <span>Explain</span>
        </label>

        <label class="flex items-center space-x-2">
          <input
            class="checkbox"
            type="checkbox"
            v-model="options.check_pii"
          />
          <span>Check PII</span>
        </label>

        <label class="flex items-center space-x-2">
          <input
            class="checkbox"
            type="checkbox"
            v-model="options.complete"
          />
          <span>Complete</span>
        </label>

        <label class="flex items-center space-x-2">
          <input
            class="checkbox"
            type="checkbox"
            v-model="options.anonymize"
          />
          <span>Anonymize</span>
        </label>
      </div>
    </div>

    <!-- SQL Editor (Using SkeletonUI textarea) -->
    <div class="p-4">
      <textarea
        class="textarea font-mono"
        rows="8"
        placeholder="Enter your SQL query here..."
        v-model="source"
        @keydown="onKeyDown"
        @input="onSourceChange"
      ></textarea>
    </div>

    <!-- Outputs -->
    <div v-if="outputs.length > 0" class="border-t border-surface-300-600-token">
      <SQLCellOutput
        v-for="(output, index) in outputs"
        :key="index"
        :output="output"
      />
    </div>

    <!-- Execution Status -->
    <footer v-if="executionTime" class="card-footer">
      <span class="text-xs opacity-50">Executed in {{ executionTime }}ms</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useNotebook } from '@/composables/useNotebook'
import SQLCellOutput from './SQLCellOutput.vue'

const props = defineProps({
  cellId: String,
  sessionId: String,
  initialSource: { type: String, default: '' },
  initialOptions: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['update:source', 'execute', 'duplicate', 'delete'])

const { executeCell: executeCellAPI } = useNotebook()

const source = ref(props.initialSource)
const outputs = ref([])
const executionCount = ref(null)
const executionTime = ref(null)
const isExecuting = ref(false)
const showOptions = ref(false)

const options = reactive({
  validate: true,
  explain: false,
  check_pii: true,
  complete: false,
  anonymize: false,
  ...props.initialOptions
})

watch(source, (newSource) => {
  emit('update:source', newSource)
})

const onSourceChange = () => {
  // Auto-resize textarea
  const textarea = event.target
  textarea.style.height = 'auto'
  textarea.style.height = textarea.scrollHeight + 'px'
}

const onKeyDown = (event) => {
  // Execute on Ctrl/Cmd + Enter
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    executeCell()
  }
}

const executeCell = async () => {
  if (isExecuting.value || !source.value.trim()) return

  isExecuting.value = true
  const startTime = Date.now()

  try {
    const result = await executeCellAPI(props.sessionId, props.cellId, {
      source: source.value,
      options: { ...options }
    })

    executionTime.value = Date.now() - startTime
    executionCount.value = result.execution_result.execution_count
    outputs.value = result.execution_result.outputs

    emit('execute', {
      cellId: props.cellId,
      result: result.execution_result
    })

  } catch (error) {
    console.error('Cell execution failed:', error)
    outputs.value = [{
      output_type: 'error',
      data: {
        ename: 'ExecutionError',
        evalue: error.message,
        traceback: [error.message]
      }
    }]
  } finally {
    isExecuting.value = false
  }
}
</script>

<style scoped>
/* Auto-resize textarea */
.textarea {
  resize: none;
  min-height: 120px;
}
</style>