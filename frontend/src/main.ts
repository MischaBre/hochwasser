import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@/styles/main.css'
import App from './App.vue'
import router from '@/router'
import { queryPlugin } from '@/plugins/query'
import { useAuthStore } from '@/stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(queryPlugin)

useAuthStore().initialize()

app.mount('#app')
