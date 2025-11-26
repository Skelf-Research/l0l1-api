import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.mount('#app')

// Start API health check after mounting
import { useApiStore } from './stores/api'
const apiStore = useApiStore()
apiStore.startHealthCheck()
