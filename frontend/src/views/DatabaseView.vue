<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/composables/useApi'
import {
  PlusIcon,
  ServerIcon,
  TrashIcon,
  PencilIcon,
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  CircleStackIcon,
  TableCellsIcon,
  KeyIcon
} from '@heroicons/vue/24/outline'

const connections = ref([])
const supportedDatabases = ref({})
const loading = ref(true)
const showCreateModal = ref(false)
const showSchemaModal = ref(false)
const selectedConnection = ref(null)
const introspectedSchema = ref(null)
const testing = ref({})

const newConnection = ref({
  name: '',
  db_type: 'postgresql',
  host: 'localhost',
  port: null,
  database: '',
  username: '',
  password: '',
  ssl_enabled: false,
  workspace_id: null
})

const dbTypeOptions = computed(() => {
  return Object.entries(supportedDatabases.value).map(([type, info]) => ({
    value: type,
    label: type.charAt(0).toUpperCase() + type.slice(1),
    defaultPort: info.default_port
  }))
})

async function loadConnections() {
  loading.value = true
  try {
    const [connResponse, dbResponse] = await Promise.all([
      api.get('/databases'),
      api.get('/databases/supported')
    ])
    connections.value = connResponse.data
    supportedDatabases.value = dbResponse.data
  } catch (error) {
    console.error('Failed to load connections:', error)
  } finally {
    loading.value = false
  }
}

async function createConnection() {
  try {
    await api.post('/databases', newConnection.value)
    showCreateModal.value = false
    resetNewConnection()
    await loadConnections()
  } catch (error) {
    console.error('Failed to create connection:', error)
  }
}

async function deleteConnection(id) {
  if (!confirm('Are you sure you want to delete this connection?')) return
  try {
    await api.delete(`/databases/${id}`)
    await loadConnections()
  } catch (error) {
    console.error('Failed to delete connection:', error)
  }
}

async function testConnection(conn) {
  testing.value[conn.id] = true
  try {
    const response = await api.post(`/databases/${conn.id}/test`)
    conn.is_connected = response.data.success
    conn.test_result = response.data
  } catch (error) {
    conn.is_connected = false
    conn.test_result = { success: false, message: error.message }
  } finally {
    testing.value[conn.id] = false
  }
}

async function viewSchema(conn) {
  selectedConnection.value = conn
  introspectedSchema.value = null
  showSchemaModal.value = true

  try {
    const response = await api.get(`/databases/${conn.id}/schema`)
    introspectedSchema.value = response.data
  } catch (error) {
    console.error('Failed to introspect schema:', error)
  }
}

function resetNewConnection() {
  newConnection.value = {
    name: '',
    db_type: 'postgresql',
    host: 'localhost',
    port: null,
    database: '',
    username: '',
    password: '',
    ssl_enabled: false,
    workspace_id: null
  }
}

function onDbTypeChange() {
  const selected = dbTypeOptions.value.find(opt => opt.value === newConnection.value.db_type)
  if (selected) {
    newConnection.value.port = selected.defaultPort
  }
}

