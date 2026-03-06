import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'

export const useAuth = () => {
  const authStore = useAuthStore()
  const router = useRouter()
  const { isAuthenticated, session, userEmail, userId } = storeToRefs(authStore)

  const signOut = async () => {
    await authStore.signOut()
    router.push('/')
  }

  return {
    isAuthenticated,
    session,
    signOut,
    userEmail,
    userId,
  }
}
