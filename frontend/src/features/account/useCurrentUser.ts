import { useQuery } from '@tanstack/vue-query'
import { storeToRefs } from 'pinia'
import { getMe } from '@/features/account/api'
import { useAuthStore } from '@/stores/auth'

export const useCurrentUserQuery = () => {
  const authStore = useAuthStore()
  const { isAuthenticated, ready } = storeToRefs(authStore)

  return useQuery({
    queryKey: ['current-user'],
    queryFn: getMe,
    enabled: () => ready.value && isAuthenticated.value,
    staleTime: 60_000,
    retry: false,
  })
}
