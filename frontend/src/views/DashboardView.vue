<script setup lang="ts">
import Alert from '@/components/ui/alert/Alert.vue'
import Badge from '@/components/ui/badge/Badge.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
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
    <Card>
      <CardHeader>
        <CardTitle>Account overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3 text-sm text-muted-foreground">
          <p class="leading-6">Membership data is loaded from <code>/v1/me</code> during authenticated app usage.</p>
          <div v-if="isMeSuccess" class="space-y-2 rounded-md border bg-muted/30 p-4">
            <div class="flex items-center justify-between">
              <span>Role</span>
              <Badge :variant="membershipTagSeverity === 'danger' ? 'destructive' : 'secondary'">{{ meData?.role }}</Badge>
            </div>
            <div class="flex items-center justify-between gap-4">
              <span>Organization</span>
              <code class="max-w-[220px] truncate rounded bg-muted px-2 py-1 text-xs">{{ meData?.org_id }}</code>
            </div>
          </div>
          <Alert v-else-if="isMeError" variant="destructive">{{ membershipErrorMessage }}</Alert>
          <p v-else class="text-xs text-muted-foreground">Waiting for session to load.</p>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle class="text-lg">Session</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3 text-sm text-muted-foreground">
          <div class="flex items-center justify-between">
            <span>Status</span>
            <Badge :variant="isAuthenticated ? 'default' : 'secondary'">{{ isAuthenticated ? 'Authenticated' : 'Guest' }}</Badge>
          </div>
          <div class="flex items-center justify-between">
            <span>User ID</span>
            <code class="max-w-[190px] truncate rounded bg-muted px-2 py-1 text-xs">{{ userId || 'Not signed in' }}</code>
          </div>
        </div>
      </CardContent>
    </Card>
  </section>
</template>
