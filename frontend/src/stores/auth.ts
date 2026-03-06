import type { Session } from '@supabase/supabase-js'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { supabase } from '@/lib/supabase'

export const useAuthStore = defineStore('auth', () => {
  const session = ref<Session | null>(null)
  const ready = ref(false)
  const loading = ref(false)

  const isAuthenticated = computed(() => Boolean(session.value?.access_token))
  const userId = computed(() => session.value?.user.id ?? '')
  const userEmail = computed(() => session.value?.user.email ?? '')

  const refreshSession = async () => {
    const { data, error } = await supabase.auth.getSession()

    if (error) {
      throw error
    }

    session.value = data.session
    ready.value = true
  }

  const initialize = () => {
    void refreshSession()

    supabase.auth.onAuthStateChange((_event, nextSession) => {
      session.value = nextSession
      ready.value = true
    })
  }

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  const signIn = async (email: string, password: string) => {
    loading.value = true

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        throw error
      }

      session.value = data.session
      ready.value = true
      return data
    } finally {
      loading.value = false
    }
  }

  const signUp = async (email: string, password: string) => {
    loading.value = true

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      })

      if (error) {
        throw error
      }

      session.value = data.session
      ready.value = true
      return data
    } finally {
      loading.value = false
    }
  }

  const getAccessToken = () => session.value?.access_token ?? null

  return {
    getAccessToken,
    initialize,
    isAuthenticated,
    loading,
    ready,
    refreshSession,
    session,
    signIn,
    signUp,
    signOut,
    userEmail,
    userId,
  }
})
