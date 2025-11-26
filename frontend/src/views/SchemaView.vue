<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/composables/useApi'
import {
  PlusIcon,
  DocumentDuplicateIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowsRightLeftIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  TrashIcon,
  TableCellsIcon,
  ViewColumnsIcon,
  ExclamationTriangleIcon,
  CheckIcon
} from '@heroicons/vue/24/outline'

const versions = ref([])
const loading = ref(true)
const activeWorkspace = ref(localStorage.getItem('l0l1_workspace_id') || 'default')
const showCreateModal = ref(false)
const showCompareModal = ref(false)
const showImportModal = ref(false)
const selectedVersions = ref([])
const comparison = ref(null)
const migrations = ref([])

const newSchema = ref({
  workspace_id: activeWorkspace.value,
  description: '',
  schema_data: {
    tables: []
  },
  set_active: true
})

const newTable = ref({
  name: '',
  schema: 'public',
  columns: [],
  indexes: [],
  foreign_keys: []
})

const newColumn = ref({
  name: '',
  type: 'VARCHAR(255)',
  nullable: true,
  primary_key: false,
  unique: false
})

const importSql = ref('')
const validationResult = ref(null)

const columnTypes = [
  'INTEGER', 'BIGINT', 'SMALLINT',
  'VARCHAR(255)', 'VARCHAR(100)', 'TEXT',
  'BOOLEAN',
  'DECIMAL(10,2)', 'FLOAT', 'DOUBLE',
  'DATE', 'TIMESTAMP', 'TIME',
  'JSON', 'JSONB',
  'UUID'
]

async function loadVersions() {
  loading.value = true
  try {
    const response = await api.get('/schemas', {
      params: { workspace_id: activeWorkspace.value }
    })
    versions.value = response.data
  } catch (error) {
    console.error('Failed to load schema versions:', error)
    versions.value = []
  } finally {
    loading.value = false
  }
}

async function createVersion() {
  try {
    newSchema.value.workspace_id = activeWorkspace.value
    await api.post('/schemas', newSchema.value)
    showCreateModal.value = false
    resetNewSchema()
    await loadVersions()
  } catch (error) {
    console.error('Failed to create schema version:', error)
  }
}

async function activateVersion(versionId) {
  try {
    await api.post(`/schemas/${versionId}/activate`, null, {
      params: { workspace_id: activeWorkspace.value }
    })
    await loadVersions()
  } catch (error) {
    console.error('Failed to activate version:', error)
  }
}

async function compareVersions() {
  if (selectedVersions.value.length !== 2) return

  try {
    const response = await api.post('/schemas/compare', null, {
      params: {
        version_id_1: selectedVersions.value[0],
        version_id_2: selectedVersions.value[1]
      }
    })
    comparison.value = response.data
    showCompareModal.value = true

    // Also generate migrations
    const migrationsResponse = await api.post('/schemas/migrate', null, {
      params: {
        from_version_id: selectedVersions.value[0],
        to_version_id: selectedVersions.value[1]
      }
    })
    migrations.value = migrationsResponse.data
  } catch (error) {
    console.error('Failed to compare versions:', error)
  }
}

