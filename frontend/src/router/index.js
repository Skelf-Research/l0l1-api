import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { title: 'Dashboard' }
    },
    {
      path: '/workbench',
      name: 'workbench',
      component: () => import('@/views/WorkbenchView.vue'),
      meta: { title: 'SQL Workbench' }
    },
    {
      path: '/databases',
      name: 'databases',
      component: () => import('@/views/DatabaseView.vue'),
      meta: { title: 'Database Connections' }
    },
    {
      path: '/schemas',
      name: 'schemas',
      component: () => import('@/views/SchemaView.vue'),
      meta: { title: 'Schema Management' }
    },
    {
      path: '/workspaces',
      name: 'workspaces',
      component: () => import('@/views/WorkspacesView.vue'),
      meta: { title: 'Workspaces' }
    },
    {
      path: '/learning',
      name: 'learning',
      component: () => import('@/views/LearningView.vue'),
      meta: { title: 'Learning & Patterns' }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: 'Settings' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} | l0l1`
  next()
})

export default router
