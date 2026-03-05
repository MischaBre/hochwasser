<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { getJobOutbox, getJobStatus, listJobs } from '@/features/jobs/api'

const route = useRoute()
const router = useRouter()
const jobUuid = computed(() => route.params.jobUuid as string)

const outboxLimit = ref(20)
const outboxOffset = ref(0)

const jobsQuery = useQuery({
  queryKey: ['jobs', 'all'],
  queryFn: () => listJobs(true),
})

const job = computed(() => jobsQuery.data.value?.find((item) => item.job_uuid === jobUuid.value))

const statusQuery = useQuery({
  queryKey: computed(() => ['job-status', jobUuid.value]),
  queryFn: () => getJobStatus(jobUuid.value),
})

const outboxQuery = useQuery({
  queryKey: computed(() => ['job-outbox', jobUuid.value, outboxLimit.value, outboxOffset.value]),
  queryFn: () => getJobOutbox(jobUuid.value, outboxLimit.value, outboxOffset.value),
})

const statusError = computed(() => {
  const error = statusQuery.error.value
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return ''
})

const outboxError = computed(() => {
  const error = outboxQuery.error.value
  if (error instanceof ApiError) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return ''
})

const nextPage = () => {
  if ((outboxQuery.data.value?.items.length ?? 0) < outboxLimit.value) {
    return
  }

  outboxOffset.value += outboxLimit.value
}

const prevPage = () => {
  outboxOffset.value = Math.max(0, outboxOffset.value - outboxLimit.value)
}
</script>

<template>
  <section class="space-y-4">
    <Card class="glass-card rounded-2xl">
      <template #title>
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <h2 class="text-2xl font-semibold text-ink-900">{{ job?.name || 'Job details' }}</h2>
          <div class="flex gap-2">
            <Button text label="Back" icon="pi pi-arrow-left" @click="router.push({ name: 'jobs' })" />
            <Button
              label="Edit"
              icon="pi pi-pencil"
              :disabled="!job"
              @click="router.push({ name: 'job-edit', params: { jobUuid } })"
            />
          </div>
        </div>
      </template>
      <template #content>
        <div v-if="jobsQuery.isLoading.value" class="text-sm text-ink-500">Loading job...</div>
        <Message v-else-if="!job" severity="error" :closable="false">Job not found.</Message>
        <div v-else class="grid gap-4 md:grid-cols-2 text-sm text-ink-700">
          <div class="space-y-2 rounded-xl bg-surface-100 p-4">
            <p><span class="font-semibold text-ink-900">Station:</span> {{ job.station_uuid }}</p>
            <p><span class="font-semibold text-ink-900">Limit:</span> {{ job.limit_cm }} cm</p>
            <p><span class="font-semibold text-ink-900">Schedule:</span> {{ job.schedule_cron }}</p>
            <p><span class="font-semibold text-ink-900">Locale:</span> {{ job.locale }}</p>
            <p><span class="font-semibold text-ink-900">Alert recipient:</span> {{ job.alert_recipient }}</p>
            <p><span class="font-semibold text-ink-900">Recipients:</span> {{ job.recipients.join(', ') }}</p>
            <Tag :severity="job.enabled ? 'success' : 'warning'" :value="job.enabled ? 'Enabled' : 'Disabled'" />
          </div>

          <div class="space-y-2 rounded-xl bg-surface-100 p-4">
            <p class="font-semibold text-ink-900">Status</p>
            <Message v-if="statusQuery.isError.value && statusError" severity="error" :closable="false">{{ statusError }}</Message>
            <div v-else-if="statusQuery.isLoading.value" class="text-sm text-ink-500">Loading status...</div>
            <div v-else-if="statusQuery.data.value" class="space-y-2">
              <p><span class="font-semibold text-ink-900">State:</span> {{ statusQuery.data.value.state || 'n/a' }}</p>
              <p><span class="font-semibold text-ink-900">State since:</span> {{ statusQuery.data.value.state_since || 'n/a' }}</p>
              <p>
                <span class="font-semibold text-ink-900">Predicted peak:</span>
                {{ statusQuery.data.value.predicted_peak_cm ?? 'n/a' }} at {{ statusQuery.data.value.predicted_peak_at || 'n/a' }}
              </p>
              <p><span class="font-semibold text-ink-900">Last notified:</span> {{ statusQuery.data.value.last_notified_at || 'n/a' }}</p>
            </div>
          </div>
        </div>
      </template>
    </Card>

    <Card class="glass-card rounded-2xl">
      <template #title>
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-semibold text-ink-900">Outbox</h3>
          <p class="text-xs text-ink-500">limit {{ outboxLimit }} | offset {{ outboxOffset }}</p>
        </div>
      </template>
      <template #content>
        <Message v-if="outboxQuery.isError.value && outboxError" severity="error" :closable="false">{{ outboxError }}</Message>
        <div v-else-if="outboxQuery.isLoading.value" class="text-sm text-ink-500">Loading outbox...</div>
        <div v-else-if="!outboxQuery.data.value || outboxQuery.data.value.items.length === 0" class="text-sm text-ink-700">No outbox entries.</div>
        <div v-else class="space-y-4">
          <div class="overflow-x-auto">
            <table class="w-full min-w-[820px] border-collapse text-left text-sm">
              <thead>
                <tr class="border-b border-surface-200 text-xs uppercase tracking-[0.12em] text-ink-500">
                  <th class="py-3 pr-4">ID</th>
                  <th class="py-3 pr-4">Target</th>
                  <th class="py-3 pr-4">Reason</th>
                  <th class="py-3 pr-4">Status</th>
                  <th class="py-3 pr-4">Attempts</th>
                  <th class="py-3">Next attempt</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="entry in outboxQuery.data.value.items" :key="entry.id" class="border-b border-surface-200/80 last:border-none">
                  <td class="py-3 pr-4">{{ entry.id }}</td>
                  <td class="py-3 pr-4">{{ entry.target_state }}</td>
                  <td class="py-3 pr-4">{{ entry.trigger_reason }}</td>
                  <td class="py-3 pr-4">{{ entry.status }}</td>
                  <td class="py-3 pr-4">{{ entry.attempt_count }}</td>
                  <td class="py-3">{{ entry.next_attempt_at }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="flex justify-end gap-2">
            <Button text label="Previous" :disabled="outboxOffset === 0" @click="prevPage" />
            <Button
              text
              label="Next"
              :disabled="(outboxQuery.data.value?.items.length ?? 0) < outboxLimit"
              @click="nextPage"
            />
          </div>
        </div>
      </template>
    </Card>
  </section>
</template>
