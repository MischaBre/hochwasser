import { createApp } from 'vue'
import { createPinia } from 'pinia'
import '@/styles/main.css'
import App from './App.vue'
import router from '@/router'
import { i18n, initializeAppLocale } from '@/plugins/i18n'
import { queryPlugin } from '@/plugins/query'
import { initSeo } from '@/plugins/seo'
import { useAuthStore } from '@/stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(queryPlugin)

useAuthStore().initialize()
initializeAppLocale()
initSeo(router)

app.mount('#app')
