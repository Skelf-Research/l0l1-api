<script setup>
import { ref, onMounted } from 'vue'
import { workspaceApi } from '@/composables/useApi'
import {
  PlusIcon,
  FolderIcon,
  TrashIcon,
  PencilIcon,
  EllipsisVerticalIcon,
  MagnifyingGlassIcon,
  CheckIcon
} from '@heroicons/vue/24/outline'

const workspaces = ref([])
const loading = ref(true)
const searchQuery = ref('')
const showCreateModal = ref(false)
const editingWorkspace = ref(null)
const activeWorkspaceId = ref(localStorage.getItem('l0l1_workspace_id'))

const newWorkspace = ref({
  name: '',
  description: '',
  schema: ''
})

async function loadWorkspaces() {
  loading.value = true
  try {
    const response = await workspaceApi.list()
    workspaces.value = response.data.workspaces || response.data || []
  } catch (error) {
    console.error('Failed to load workspaces:', error)
    workspaces.value = []
  } finally {
    loading.value = false
  }
}

async function createWorkspace() {
  try {
    await workspaceApi.create(newWorkspace.value)
    showCreateModal.value = false
    newWorkspace.value = { name: '', description: '', schema: '' }
    await loadWorkspaces()
  } catch (error) {
    console.error('Failed to create workspace:', error)
  }
}

async function deleteWorkspace(id) {
  if (!confirm('Are you sure you want to delete this workspace?')) return

  try {
    await workspaceApi.delete(id)
    if (activeWorkspaceId.value === id) {
      setActiveWorkspace(null)
    }
    await loadWorkspaces()
  } catch (error) {
    console.error('Failed to delete workspace:', error)
  }
}

function setActiveWorkspace(id) {
  activeWorkspaceId.value = id
  if (id) {
    localStorage.setItem('l0l1_workspace_id', id)
  } else {
    localStorage.removeItem('l0l1_workspace_id')
  }
}

function editWorkspace(workspace) {
  editingWorkspace.value = { ...workspace }
}

async function saveWorkspace() {
  try {
    await workspaceApi.update(editingWorkspace.value.id, editingWorkspace.value)
    editingWorkspace.value = null
    await loadWorkspaces()
  } catch (error) {
    console.error('Failed to update workspace:', error)
  }
}

const filteredWorkspaces = computed(() => {
  if (!searchQuery.value) return workspaces.value
  const query = searchQuery.value.toLowerCase()
  return workspaces.value.filter(w =>
    w.name.toLowerCase().includes(query) ||
    w.description?.toLowerCase().includes(query)
  )
})

import { computed } from 'vue'

onMounted(() => {
  loadWorkspaces()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <div class="relative">
          <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search workspaces..."
            class="input pl-9 w-64"
          />
        </div>
      </div>
      <button @click="showCreateModal = true" class="btn-primary flex items-center">
        <PlusIcon class="w-4 h-4 mr-2" />
        New Workspace
      </button>
    </div>

    <!-- Active Workspace Banner -->
    <div
      v-if="activeWorkspaceId"
      class="p-4 bg-primary-900/30 border border-primary-800 rounded-lg flex items-center justify-between"
    >
      <div class="flex items-center">
        <CheckIcon class="w-5 h-5 text-primary-400 mr-2" />
        <span class="text-primary-300">
          Active Workspace:
          <strong>{{ workspaces.find(w => w.id === activeWorkspaceId)?.name || activeWorkspaceId }}</strong>
        </span>
      </div>
      <button
        @click="setActiveWorkspace(null)"
        class="text-sm text-primary-400 hover:text-primary-300"
      >
        Clear
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent"></div>
    </div>

    <!-- Workspaces Grid -->
    <div v-else-if="filteredWorkspaces.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="workspace in filteredWorkspaces"
        :key="workspace.id"
        :class="[
          'card p-5 cursor-pointer transition-all hover:border-primary-600',
          activeWorkspaceId === workspace.id ? 'border-primary-500 ring-1 ring-primary-500' : ''
        ]"
        @click="setActiveWorkspace(workspace.id)"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center">
            <div class="p-2 bg-primary-500/10 rounded-lg">
              <FolderIcon class="w-5 h-5 text-primary-400" />
            </div>
            <div class="ml-3">
              <h3 class="font-medium text-white">{{ workspace.name }}</h3>
              <p class="text-sm text-dark-400">
                {{ workspace.description || 'No description' }}
              </p>
            </div>
          </div>

          <div class="flex items-center space-x-1">
            <button
              @click.stop="editWorkspace(workspace)"
              class="p-1.5 rounded text-dark-400 hover:text-dark-100 hover:bg-dark-700"
            >
              <PencilIcon class="w-4 h-4" />
            </button>
            <button
              @click.stop="deleteWorkspace(workspace.id)"
              class="p-1.5 rounded text-dark-400 hover:text-red-400 hover:bg-dark-700"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div class="mt-4 pt-4 border-t border-dark-700">
          <div class="flex items-center justify-between text-sm">
            <span class="text-dark-400">Created</span>
            <span class="text-dark-300">
              {{ workspace.created_at ? new Date(workspace.created_at).toLocaleDateString() : 'N/A' }}
            </span>
          </div>
        </div>

        <div v-if="activeWorkspaceId === workspace.id" class="mt-3">
          <span class="badge-success">Active</span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card p-12 text-center">
      <FolderIcon class="w-12 h-12 text-dark-600 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-white mb-2">No Workspaces</h3>
      <p class="text-dark-400 mb-6">
        Create a workspace to organize your SQL queries and schemas.
      </p>
      <button @click="showCreateModal = true" class="btn-primary">
        <PlusIcon class="w-4 h-4 mr-2 inline" />
        Create First Workspace
      </button>
    </div>

    <!-- Create Modal -->
    <Teleport to="body">
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showCreateModal = false"
      >
        <div class="card w-full max-w-md mx-4 p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Create Workspace</h2>

          <div class="space-y-4">
            <div>
              <label class="label">Name</label>
              <input
                v-model="newWorkspace.name"
                type="text"
                class="input"
                placeholder="My Workspace"
              />
            </div>

            <div>
              <label class="label">Description</label>
              <input
                v-model="newWorkspace.description"
                type="text"
                class="input"
                placeholder="Optional description"
              />
            </div>

            <div>
              <label class="label">Schema (JSON)</label>
              <textarea
                v-model="newWorkspace.schema"
                class="sql-editor h-32"
                placeholder='{"tables": [...]}'
              ></textarea>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button @click="showCreateModal = false" class="btn-secondary">
              Cancel
            </button>
            <button
              @click="createWorkspace"
              :disabled="!newWorkspace.name"
              class="btn-primary"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Edit Modal -->
    <Teleport to="body">
      <div
        v-if="editingWorkspace"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="editingWorkspace = null"
      >
        <div class="card w-full max-w-md mx-4 p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Edit Workspace</h2>

          <div class="space-y-4">
            <div>
              <label class="label">Name</label>
              <input
                v-model="editingWorkspace.name"
                type="text"
                class="input"
              />
            </div>

            <div>
              <label class="label">Description</label>
              <input
                v-model="editingWorkspace.description"
                type="text"
                class="input"
              />
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button @click="editingWorkspace = null" class="btn-secondary">
              Cancel
            </button>
            <button @click="saveWorkspace" class="btn-primary">
              Save
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
