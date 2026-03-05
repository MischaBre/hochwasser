<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import { RouterLink, RouterView } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated, userEmail, signOut } = useAuth()
</script>

<template>
  <div class="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-6 md:px-8">
    <header class="mb-6 flex items-center justify-between rounded-lg border bg-card px-5 py-4">
      <div class="flex items-center gap-5">
        <div>
          <p class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Hochwasser</p>
          <h1 class="text-xl font-semibold md:text-2xl">Job Control</h1>
        </div>
        <nav class="hidden items-center gap-2 md:flex">
          <RouterLink class="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground" to="/">Overview</RouterLink>
          <RouterLink class="rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground" to="/jobs">Jobs</RouterLink>
        </nav>
      </div>
      <div class="flex items-center gap-3">
        <p v-if="isAuthenticated" class="hidden text-sm text-muted-foreground md:block">{{ userEmail }}</p>
        <Button
          v-if="isAuthenticated"
          variant="outline"
          size="sm"
          @click="signOut"
        >
          Sign out
        </Button>
      </div>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>
