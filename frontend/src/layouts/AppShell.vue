<script setup lang="ts">
import Button from 'primevue/button'
import Toast from 'primevue/toast'
import { RouterLink, RouterView } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated, userEmail, signOut } = useAuth()
</script>

<template>
  <div class="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 pb-8 pt-6 md:px-8">
    <header class="glass-card animate-fade-in-up mb-6 flex items-center justify-between rounded-2xl px-5 py-4 md:px-7">
      <div class="flex items-center gap-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.24em] text-ink-500">Hochwasser</p>
          <h1 class="text-xl font-semibold text-ink-900 md:text-2xl">Job Control</h1>
        </div>
        <nav class="hidden items-center gap-2 md:flex">
          <RouterLink class="rounded-lg px-3 py-1.5 text-sm font-semibold text-ink-700 hover:bg-surface-100" to="/">Overview</RouterLink>
          <RouterLink class="rounded-lg px-3 py-1.5 text-sm font-semibold text-ink-700 hover:bg-surface-100" to="/jobs">Jobs</RouterLink>
        </nav>
      </div>
      <div class="flex items-center gap-3">
        <p v-if="isAuthenticated" class="hidden text-sm text-ink-700 md:block">{{ userEmail }}</p>
        <Button
          v-if="isAuthenticated"
          label="Sign out"
          icon="pi pi-sign-out"
          outlined
          size="small"
          @click="signOut"
        />
      </div>
    </header>

    <main class="animate-fade-in-up" style="animation-delay: 80ms">
      <RouterView />
    </main>

    <Toast position="bottom-right" />
  </div>
</template>
