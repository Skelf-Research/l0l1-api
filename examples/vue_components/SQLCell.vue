<template>
  <div class="sql-cell bg-white rounded-lg border border-gray-200 shadow-sm">
    <!-- Cell Header -->
    <div class="cell-header flex items-center justify-between p-4 border-b border-gray-100">
      <div class="cell-type flex items-center space-x-2">
        <Icon name="database" class="w-4 h-4 text-blue-500" />
        <span class="text-sm font-medium text-gray-700">SQL Cell</span>
        <span v-if="executionCount" class="text-xs text-gray-500">[{{ executionCount }}]</span>
      </div>

      <div class="cell-actions flex items-center space-x-2">
        <!-- Options Toggle -->
        <button
          @click="showOptions = !showOptions"
          class="text-xs text-gray-500 hover:text-gray-700 flex items-center space-x-1"
        >
          <Icon name="cog" class="w-3 h-3" />
          <span>Options</span>
        </button>

        <!-- Execute Button -->
        <button
          @click="executeCell"
          :disabled="isExecuting || !source.trim()"
          class="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Icon v-if="isExecuting" name="spinner" class="w-3 h-3 animate-spin" />
          <Icon v-else name="play" class="w-3 h-3" />
          Run
        </button>

        <!-- Cell Menu -->
        <Dropdown>
          <template #trigger>
            <button class="text-gray-400 hover:text-gray-600">
              <Icon name="dots-vertical" class="w-4 h-4" />
            </button>
          </template>
          <DropdownItem @click="duplicateCell">Duplicate</DropdownItem>
          <DropdownItem @click="deleteCell" class="text-red-600">Delete</DropdownItem>
        </Dropdown>
      </div>
    </div>

    <!-- Options Panel -->
    <transition name="slide-down">
      <div v-if="showOptions" class="options-panel p-4 bg-gray-50 border-b border-gray-100">
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
          <label class="flex items-center space-x-2 text-sm">
            <input
              v-model="options.validate"
              type="checkbox"
              class="rounded border-gray-300 text-blue-500 focus:ring-blue-500"
            >
            <span>Validate</span>
          </label>

          <label class="flex items-center space-x-2 text-sm">
            <input
              v-model="options.explain"
              type="checkbox"
              class="rounded border-gray-300 text-blue-500 focus:ring-blue-500"
            >
            <span>Explain</span>
          </label>

          <label class="flex items-center space-x-2 text-sm">
            <input
              v-model="options.check_pii"
              type="checkbox"
              class="rounded border-gray-300 text-blue-500 focus:ring-blue-500"
            >
            <span>Check PII</span>
          </label>

          <label class="flex items-center space-x-2 text-sm">
            <input
              v-model="options.complete"
              type="checkbox"
              class="rounded border-gray-300 text-blue-500 focus:ring-blue-500"
            >
            <span>Complete</span>
          </label>

          <label class="flex items-center space-x-2 text-sm">
            <input
              v-model="options.anonymize"
              type="checkbox"
              class="rounded border-gray-300 text-blue-500 focus:ring-blue-500"
            >
            <span>Anonymize</span>
          </label>
        </div>
      </div>
    </transition>

    <!-- Code Editor -->
    <div class="code-editor">
      <CodeMirror
        v-model="source"
        :options="editorOptions"
        class="min-h-[120px] border-0 focus:ring-0"
        @input="onSourceChange"
        @keydown="onKeyDown"
      />
    </div>

    <!-- Outputs -->
    <div v-if="outputs.length > 0" class="outputs border-t border-gray-100">
      <SQLCellOutput
        v-for="(output, index) in outputs"
        :key="index"
        :output="output"
        :show-metadata="showMetadata"
      />
    </div>

    <!-- Execution Status -->
    <div v-if="executionTime" class="execution-info p-2 bg-gray-50 text-xs text-gray-500 border-t border-gray-100">
      Executed in {{ executionTime }}ms
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useNotebook } from '@/composables/useNotebook'
import { Icon, Dropdown, DropdownItem } from '@skeletonlabs/skeleton'
import CodeMirror from '@/components/CodeMirror.vue'
import SQLCellOutput from './SQLCellOutput.vue'

const props = defineProps({
  cellId: {
    type: String,
    required: true
  },
  sessionId: {
    type: String,
    required: true
  },
  initialSource: {
    type: String,
    default: ''
  },
  initialOptions: {
    type: Object,
    default: () => ({})
  },
  workspaceId: {
    type: String,
    default: 'default'
  }
})

const emit = defineEmits(['update:source', 'execute', 'duplicate', 'delete'])

const { executeCell: executeCellAPI } = useNotebook()

const source = ref(props.initialSource)
const outputs = ref([])
const executionCount = ref(null)
const executionTime = ref(null)
const isExecuting = ref(false)
const showOptions = ref(false)
const showMetadata = ref(false)

const options = reactive({
  validate: true,
  explain: false,
  check_pii: true,
  complete: false,
  anonymize: false,
  ...props.initialOptions
})

const editorOptions = {
  mode: 'sql',
  theme: 'material',
  lineNumbers: true,
  autoCloseBrackets: true,
  matchBrackets: true,
  indentWithTabs: true,
  smartIndent: true,
  extraKeys: {
    'Shift-Enter': () => executeCell(),
    'Ctrl-Enter': () => executeCell(),
    'Cmd-Enter': () => executeCell()
  }
}

// Watch for source changes and emit to parent
watch(source, (newSource) => {
  emit('update:source', newSource)
})

const onSourceChange = (newSource) => {
  source.value = newSource
}

const onKeyDown = (event) => {
  // Handle keyboard shortcuts
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    executeCell()
  }
}

const executeCell = async () => {
  if (isExecuting.value || !source.value.trim()) return

  isExecuting.value = true

  try {
    const startTime = Date.now()

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

const duplicateCell = () => {
  emit('duplicate', {
    cellId: props.cellId,
    source: source.value,
    options: { ...options }
  })
}

const deleteCell = () => {
  if (confirm('Are you sure you want to delete this cell?')) {
    emit('delete', props.cellId)
  }
}
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

/* CodeMirror customization */
:deep(.CodeMirror) {
  font-family: 'JetBrains Mono', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.4;
}

:deep(.CodeMirror-focused .CodeMirror-cursor) {
  border-color: #3b82f6;
}

:deep(.CodeMirror-selected) {
  background-color: #e0f2fe;
}
</style>