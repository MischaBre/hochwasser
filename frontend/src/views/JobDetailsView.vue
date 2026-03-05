<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import Alert from '@/components/ui/alert/Alert.vue'
import Badge from '@/components/ui/badge/Badge.vue'
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { getJobOutbox, getJobStatus, listJobs } from '@/features/jobs/api'
import { listStations } from '@/features/stations/api'

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

const stationQuery = useQuery({
  queryKey: computed(() => ['stations', 'job-details', job.value?.station_uuid || '']),
  queryFn: () => listStations({ uuids: [job.value?.station_uuid || ''], limit: 1, offset: 0 }),
  enabled: computed(() => Boolean(job.value?.station_uuid)),
  staleTime: 5 * 60 * 1000,
})

const station = computed(() => stationQuery.data.value?.items[0] ?? null)

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
    <Card>
      <CardHeader>
        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <CardTitle>{{ job?.name || 'Job details' }}</CardTitle>
          <div class="flex gap-2">
            <Button variant="ghost" @click="router.push({ name: 'jobs' })">Back</Button>
            <Button
              variant="outline"
              :disabled="!job"
              @click="router.push({ name: 'job-edit', params: { jobUuid } })"
            >
              Edit
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div v-if="jobsQuery.isLoading.value" class="text-sm text-muted-foreground">Loading job...</div>
        <Alert v-else-if="!job" variant="destructive">Job not found.</Alert>
        <div v-else class="grid gap-4 text-sm text-muted-foreground md:grid-cols-2">
          <div class="space-y-2 rounded-md border bg-muted/30 p-4">
            <p>
              <span class="font-semibold text-foreground">Station:</span>
              {{ station ? `${station.shortname} - ${station.longname}` : job.station_uuid }}
            </p>
            <p>
              <span class="font-semibold text-foreground">Water:</span>
              {{ station?.water_longname || station?.water_shortname || 'n/a' }}
            </p>
            <p>
              <span class="font-semibold text-foreground">Agency:</span>
              {{ station?.agency || 'n/a' }}
            </p>
            <p>
              <span class="font-semibold text-foreground">Coordinates:</span>
              {{ station?.latitude ?? 'n/a' }}, {{ station?.longitude ?? 'n/a' }}
            </p>
            <p><span class="font-semibold text-foreground">Station UUID:</span> {{ job.station_uuid }}</p>
            <p><span class="font-semibold text-foreground">Limit:</span> {{ job.limit_cm }} cm</p>
            <p><span class="font-semibold text-foreground">Schedule:</span> {{ job.schedule_cron }}</p>
            <p><span class="font-semibold text-foreground">Locale:</span> {{ job.locale }}</p>
            <p><span class="font-semibold text-foreground">Alert recipient:</span> {{ job.alert_recipient }}</p>
            <p><span class="font-semibold text-foreground">Recipients:</span> {{ job.recipients.join(', ') }}</p>
            <Badge :variant="job.enabled ? 'default' : 'secondary'">{{ job.enabled ? 'Enabled' : 'Disabled' }}</Badge>
          </div>

          <div class="space-y-2 rounded-md border bg-muted/30 p-4">
            <p class="font-semibold text-foreground">Status</p>
            <Alert v-if="statusQuery.isError.value && statusError" variant="destructive">{{ statusError }}</Alert>
            <div v-else-if="statusQuery.isLoading.value" class="text-sm text-muted-foreground">Loading status...</div>
            <div v-else-if="statusQuery.data.value" class="space-y-2">
              <p><span class="font-semibold text-foreground">State:</span> {{ statusQuery.data.value.state || 'n/a' }}</p>
              <p><span class="font-semibold text-foreground">State since:</span> {{ statusQuery.data.value.state_since || 'n/a' }}</p>
              <p>
                <span class="font-semibold text-foreground">Predicted peak:</span>
                {{ statusQuery.data.value.predicted_peak_cm ?? 'n/a' }} at {{ statusQuery.data.value.predicted_peak_at || 'n/a' }}
              </p>
              <p><span class="font-semibold text-foreground">Last notified:</span> {{ statusQuery.data.value.last_notified_at || 'n/a' }}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <CardTitle>Outbox</CardTitle>
          <p class="text-xs text-muted-foreground">limit {{ outboxLimit }} | offset {{ outboxOffset }}</p>
        </div>
      </CardHeader>
      <CardContent>
        <Alert v-if="outboxQuery.isError.value && outboxError" variant="destructive">{{ outboxError }}</Alert>
        <div v-else-if="outboxQuery.isLoading.value" class="text-sm text-muted-foreground">Loading outbox...</div>
        <div v-else-if="!outboxQuery.data.value || outboxQuery.data.value.items.length === 0" class="text-sm text-muted-foreground">No outbox entries.</div>
        <div v-else class="space-y-4">
          <div class="overflow-x-auto">
            <table class="w-full min-w-[820px] border-collapse text-left text-sm">
              <thead>
                <tr class="border-b text-xs uppercase tracking-wide text-muted-foreground">
                  <th class="py-3 pr-4">ID</th>
                  <th class="py-3 pr-4">Target</th>
                  <th class="py-3 pr-4">Reason</th>
                  <th class="py-3 pr-4">Status</th>
                  <th class="py-3 pr-4">Attempts</th>
                  <th class="py-3">Next attempt</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="entry in outboxQuery.data.value.items" :key="entry.id" class="border-b last:border-none">
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
            <Button variant="outline" size="sm" :disabled="outboxOffset === 0" @click="prevPage">Previous</Button>
            <Button
              variant="outline"
              size="sm"
              :disabled="(outboxQuery.data.value?.items.length ?? 0) < outboxLimit"
              @click="nextPage"
            >
              Next
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  </section>
</template>
