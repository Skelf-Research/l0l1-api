<template>
  <div class="notebook-interface h-full flex flex-col">
    <!-- Notebook Toolbar -->
    <div class="toolbar flex items-center justify-between p-4 border-b border-gray-200 bg-white">
      <div class="toolbar-left flex items-center space-x-4">
        <h2 class="text-lg font-semibold text-gray-800">{{ notebookTitle }}</h2>

        <div class="workspace-info text-sm text-gray-500">
          Workspace: <span class="font-medium">{{ workspaceId }}</span>
        </div>
      </div>

      <div class="toolbar-right flex items-center space-x-2">
        <!-- Add Cell Dropdown -->
        <Dropdown placement="bottom-end">
          <template #trigger>
            <button class="px-3 py-1.5 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 flex items-center space-x-1">
              <Icon name="plus" class="w-4 h-4" />
              <span>Add Cell</span>
            </button>
          </template>
          <DropdownItem @click="addCell('sql')">
            <Icon name="database" class="w-4 h-4 mr-2" />
            SQL Cell
          </DropdownItem>
          <DropdownItem @click="addCell('markdown')">
            <Icon name="document-text" class="w-4 h-4 mr-2" />
            Markdown Cell
          </DropdownItem>
        </Dropdown>

        <!-- Run All Button -->
        <button
          @click="runAllCells"
          :disabled="isRunningAll || cells.length === 0"
          class="px-3 py-1.5 bg-green-500 text-white text-sm rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1"
        >
          <Icon v-if="isRunningAll" name="spinner" class="w-4 h-4 animate-spin" />
          <Icon v-else name="play-circle" class="w-4 h-4" />
          <span>Run All</span>
        </button>

        <!-- Clear Outputs -->
        <button
          @click="clearAllOutputs"
          class="px-3 py-1.5 bg-gray-500 text-white text-sm rounded hover:bg-gray-600"
        >
          <Icon name="trash" class="w-4 h-4" />
        </button>

        <!-- Notebook Menu -->
        <Dropdown placement="bottom-end">
          <template #trigger>
            <button class="p-1.5 text-gray-400 hover:text-gray-600 rounded">
              <Icon name="dots-vertical" class="w-5 h-5" />
            </button>
          </template>
          <DropdownItem @click="saveNotebook">
            <Icon name="save" class="w-4 h-4 mr-2" />
            Save Notebook
          </DropdownItem>
          <DropdownItem @click="exportNotebook">
            <Icon name="download" class="w-4 h-4 mr-2" />
            Export
          </DropdownItem>
          <DropdownItem @click="showSchemaDialog = true">
            <Icon name="database" class="w-4 h-4 mr-2" />
            Set Schema Context
          </DropdownItem>
          <div class="dropdown-divider"></div>
          <DropdownItem @click="showStats = true">
            <Icon name="chart-bar" class="w-4 h-4 mr-2" />
            Show Statistics
          </DropdownItem>
        </Dropdown>
      </div>
    </div>

    <!-- Cells Container -->
    <div class="cells-container flex-1 overflow-y-auto p-4 space-y-4">
      <template v-if="cells.length === 0">
        <div class="empty-state text-center py-12">
          <Icon name="document-plus" class="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 class="text-lg font-medium text-gray-600 mb-2">No cells yet</h3>
          <p class="text-gray-500 mb-4">Add your first cell to start analyzing SQL queries</p>
          <button
            @click="addCell('sql')"
            class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Add SQL Cell
          </button>
        </div>
      </template>

      <template v-else>
        <draggable
          v-model="cells"
          item-key="id"
          handle=".cell-drag-handle"
          @update="onCellsReordered"
          class="space-y-4"
        >
          <template #item="{ element: cell, index }">
            <div class="cell-wrapper relative group">
              <!-- Drag Handle -->
              <div class="cell-drag-handle absolute -left-6 top-4 opacity-0 group-hover:opacity-100 transition-opacity cursor-move">
                <Icon name="dots-vertical" class="w-4 h-4 text-gray-400" />
              </div>

              <!-- SQL Cell -->
              <SQLCell
                v-if="cell.cell_type === 'sql'"
                :key="cell.id"
                :cell-id="cell.id"
                :session-id="sessionId"
                :initial-source="cell.source"
                :initial-options="cell.metadata?.l0l1?.options || {}"
                :workspace-id="workspaceId"
                @update:source="(source) => updateCellSource(cell.id, source)"
                @execute="onCellExecuted"
                @duplicate="(data) => duplicateCell(index, data)"
                @delete="deleteCell"
              />

              <!-- Markdown Cell -->
              <MarkdownCell
                v-else-if="cell.cell_type === 'markdown'"
                :key="cell.id"
                :cell-id="cell.id"
                :initial-source="cell.source"
                @update:source="(source) => updateCellSource(cell.id, source)"
                @duplicate="(data) => duplicateCell(index, data)"
                @delete="deleteCell"
              />

              <!-- Add Cell Between -->
              <div class="add-cell-between opacity-0 group-hover:opacity-100 transition-opacity mt-2 text-center">
                <button
                  @click="insertCellAfter(index, 'sql')"
                  class="inline-flex items-center space-x-1 px-2 py-1 text-xs text-gray-500 hover:text-blue-500 hover:bg-blue-50 rounded"
                >
                  <Icon name="plus" class="w-3 h-3" />
                  <span>Add Cell</span>
                </button>
              </div>
            </div>
          </template>
        </draggable>
      </template>
    </div>

    <!-- Status Bar -->
    <div class="status-bar flex items-center justify-between p-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
      <div class="status-left flex items-center space-x-4">
        <span>{{ cells.length }} cells</span>
        <span v-if="executedCells > 0">{{ executedCells }} executed</span>
        <span v-if="sessionStats?.learning_stats?.total_queries">
          {{ sessionStats.learning_stats.total_queries }} learned queries
        </span>
      </div>
      <div class="status-right">
        <span>Session: {{ sessionId.slice(-8) }}</span>
      </div>
    </div>

    <!-- Schema Context Dialog -->
    <Modal v-model="showSchemaDialog" title="Set Schema Context">
      <div class="p-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Database Schema (SQL DDL)
        </label>
        <textarea
          v-model="schemaContext"
          rows="10"
          class="w-full border border-gray-300 rounded-md shadow-sm p-3 font-mono text-sm"
          placeholder="CREATE TABLE users (&#10;  id SERIAL PRIMARY KEY,&#10;  name VARCHAR(100) NOT NULL,&#10;  email VARCHAR(255) UNIQUE NOT NULL&#10;);"
        ></textarea>
        <div class="flex justify-end space-x-2 mt-4">
          <button
            @click="showSchemaDialog = false"
            class="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            @click="updateSchemaContext"
            class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Update Schema
          </button>
        </div>
      </div>
    </Modal>

    <!-- Statistics Modal -->
    <Modal v-model="showStats" title="Notebook Statistics">
      <div class="p-6" v-if="sessionStats">
        <div class="grid grid-cols-2 gap-6">
          <div>
            <h4 class="font-semibold text-gray-800 mb-3">Session Info</h4>
            <dl class="space-y-2 text-sm">
              <div>
                <dt class="text-gray-600">Total Cells:</dt>
                <dd class="font-medium">{{ sessionStats.total_cells }}</dd>
              </div>
              <div>
                <dt class="text-gray-600">SQL Cells:</dt>
                <dd class="font-medium">{{ sessionStats.sql_cells }}</dd>
              </div>
              <div>
                <dt class="text-gray-600">Executed:</dt>
                <dd class="font-medium">{{ sessionStats.executed_cells }}</dd>
              </div>
              <div>
                <dt class="text-gray-600">Created:</dt>
                <dd class="font-medium">{{ new Date(sessionStats.created_at).toLocaleString() }}</dd>
              </div>
            </dl>
          </div>
          <div v-if="sessionStats.learning_stats">
            <h4 class="font-semibold text-gray-800 mb-3">Learning Stats</h4>
            <dl class="space-y-2 text-sm">
              <div>
                <dt class="text-gray-600">Learned Queries:</dt>
                <dd class="font-medium">{{ sessionStats.learning_stats.total_queries }}</dd>
              </div>
              <div>
                <dt class="text-gray-600">Avg Execution:</dt>
                <dd class="font-medium">{{ sessionStats.learning_stats.avg_execution_time?.toFixed(3) }}s</dd>
              </div>
              <div>
                <dt class="text-gray-600">Recent Activity:</dt>
                <dd class="font-medium">{{ sessionStats.learning_stats.recent_activity }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useNotebook } from '@/composables/useNotebook'
