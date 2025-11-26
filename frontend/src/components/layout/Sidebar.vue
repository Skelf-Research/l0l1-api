<script setup>
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import {
  HomeIcon,
  CommandLineIcon,
  FolderIcon,
  AcademicCapIcon,
  Cog6ToothIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CircleStackIcon,
  TableCellsIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  collapsed: Boolean
})

const emit = defineEmits(['toggle'])

const route = useRoute()

const navigation = [
  { name: 'Dashboard', path: '/', icon: HomeIcon },
  { name: 'SQL Workbench', path: '/workbench', icon: CommandLineIcon },
  { name: 'Databases', path: '/databases', icon: CircleStackIcon },
  { name: 'Schemas', path: '/schemas', icon: TableCellsIcon },
  { name: 'Workspaces', path: '/workspaces', icon: FolderIcon },
  { name: 'Learning', path: '/learning', icon: AcademicCapIcon },
  { name: 'Settings', path: '/settings', icon: Cog6ToothIcon }
]

const isActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <aside
    :class="[
      'flex flex-col bg-dark-950 border-r border-dark-800 transition-all duration-300',
      collapsed ? 'w-16' : 'w-64'
    ]"
  >
    <!-- Logo -->
    <div class="flex items-center h-16 px-4 border-b border-dark-800">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
          <span class="text-white font-bold text-sm">l0</span>
        </div>
        <span v-if="!collapsed" class="text-lg font-semibold text-white">l0l1</span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
      <RouterLink
        v-for="item in navigation"
        :key="item.path"
        :to="item.path"
        :class="[
          'flex items-center px-3 py-2.5 rounded-lg transition-colors group',
          isActive(item.path)
            ? 'bg-primary-600/20 text-primary-400'
            : 'text-dark-400 hover:bg-dark-800 hover:text-dark-100'
        ]"
      >
        <component
          :is="item.icon"
          :class="[
            'w-5 h-5 flex-shrink-0',
            isActive(item.path) ? 'text-primary-400' : 'text-dark-500 group-hover:text-dark-300'
          ]"
        />
        <span v-if="!collapsed" class="ml-3 text-sm font-medium">{{ item.name }}</span>
      </RouterLink>
    </nav>

    <!-- Collapse toggle -->
    <div class="p-2 border-t border-dark-800">
      <button
        @click="emit('toggle')"
        class="w-full flex items-center justify-center p-2 rounded-lg text-dark-400 hover:bg-dark-800 hover:text-dark-100 transition-colors"
      >
        <ChevronLeftIcon v-if="!collapsed" class="w-5 h-5" />
        <ChevronRightIcon v-else class="w-5 h-5" />
      </button>
    </div>
  </aside>
</template>
