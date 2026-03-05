<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputSwitch from 'primevue/inputswitch'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { deleteJob, listJobs } from '@/features/jobs/api'

const router = useRouter()
const queryClient = useQueryClient()
const toast = useToast()
const includeDisabled = ref(false)

const jobsQuery = useQuery({
  queryKey: computed(() => ['jobs', includeDisabled.value]),
  queryFn: () => listJobs(includeDisabled.value),
})

const deleteMutation = useMutation({
  mutationFn: deleteJob,
  onSuccess: async () => {
    toast.add({
      severity: 'success',
      summary: 'Job deleted',
      detail: 'The job was disabled successfully.',
      life: 2500,
    })
    await queryClient.invalidateQueries({ queryKey: ['jobs'] })
  },
  onError: () => {
    toast.add({
      severity: 'error',
      summary: 'Delete failed',
      detail: 'Could not delete the job. Please try again.',
      life: 3500,
    })
  },
})

const jobs = computed(() => jobsQuery.data.value ?? [])

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
    <Card class="glass-card rounded-2xl">
      <template #title>
        <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <h2 class="text-2xl font-semibold text-ink-900">Jobs</h2>
          <Button label="Create job" icon="pi pi-plus" @click="goToCreate" />
        </div>
      </template>
      <template #content>
        <div class="mb-4 flex items-center gap-2 text-sm text-ink-700">
          <InputSwitch v-model="includeDisabled" input-id="include-disabled" />
          <label for="include-disabled">Include disabled jobs</label>
        </div>

        <Message v-if="jobsQuery.isError.value" severity="error" :closable="false">{{ errorMessage }}</Message>
        <Message v-if="deleteMutation.isError.value" severity="error" :closable="false">{{ deleteErrorMessage }}</Message>

        <div v-if="jobsQuery.isLoading.value" class="text-sm text-ink-500">Loading jobs...</div>

        <div v-else-if="jobs.length === 0" class="rounded-xl bg-surface-100 p-4 text-sm text-ink-700">No jobs found.</div>

        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-[760px] border-collapse text-left text-sm">
            <thead>
              <tr class="border-b border-surface-200 text-xs uppercase tracking-[0.12em] text-ink-500">
                <th class="py-3 pr-4">Name</th>
                <th class="py-3 pr-4">Station</th>
                <th class="py-3 pr-4">Limit</th>
                <th class="py-3 pr-4">Locale</th>
                <th class="py-3 pr-4">Status</th>
                <th class="py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in jobs" :key="job.job_uuid" class="border-b border-surface-200/80 last:border-none">
                <td class="py-3 pr-4 font-semibold text-ink-900">{{ job.name }}</td>
                <td class="py-3 pr-4 text-ink-700">{{ job.station_uuid }}</td>
                <td class="py-3 pr-4 text-ink-700">{{ job.limit_cm }} cm</td>
                <td class="py-3 pr-4 text-ink-700">{{ job.locale }}</td>
                <td class="py-3 pr-4">
                  <Tag :severity="job.enabled ? 'success' : 'warning'" :value="job.enabled ? 'Enabled' : 'Disabled'" />
                </td>
                <td class="py-3 text-right">
                  <div class="flex justify-end gap-2">
                    <Button text size="small" label="View" @click="router.push({ name: 'job-details', params: { jobUuid: job.job_uuid } })" />
                    <Button text size="small" label="Edit" @click="router.push({ name: 'job-edit', params: { jobUuid: job.job_uuid } })" />
                    <Button
                      text
                      severity="danger"
                      size="small"
                      label="Delete"
                      :loading="deleteMutation.isPending.value"
                      :disabled="deleteMutation.isPending.value"
                      @click="handleDelete(job.job_uuid)"
                    />
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </Card>
  </section>
</template>
