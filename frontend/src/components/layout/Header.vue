<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useApiStore } from '@/stores/api'
import { BellIcon, UserCircleIcon } from '@heroicons/vue/24/outline'
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/vue/24/solid'

const route = useRoute()
const apiStore = useApiStore()
</script>

<template>
  <header class="flex items-center justify-between h-16 px-6 bg-dark-900 border-b border-dark-800">
    <!-- Page title -->
    <div>
      <h1 class="text-xl font-semibold text-white">{{ route.meta.title }}</h1>
    </div>

    <!-- Right side -->
    <div class="flex items-center space-x-4">
      <!-- API Status -->
      <div class="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-dark-800">
        <CheckCircleIcon
          v-if="apiStore.isConnected"
          class="w-4 h-4 text-green-400"
        />
        <ExclamationCircleIcon
          v-else
          class="w-4 h-4 text-red-400"
        />
        <span class="text-sm text-dark-300">
          API: {{ apiStore.isConnected ? 'Connected' : 'Disconnected' }}
        </span>
      </div>

      <!-- Notifications -->
      <button class="p-2 rounded-lg text-dark-400 hover:bg-dark-800 hover:text-dark-100 transition-colors">
        <BellIcon class="w-5 h-5" />
      </button>

      <!-- User -->
      <button class="p-2 rounded-lg text-dark-400 hover:bg-dark-800 hover:text-dark-100 transition-colors">
        <UserCircleIcon class="w-6 h-6" />
      </button>
    </div>
  </header>
</template>