async function exportSchema(versionId, format) {
  try {
    const response = await api.get(`/schemas/${versionId}/export`, {
      params: { format }
    })
    const blob = new Blob([response.data], { type: format === 'json' ? 'application/json' : 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `schema_${versionId}.${format === 'json' ? 'json' : 'sql'}`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to export schema:', error)
  }
}

async function importFromSql() {
  try {
    const response = await api.post('/schemas/import', {
      sql: importSql.value,
      workspace_id: activeWorkspace.value
    })

    // Create a new schema version with the imported data
    newSchema.value.schema_data = response.data.schema_data
    newSchema.value.description = `Imported from SQL (${response.data.tables_parsed} tables)`
    await createVersion()

    showImportModal.value = false
    importSql.value = ''
  } catch (error) {
    console.error('Failed to import schema:', error)
  }
}

async function validateSchema() {
  try {
    const response = await api.post('/schemas/validate', newSchema.value.schema_data)
    validationResult.value = response.data
  } catch (error) {
    console.error('Failed to validate schema:', error)
  }
}

function addTable() {
  if (!newTable.value.name) return
  newSchema.value.schema_data.tables.push({ ...newTable.value, columns: [...newTable.value.columns] })
  newTable.value = { name: '', schema: 'public', columns: [], indexes: [], foreign_keys: [] }
}

function removeTable(index) {
  newSchema.value.schema_data.tables.splice(index, 1)
}

function addColumn() {
  if (!newColumn.value.name) return
  newTable.value.columns.push({ ...newColumn.value })
  newColumn.value = { name: '', type: 'VARCHAR(255)', nullable: true, primary_key: false, unique: false }
}

function removeColumn(index) {
  newTable.value.columns.splice(index, 1)
}

function resetNewSchema() {
  newSchema.value = {
    workspace_id: activeWorkspace.value,
    description: '',
    schema_data: { tables: [] },
    set_active: true
  }
  validationResult.value = null
}

function toggleVersionSelect(versionId) {
  const idx = selectedVersions.value.indexOf(versionId)
  if (idx === -1) {
    if (selectedVersions.value.length < 2) {
      selectedVersions.value.push(versionId)
    }
  } else {
    selectedVersions.value.splice(idx, 1)
  }
}

onMounted(() => {
  loadVersions()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-white">Schema Management</h2>
        <p class="text-sm text-dark-400">Version control and manage your database schemas</p>
      </div>
      <div class="flex items-center space-x-2">
        <button
          @click="compareVersions"
          :disabled="selectedVersions.length !== 2"
          class="btn-secondary flex items-center"
        >
          <ArrowsRightLeftIcon class="w-4 h-4 mr-2" />
          Compare ({{ selectedVersions.length }}/2)
        </button>
        <button @click="showImportModal = true" class="btn-secondary flex items-center">
          <ArrowUpTrayIcon class="w-4 h-4 mr-2" />
          Import SQL
        </button>
        <button @click="showCreateModal = true" class="btn-primary flex items-center">
          <PlusIcon class="w-4 h-4 mr-2" />
          New Version
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent"></div>
    </div>

    <!-- Versions List -->
    <div v-else-if="versions.length" class="space-y-3">
      <div
        v-for="version in versions"
        :key="version.id"
        :class="[
          'card p-5 cursor-pointer transition-all',
          selectedVersions.includes(version.id) ? 'border-primary-500 ring-1 ring-primary-500' : '',
          version.is_active ? 'border-green-500/50' : ''
        ]"
        @click="toggleVersionSelect(version.id)"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center">
            <div :class="[
              'p-2 rounded-lg',
              version.is_active ? 'bg-green-500/10' : 'bg-dark-700'
            ]">
              <DocumentDuplicateIcon :class="[
                'w-5 h-5',
                version.is_active ? 'text-green-400' : 'text-dark-400'
              ]" />
            </div>
            <div class="ml-3">
              <div class="flex items-center">
                <h3 class="font-medium text-white">Version {{ version.version }}</h3>
                <span v-if="version.is_active" class="ml-2 badge-success">Active</span>
              </div>
              <p class="text-sm text-dark-400">{{ version.description || 'No description' }}</p>
            </div>
          </div>

          <div class="flex items-center space-x-2">
            <button
              v-if="!version.is_active"
              @click.stop="activateVersion(version.id)"
              class="btn-secondary btn-sm"
            >
              <CheckIcon class="w-4 h-4 mr-1" />
              Activate
            </button>
            <button
              @click.stop="exportSchema(version.id, 'json')"
              class="p-1.5 rounded text-dark-400 hover:text-primary-400 hover:bg-dark-700"
              title="Export JSON"
            >
              <ArrowDownTrayIcon class="w-4 h-4" />
            </button>
            <button
              @click.stop="exportSchema(version.id, 'sql')"
              class="p-1.5 rounded text-dark-400 hover:text-primary-400 hover:bg-dark-700"
              title="Export SQL"
            >
              <ViewColumnsIcon class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div class="mt-4 grid grid-cols-4 gap-4 text-sm">
          <div>
            <span class="text-dark-400">Tables:</span>
            <span class="ml-2 text-dark-200">{{ version.schema_data?.tables?.length || 0 }}</span>
          </div>
          <div>
            <span class="text-dark-400">Checksum:</span>
            <span class="ml-2 text-dark-200 font-mono text-xs">{{ version.checksum }}</span>
          </div>
          <div>
            <span class="text-dark-400">Created:</span>
            <span class="ml-2 text-dark-200">
              {{ version.created_at ? new Date(version.created_at).toLocaleDateString() : 'N/A' }}
            </span>
          </div>
          <div>
            <span class="text-dark-400">Parent:</span>
            <span class="ml-2 text-dark-200">{{ version.parent_version || 'None' }}</span>
          </div>
        </div>

        <!-- Tables Preview -->
        <div v-if="version.schema_data?.tables?.length" class="mt-4 pt-4 border-t border-dark-700">
          <div class="flex flex-wrap gap-2">
            <span
              v-for="table in version.schema_data.tables.slice(0, 5)"
              :key="table.name"
              class="px-2 py-1 bg-dark-700 rounded text-xs text-dark-300"
            >
              <TableCellsIcon class="w-3 h-3 inline mr-1" />
              {{ table.name }}
            </span>
            <span v-if="version.schema_data.tables.length > 5" class="px-2 py-1 text-xs text-dark-400">
              +{{ version.schema_data.tables.length - 5 }} more
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card p-12 text-center">
      <DocumentDuplicateIcon class="w-12 h-12 text-dark-600 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-white mb-2">No Schema Versions</h3>
      <p class="text-dark-400 mb-6">Create your first schema version to start tracking changes.</p>
      <button @click="showCreateModal = true" class="btn-primary">
        <PlusIcon class="w-4 h-4 mr-2 inline" />
        Create First Version
      </button>
    </div>

    <!-- Create Modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showCreateModal = false"
      >
        <div class="card w-full max-w-4xl mx-4 p-6 max-h-[90vh] overflow-y-auto">
          <h2 class="text-lg font-semibold text-white mb-4">Create Schema Version</h2>

          <div class="space-y-6">
            <!-- Description -->
            <div>
              <label class="label">Description</label>
              <input
                v-model="newSchema.description"
                type="text"
                class="input"
                placeholder="What changed in this version?"
              />
            </div>

            <!-- Add Table Form -->
            <div class="p-4 bg-dark-900/50 rounded-lg">
              <h3 class="text-sm font-medium text-dark-200 mb-3">Add Table</h3>

              <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label class="label">Table Name</label>
                  <input v-model="newTable.name" type="text" class="input" placeholder="users" />
                </div>
                <div>
                  <label class="label">Schema</label>
                  <input v-model="newTable.schema" type="text" class="input" placeholder="public" />
                </div>
              </div>

              <!-- Add Column Form -->
              <div class="p-3 bg-dark-800 rounded-lg mb-3">
                <h4 class="text-xs font-medium text-dark-300 mb-2">Add Column</h4>
                <div class="grid grid-cols-6 gap-2">
                  <input v-model="newColumn.name" type="text" class="input text-sm" placeholder="column_name" />
                  <select v-model="newColumn.type" class="input text-sm">
                    <option v-for="t in columnTypes" :key="t" :value="t">{{ t }}</option>
                  </select>
                  <label class="flex items-center">
                    <input type="checkbox" v-model="newColumn.nullable" class="mr-1" />
                    <span class="text-xs text-dark-400">Nullable</span>
                  </label>
                  <label class="flex items-center">
                    <input type="checkbox" v-model="newColumn.primary_key" class="mr-1" />
                    <span class="text-xs text-dark-400">PK</span>
                  </label>
                  <label class="flex items-center">
                    <input type="checkbox" v-model="newColumn.unique" class="mr-1" />
                    <span class="text-xs text-dark-400">Unique</span>
                  </label>
                  <button @click="addColumn" class="btn-secondary btn-sm">Add</button>
                </div>
              </div>

              <!-- Columns List -->
              <div v-if="newTable.columns.length" class="mb-3">
                <div
                  v-for="(col, i) in newTable.columns"
                  :key="i"
                  class="flex items-center justify-between py-1 px-2 bg-dark-800 rounded mb-1 text-sm"
                >
                  <span class="text-dark-200">{{ col.name }}</span>
                  <span class="text-primary-400 font-mono text-xs">{{ col.type }}</span>
                  <div class="flex items-center space-x-2 text-xs text-dark-400">
                    <span v-if="col.primary_key">PK</span>
                    <span v-if="col.unique">UQ</span>
                    <span v-if="!col.nullable">NOT NULL</span>
                  </div>
                  <button @click="removeColumn(i)" class="text-red-400 hover:text-red-300">
                    <TrashIcon class="w-4 h-4" />
                  </button>
                </div>
              </div>

              <button
                @click="addTable"
                :disabled="!newTable.name || !newTable.columns.length"
                class="btn-primary btn-sm"
              >
                Add Table
              </button>
            </div>

            <!-- Tables List -->
            <div v-if="newSchema.schema_data.tables.length">
              <h3 class="text-sm font-medium text-dark-200 mb-3">Tables in Schema</h3>
              <div class="space-y-2">
                <div
                  v-for="(table, i) in newSchema.schema_data.tables"
                  :key="i"
                  class="p-3 bg-dark-900/50 rounded-lg flex items-center justify-between"
                >
                  <div>
                    <span class="text-white font-medium">{{ table.name }}</span>
                    <span class="text-dark-400 text-sm ml-2">({{ table.columns.length }} columns)</span>
                  </div>
                  <button @click="removeTable(i)" class="text-red-400 hover:text-red-300">
                    <TrashIcon class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Validation -->
            <div>
              <button @click="validateSchema" class="btn-secondary btn-sm mb-2">Validate Schema</button>
              <div v-if="validationResult" :class="[
                'p-3 rounded-lg',
                validationResult.is_valid ? 'bg-green-900/30 border border-green-800' : 'bg-red-900/30 border border-red-800'
              ]">
                <div class="flex items-center mb-2">
                  <CheckCircleIcon v-if="validationResult.is_valid" class="w-5 h-5 text-green-400 mr-2" />
                  <ExclamationTriangleIcon v-else class="w-5 h-5 text-red-400 mr-2" />
                  <span :class="validationResult.is_valid ? 'text-green-400' : 'text-red-400'">
                    {{ validationResult.is_valid ? 'Valid Schema' : 'Invalid Schema' }}
                  </span>
                </div>
                <div v-if="validationResult.errors.length" class="text-sm text-red-400 mb-2">
                  <p v-for="err in validationResult.errors" :key="err">{{ err }}</p>
                </div>
                <div v-if="validationResult.warnings.length" class="text-sm text-yellow-400">
                  <p v-for="warn in validationResult.warnings" :key="warn">{{ warn }}</p>
                </div>
              </div>
            </div>

            <div class="flex items-center">
              <input
                id="setActive"
                type="checkbox"
                v-model="newSchema.set_active"
                class="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-500"
              />
              <label for="setActive" class="ml-2 text-sm text-dark-300">Set as active version</label>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button @click="showCreateModal = false" class="btn-secondary">Cancel</button>
            <button
              @click="createVersion"
              :disabled="!newSchema.schema_data.tables.length"
              class="btn-primary"
            >
              Create Version
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Compare Modal -->
    <Teleport to="body">
      <div
        v-if="showCompareModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showCompareModal = false"
      >
        <div class="card w-full max-w-4xl mx-4 p-6 max-h-[90vh] overflow-y-auto">
          <h2 class="text-lg font-semibold text-white mb-4">Schema Comparison</h2>

          <div v-if="comparison" class="space-y-4">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div class="p-3 bg-dark-900/50 rounded-lg">
                <p class="text-dark-400">From Version</p>
                <p class="text-white font-medium">{{ comparison.version_1.version }}</p>
              </div>
              <div class="p-3 bg-dark-900/50 rounded-lg">
                <p class="text-dark-400">To Version</p>
                <p class="text-white font-medium">{{ comparison.version_2.version }}</p>
              </div>
            </div>

            <div v-if="comparison.tables_added.length" class="p-4 bg-green-900/20 border border-green-800 rounded-lg">
              <h4 class="text-green-400 font-medium mb-2">Tables Added</h4>
              <div v-for="t in comparison.tables_added" :key="t.name" class="text-sm text-dark-200">
                + {{ t.name }}
              </div>
            </div>

            <div v-if="comparison.tables_removed.length" class="p-4 bg-red-900/20 border border-red-800 rounded-lg">
              <h4 class="text-red-400 font-medium mb-2">Tables Removed</h4>
              <div v-for="t in comparison.tables_removed" :key="t.name" class="text-sm text-dark-200">
                - {{ t.name }}
              </div>
            </div>

            <div v-if="comparison.columns_added.length" class="p-4 bg-green-900/20 border border-green-800 rounded-lg">
              <h4 class="text-green-400 font-medium mb-2">Columns Added</h4>
              <div v-for="c in comparison.columns_added" :key="`${c.table}.${c.column.name}`" class="text-sm text-dark-200">
                + {{ c.table }}.{{ c.column.name }} ({{ c.column.type }})
              </div>
            </div>

            <div v-if="comparison.columns_removed.length" class="p-4 bg-red-900/20 border border-red-800 rounded-lg">
              <h4 class="text-red-400 font-medium mb-2">Columns Removed</h4>
              <div v-for="c in comparison.columns_removed" :key="`${c.table}.${c.column.name}`" class="text-sm text-dark-200">
                - {{ c.table }}.{{ c.column.name }}
              </div>
            </div>

            <!-- Migration SQL -->
            <div v-if="migrations.length" class="p-4 bg-dark-900/50 rounded-lg">
              <h4 class="text-dark-200 font-medium mb-2">Migration SQL</h4>
              <div class="space-y-2">
                <div v-for="m in migrations" :key="m.id" class="p-2 bg-dark-800 rounded">
                  <p class="text-xs text-dark-400 mb-1">{{ m.change_type }}: {{ m.target }}</p>
                  <pre class="text-sm text-primary-400 font-mono whitespace-pre-wrap">{{ m.sql_up }}</pre>
                </div>
              </div>
            </div>
          </div>

          <div class="flex justify-end mt-6">
            <button @click="showCompareModal = false; selectedVersions = []" class="btn-secondary">Close</button>
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
          <h2 class="text-lg font-semibold text-white mb-4">Import from SQL</h2>

          <div>
            <label class="label">Paste CREATE TABLE statements</label>
            <textarea
              v-model="importSql"
              class="sql-editor h-64"
              placeholder="CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(100)
);"
            ></textarea>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button @click="showImportModal = false" class="btn-secondary">Cancel</button>
            <button @click="importFromSql" :disabled="!importSql.trim()" class="btn-primary">
              Import & Create Version
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