import { Icon, Dropdown, DropdownItem, Modal } from '@skeletonlabs/skeleton'
import draggable from 'vuedraggable'
import SQLCell from './SQLCell.vue'
import MarkdownCell from './MarkdownCell.vue'

const props = defineProps({
  workspaceId: {
    type: String,
    required: true
  },
  tenantId: {
    type: String,
    default: 'default'
  },
  notebookTitle: {
    type: String,
    default: 'Untitled Notebook'
  }
})

const emit = defineEmits(['session-created', 'notebook-saved'])

const {
  createSession,
  getSession,
  createCell,
  updateCell,
  deleteCell: deleteCellAPI,
  moveCell,
  clearAllOutputs: clearOutputsAPI,
  exportNotebook: exportNotebookAPI
} = useNotebook()

const sessionId = ref('')
const cells = ref([])
const sessionStats = ref(null)
const schemaContext = ref('')
const isRunningAll = ref(false)
const showSchemaDialog = ref(false)
const showStats = ref(false)

const executedCells = computed(() => {
  return cells.value.filter(cell => cell.execution_count !== null).length
})

onMounted(async () => {
  await initializeSession()
})

const initializeSession = async () => {
  try {
    const session = await createSession({
      workspace_id: props.workspaceId,
      tenant_id: props.tenantId
    })
    sessionId.value = session.session_id
    emit('session-created', session.session_id)

    // Load session data
    await loadSession()
  } catch (error) {
    console.error('Failed to initialize session:', error)
  }
}

