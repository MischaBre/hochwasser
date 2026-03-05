import type { App } from 'vue'
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export const queryPlugin = {
  install(app: App) {
    app.use(VueQueryPlugin, { queryClient })
  },
}