onMounted(() => {
  loadConnections()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-white">Database Connections</h2>
        <p class="text-sm text-dark-400">Manage database connections for schema introspection and validation</p>
      </div>
      <button @click="showCreateModal = true" class="btn-primary flex items-center">
        <PlusIcon class="w-4 h-4 mr-2" />
        Add Connection
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent"></div>
    </div>

    <!-- Connections Grid -->
    <div v-else-if="connections.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="conn in connections"
        :key="conn.id"
        class="card p-5"
      >
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center">
            <div :class="[
              'p-2 rounded-lg',
              conn.is_connected ? 'bg-green-500/10' : 'bg-dark-700'
            ]">
              <ServerIcon :class="[
                'w-5 h-5',
                conn.is_connected ? 'text-green-400' : 'text-dark-400'
              ]" />
            </div>
            <div class="ml-3">
              <h3 class="font-medium text-white">{{ conn.name }}</h3>
              <p class="text-sm text-dark-400">{{ conn.db_type.toUpperCase() }}</p>
            </div>
          </div>
          <div class="flex items-center space-x-1">
            <button
              @click="viewSchema(conn)"
              class="p-1.5 rounded text-dark-400 hover:text-primary-400 hover:bg-dark-700"
              title="View Schema"
            >
              <TableCellsIcon class="w-4 h-4" />
            </button>
            <button
              @click="deleteConnection(conn.id)"
              class="p-1.5 rounded text-dark-400 hover:text-red-400 hover:bg-dark-700"
              title="Delete"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-dark-400">Host</span>
            <span class="text-dark-200">{{ conn.host }}:{{ conn.port }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-dark-400">Database</span>
            <span class="text-dark-200">{{ conn.database }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-dark-400">Username</span>
            <span class="text-dark-200">{{ conn.username || 'N/A' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-dark-400">SSL</span>
            <span :class="conn.ssl_enabled ? 'text-green-400' : 'text-dark-400'">
              {{ conn.ssl_enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
        </div>

        <div class="mt-4 pt-4 border-t border-dark-700">
          <button
            @click="testConnection(conn)"
            :disabled="testing[conn.id]"
            class="w-full btn-secondary btn-sm flex items-center justify-center"
          >
            <ArrowPathIcon v-if="testing[conn.id]" class="w-4 h-4 mr-2 animate-spin" />
            <PlayIcon v-else class="w-4 h-4 mr-2" />
            {{ testing[conn.id] ? 'Testing...' : 'Test Connection' }}
          </button>

          <div v-if="conn.test_result" class="mt-3">
            <div :class="[
              'p-2 rounded text-sm flex items-center',
              conn.test_result.success ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
            ]">
              <CheckCircleIcon v-if="conn.test_result.success" class="w-4 h-4 mr-2" />
              <XCircleIcon v-else class="w-4 h-4 mr-2" />
              {{ conn.test_result.message }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card p-12 text-center">
      <CircleStackIcon class="w-12 h-12 text-dark-600 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-white mb-2">No Database Connections</h3>
      <p class="text-dark-400 mb-6">Add a database connection to enable schema introspection and query validation.</p>
      <button @click="showCreateModal = true" class="btn-primary">
        <PlusIcon class="w-4 h-4 mr-2 inline" />
        Add First Connection
      </button>
    </div>

    <!-- Create Modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showCreateModal = false"
      >
        <div class="card w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
          <h2 class="text-lg font-semibold text-white mb-4">Add Database Connection</h2>

          <div class="space-y-4">
            <div>
              <label class="label">Connection Name</label>
              <input v-model="newConnection.name" type="text" class="input" placeholder="My Database" />
            </div>

            <div>
              <label class="label">Database Type</label>
              <select v-model="newConnection.db_type" @change="onDbTypeChange" class="input">
                <option v-for="opt in dbTypeOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="label">Host</label>
                <input v-model="newConnection.host" type="text" class="input" placeholder="localhost" />
              </div>
              <div>
                <label class="label">Port</label>
                <input v-model.number="newConnection.port" type="number" class="input" placeholder="5432" />
              </div>
            </div>

            <div>
              <label class="label">Database Name</label>
              <input v-model="newConnection.database" type="text" class="input" placeholder="mydb" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="label">Username</label>
                <input v-model="newConnection.username" type="text" class="input" placeholder="postgres" />
              </div>
              <div>
                <label class="label">Password</label>
                <input v-model="newConnection.password" type="password" class="input" placeholder="••••••••" />
              </div>
            </div>

            <div class="flex items-center">
              <input
                id="ssl"
                type="checkbox"
                v-model="newConnection.ssl_enabled"
                class="w-4 h-4 text-primary-600 bg-dark-700 border-dark-600 rounded focus:ring-primary-500"
              />
              <label for="ssl" class="ml-2 text-sm text-dark-300">Enable SSL</label>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button @click="showCreateModal = false" class="btn-secondary">Cancel</button>
            <button @click="createConnection" :disabled="!newConnection.name || !newConnection.database" class="btn-primary">
              Create Connection
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Schema Modal -->
    <Teleport to="body">
      <div
        v-if="showSchemaModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showSchemaModal = false"
      >
        <div class="card w-full max-w-4xl mx-4 p-6 max-h-[90vh] overflow-hidden flex flex-col">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-white">
              Schema: {{ selectedConnection?.name }}
            </h2>
            <button @click="showSchemaModal = false" class="btn-secondary btn-sm">Close</button>
          </div>

          <div v-if="!introspectedSchema" class="flex items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent"></div>
          </div>

          <div v-else class="flex-1 overflow-y-auto space-y-4">
            <div class="grid grid-cols-3 gap-4 text-sm">
              <div class="p-3 bg-dark-900/50 rounded-lg">
                <p class="text-dark-400">Database</p>
                <p class="text-white font-medium">{{ introspectedSchema.database }}</p>
              </div>
              <div class="p-3 bg-dark-900/50 rounded-lg">
                <p class="text-dark-400">Type</p>
                <p class="text-white font-medium">{{ introspectedSchema.db_type.toUpperCase() }}</p>
              </div>
              <div class="p-3 bg-dark-900/50 rounded-lg">
                <p class="text-dark-400">Tables</p>
                <p class="text-white font-medium">{{ introspectedSchema.tables.length }}</p>
              </div>
            </div>

            <div class="space-y-3">
              <h3 class="text-sm font-medium text-dark-200">Tables</h3>
              <div
                v-for="table in introspectedSchema.tables"
                :key="table.name"
                class="p-4 bg-dark-900/50 rounded-lg"
              >
                <div class="flex items-center mb-3">
                  <TableCellsIcon class="w-4 h-4 text-primary-400 mr-2" />
                  <span class="font-medium text-white">{{ table.name }}</span>
                  <span class="text-xs text-dark-400 ml-2">({{ table.columns.length }} columns)</span>
                </div>

                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="text-left text-dark-400 border-b border-dark-700">
                        <th class="pb-2 pr-4">Column</th>
                        <th class="pb-2 pr-4">Type</th>
                        <th class="pb-2 pr-4">Nullable</th>
                        <th class="pb-2">Key</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="col in table.columns" :key="col.name" class="border-b border-dark-800">
                        <td class="py-2 pr-4 text-dark-200">{{ col.name }}</td>
                        <td class="py-2 pr-4 text-primary-400 font-mono text-xs">{{ col.type }}</td>
                        <td class="py-2 pr-4">
                          <span :class="col.nullable ? 'text-dark-400' : 'text-yellow-400'">
                            {{ col.nullable ? 'Yes' : 'No' }}
                          </span>
                        </td>
                        <td class="py-2">
                          <KeyIcon v-if="col.primary_key" class="w-4 h-4 text-yellow-400" title="Primary Key" />
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div v-if="table.foreign_keys?.length" class="mt-3 pt-3 border-t border-dark-700">
                  <p class="text-xs text-dark-400 mb-1">Foreign Keys:</p>
                  <div v-for="(fk, i) in table.foreign_keys" :key="i" class="text-xs text-dark-300">
                    {{ fk.columns.join(', ') }} → {{ fk.references.table }}({{ fk.references.columns.join(', ') }})
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
