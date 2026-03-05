<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import Alert from '@/components/ui/alert/Alert.vue'
import Badge from '@/components/ui/badge/Badge.vue'
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import Label from '@/components/ui/label/Label.vue'
import Switch from '@/components/ui/switch/Switch.vue'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { deleteJob, listJobs } from '@/features/jobs/api'
import { listStations } from '@/features/stations/api'

const router = useRouter()
const queryClient = useQueryClient()
const includeDisabled = ref(false)
const infoMessage = ref('')

const jobsQuery = useQuery({
  queryKey: computed(() => ['jobs', includeDisabled.value]),
  queryFn: () => listJobs(includeDisabled.value),
})

const deleteMutation = useMutation({
  mutationFn: deleteJob,
  onSuccess: async () => {
    infoMessage.value = 'The job was disabled successfully.'
    await queryClient.invalidateQueries({ queryKey: ['jobs'] })
  },
})

const jobs = computed(() => jobsQuery.data.value ?? [])

const stationUuids = computed(() => {
  return Array.from(new Set(jobs.value.map((job) => job.station_uuid).filter(Boolean)))
})

const stationsQuery = useQuery({
  queryKey: computed(() => ['stations', 'jobs', stationUuids.value]),
  queryFn: () => listStations({ uuids: stationUuids.value, limit: stationUuids.value.length || 1, offset: 0 }),
  enabled: computed(() => stationUuids.value.length > 0),
  staleTime: 5 * 60 * 1000,
})

const stationsByUuid = computed(() => {
  const map = new Map<string, { label: string; detail: string }>()

  for (const station of stationsQuery.data.value?.items ?? []) {
    const water = station.water_longname || station.water_shortname
    const label = water ? `${station.shortname} - ${water}` : station.shortname
    const detail = [station.agency, station.uuid].filter(Boolean).join(' | ')
    map.set(station.uuid, { label, detail })
  }

  return map
})

const errorMessage = computed(() => {
  const error = jobsQuery.error.value
  if (error instanceof ApiError) {
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Could not load jobs.'
})

const deleteErrorMessage = computed(() => {
  const error = deleteMutation.error.value
  if (error instanceof ApiError) {
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return ''
})

const goToCreate = () => {
  router.push({ name: 'job-create' })
}

const handleDelete = async (jobUuid: string) => {
  const confirmed = window.confirm('Delete this job? It will be disabled (soft delete).')
  if (!confirmed) {
    return
  }

  await deleteMutation.mutateAsync(jobUuid)
}
</script>

<template>
  <section class="space-y-4">
    <Card>
      <CardHeader>
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <CardTitle>Jobs</CardTitle>
          <Button @click="goToCreate">Create job</Button>
        </div>
      </CardHeader>
      <CardContent>
        <div class="mb-4 flex items-center gap-2 text-sm text-muted-foreground">
          <Switch v-model="includeDisabled" input-id="include-disabled" />
          <Label for="include-disabled">Include disabled jobs</Label>
        </div>

        <Alert v-if="infoMessage">{{ infoMessage }}</Alert>
        <Alert v-if="jobsQuery.isError.value" variant="destructive">{{ errorMessage }}</Alert>
        <Alert v-if="deleteMutation.isError.value" variant="destructive">{{ deleteErrorMessage }}</Alert>

        <div v-if="jobsQuery.isLoading.value" class="text-sm text-muted-foreground">Loading jobs...</div>

        <div v-else-if="jobs.length === 0" class="rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">No jobs found.</div>

        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-[760px] border-collapse text-left text-sm">
            <thead>
              <tr class="border-b text-xs uppercase tracking-wide text-muted-foreground">
                <th class="py-3 pr-4">Name</th>
                <th class="py-3 pr-4">Station</th>
                <th class="py-3 pr-4">Limit</th>
                <th class="py-3 pr-4">Locale</th>
                <th class="py-3 pr-4">Status</th>
                <th class="py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in jobs" :key="job.job_uuid" class="border-b last:border-none">
                <td class="py-3 pr-4 font-semibold">{{ job.name }}</td>
                <td class="py-3 pr-4">
                  <p class="font-medium">{{ stationsByUuid.get(job.station_uuid)?.label || job.station_uuid }}</p>
                  <p class="text-xs text-muted-foreground">{{ stationsByUuid.get(job.station_uuid)?.detail || job.station_uuid }}</p>
                </td>
                <td class="py-3 pr-4 text-muted-foreground">{{ job.limit_cm }} cm</td>
                <td class="py-3 pr-4 text-muted-foreground">{{ job.locale }}</td>
                <td class="py-3 pr-4">
                  <Badge :variant="job.enabled ? 'default' : 'secondary'">{{ job.enabled ? 'Enabled' : 'Disabled' }}</Badge>
                </td>
                <td class="py-3 text-right">
                  <div class="flex justify-end gap-2">
                    <Button variant="ghost" size="sm" @click="router.push({ name: 'job-details', params: { jobUuid: job.job_uuid } })">View</Button>
                    <Button variant="ghost" size="sm" @click="router.push({ name: 'job-edit', params: { jobUuid: job.job_uuid } })">Edit</Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      :disabled="deleteMutation.isPending.value"
                      @click="handleDelete(job.job_uuid)"
                    >
                      {{ deleteMutation.isPending.value ? 'Deleting...' : 'Delete' }}
                    </Button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </section>
</template>
