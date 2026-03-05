<script setup lang="ts">
import Card from 'primevue/card'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { computed } from 'vue'
import { useCurrentUserQuery } from '@/features/account/useCurrentUser'
import { useAuth } from '@/composables/useAuth'

const { isAuthenticated, userId } = useAuth()
const meQuery = useCurrentUserQuery()
const meData = computed(() => meQuery.data.value)
const isMeSuccess = computed(() => meQuery.isSuccess.value && Boolean(meData.value))
const isMeError = computed(() => meQuery.isError.value && !meData.value)

const membershipTagSeverity = computed(() => (meData.value?.role === 'admin' ? 'danger' : 'info'))

const membershipErrorMessage = computed(() => {
  const error = meQuery.error.value as unknown

  if (typeof error === 'object' && error !== null && 'status' in error && typeof (error as { status?: unknown }).status === 'number') {
    const status = (error as { status: number }).status

    if (status === 403) {
      return 'Authenticated, but no organization membership was found.'
    }

    if (status === 401) {
      return 'Session expired. Please sign in again.'
    }

    if ('message' in error && typeof (error as { message?: unknown }).message === 'string') {
      return (error as { message: string }).message
    }

    return `Membership check failed with status ${status}.`
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Could not verify membership status.'
})
</script>

<template>
  <section class="grid gap-5 md:grid-cols-[2fr_1fr]">
    <Card class="glass-card rounded-2xl">
      <template #title>
        <h2 class="text-2xl font-semibold text-ink-900">Account overview</h2>
      </template>
      <template #content>
        <div class="space-y-3 text-sm text-ink-700">
          <p class="text-balance leading-6">Membership data is loaded from <code>/v1/me</code> during authenticated app usage.</p>
          <div v-if="isMeSuccess" class="space-y-2 rounded-xl bg-surface-100 p-4">
            <div class="flex items-center justify-between">
              <span>Role</span>
              <Tag :severity="membershipTagSeverity" :value="meData?.role" />
            </div>
            <div class="flex items-center justify-between gap-4">
              <span>Organization</span>
              <code class="max-w-[220px] truncate rounded bg-surface-200 px-2 py-1 text-xs">{{ meData?.org_id }}</code>
            </div>
          </div>
          <Message v-else-if="isMeError" severity="error" :closable="false">{{ membershipErrorMessage }}</Message>
          <p v-else class="text-xs text-ink-500">Waiting for session to load.</p>
        </div>
      </template>
    </Card>

    <Card class="glass-card rounded-2xl">
      <template #title>
        <h3 class="text-lg font-semibold text-ink-900">Session</h3>
      </template>
      <template #content>
        <div class="space-y-3 text-sm text-ink-700">
          <div class="flex items-center justify-between">
            <span>Status</span>
            <Tag :severity="isAuthenticated ? 'success' : 'warning'" :value="isAuthenticated ? 'Authenticated' : 'Guest'" />
          </div>
          <div class="flex items-center justify-between">
            <span>User ID</span>
            <code class="max-w-[190px] truncate rounded bg-surface-200 px-2 py-1 text-xs">{{ userId || 'Not signed in' }}</code>
          </div>
        </div>
      </template>
    </Card>
  </section>
</template>