const loadSession = async () => {
  try {
    const sessionData = await getSession(sessionId.value)
    cells.value = sessionData.session.cells || []
    sessionStats.value = sessionData.stats
    schemaContext.value = sessionData.session.metadata?.l0l1?.schema_context || ''
  } catch (error) {
    console.error('Failed to load session:', error)
  }
}

const addCell = async (cellType = 'sql') => {
  try {
    const result = await createCell(sessionId.value, {
      cell_type: cellType,
      source: cellType === 'markdown' ? '# New Section\n\nAdd your content here...' : ''
    })

    await loadSession() // Refresh to get the new cell
  } catch (error) {
    console.error('Failed to add cell:', error)
  }
}

const insertCellAfter = async (index, cellType = 'sql') => {
  await addCell(cellType)
  // Move the new cell to the correct position
  const newCellIndex = cells.value.length - 1
  if (newCellIndex > index + 1) {
    const cellId = cells.value[newCellIndex].id
    await moveCell(sessionId.value, cellId, { new_index: index + 1 })
    await loadSession()
  }
}

const duplicateCell = async (index, cellData) => {
  try {
    await createCell(sessionId.value, {
      cell_type: 'sql',
      source: cellData.source
    })

    // Move the duplicated cell after the original
    const newCellIndex = cells.value.length - 1
    if (newCellIndex > index + 1) {
      const cellId = cells.value[newCellIndex].id
      await moveCell(sessionId.value, cellId, { new_index: index + 1 })
    }

    await loadSession()
  } catch (error) {
    console.error('Failed to duplicate cell:', error)
  }
}

const deleteCell = async (cellId) => {
  try {
    await deleteCellAPI(sessionId.value, cellId)
    await loadSession()
  } catch (error) {
    console.error('Failed to delete cell:', error)
  }
}

const updateCellSource = async (cellId, source) => {
  try {
    await updateCell(sessionId.value, cellId, { source })
  } catch (error) {
    console.error('Failed to update cell:', error)
  }
}

const onCellExecuted = (data) => {
  // Update local cell data
  const cell = cells.value.find(c => c.id === data.cellId)
  if (cell) {
    cell.execution_count = data.result.execution_count
    cell.outputs = data.result.outputs
  }
}

const onCellsReordered = async (event) => {
  if (event.moved) {
    const cellId = event.moved.element.id
    const newIndex = event.moved.newIndex

    try {
      await moveCell(sessionId.value, cellId, { new_index: newIndex })
    } catch (error) {
      console.error('Failed to reorder cells:', error)
      // Revert the change
      await loadSession()
    }
  }
}

const runAllCells = async () => {
  isRunningAll.value = true

  try {
    for (const cell of cells.value) {
      if (cell.cell_type === 'sql' && cell.source.trim()) {
        // Trigger cell execution - this would need to be coordinated with child components
        // For now, we'll skip the implementation detail
      }
    }
  } catch (error) {
    console.error('Failed to run all cells:', error)
  } finally {
    isRunningAll.value = false
  }
}

const clearAllOutputs = async () => {
  try {
    await clearOutputsAPI(sessionId.value)
    await loadSession()
  } catch (error) {
    console.error('Failed to clear outputs:', error)
  }
}

const updateSchemaContext = async () => {
  try {
    await updateSession(sessionId.value, {
      schema_context: schemaContext.value
    })
    showSchemaDialog.value = false
    await loadSession()
  } catch (error) {
    console.error('Failed to update schema context:', error)
  }
}

const saveNotebook = async () => {
  // In a real implementation, this would save to persistent storage
  emit('notebook-saved', {
    sessionId: sessionId.value,
    cells: cells.value
  })
}

const exportNotebook = async () => {
  try {
    const notebook = await exportNotebookAPI(sessionId.value)

    // Create download link
    const blob = new Blob([JSON.stringify(notebook, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${props.notebookTitle.replace(/\s+/g, '_')}.l0l1nb.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to export notebook:', error)
  }
}
</script>

<style scoped>
.cell-wrapper:hover .add-cell-between {
  opacity: 1;
}

.dropdown-divider {
  height: 1px;
  background-color: #e5e7eb;
  margin: 0.25rem 0;
}
</style>