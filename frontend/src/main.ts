import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import 'primevue/resources/themes/lara-light-amber/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import '@/styles/main.css'
import App from './App.vue'
import router from '@/router'
import { queryPlugin } from '@/plugins/query'
import { useAuthStore } from '@/stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(queryPlugin)
app.use(PrimeVue, { ripple: true })
app.use(ToastService)

useAuthStore().initialize()

app.mount('#app')
