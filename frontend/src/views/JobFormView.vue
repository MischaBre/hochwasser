<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Checkbox from 'primevue/checkbox'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Textarea from 'primevue/textarea'
import { useToast } from 'primevue/usetoast'
import { computed, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { createJob, listJobs, updateJob } from '@/features/jobs/api'
import { toCreatePayload, validateJobForm, type JobFormState } from '@/features/jobs/validation'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const toast = useToast()

const jobUuid = computed(() => route.params.jobUuid as string | undefined)
const isEditMode = computed(() => route.name === 'job-edit')

const form = reactive<JobFormState>({
  name: '',
  station_uuid: '',
  limit_cm: '0',
  recipients: '',
  alert_recipient: '',
  locale: 'de',
  schedule_cron: '*/15 * * * *',
  repeat_alerts_on_check: false,
  enabled: true,
})

const validationError = computed(() => validateJobForm(form))

const jobsQuery = useQuery({
  queryKey: ['jobs', 'all'],
  queryFn: () => listJobs(true),
  enabled: isEditMode,
})

const currentJob = computed(() => {
  if (!jobUuid.value) {
    return null
  }

  return jobsQuery.data.value?.find((job) => job.job_uuid === jobUuid.value) ?? null
})

watch(currentJob, (job) => {
  if (!job) {
    return
  }

  form.name = job.name
  form.station_uuid = job.station_uuid
  form.limit_cm = String(job.limit_cm)
  form.recipients = job.recipients.join(', ')
  form.alert_recipient = job.alert_recipient
  form.locale = job.locale
  form.schedule_cron = job.schedule_cron
  form.repeat_alerts_on_check = job.repeat_alerts_on_check
  form.enabled = job.enabled
}, { immediate: true })

const submitMutation = useMutation({
  mutationFn: async () => {
    const payload = toCreatePayload(form)

    if (isEditMode.value && jobUuid.value) {
      return updateJob(jobUuid.value, { ...payload, enabled: form.enabled })
    }

    return createJob(payload)
  },
  onSuccess: async (job) => {
    toast.add({
      severity: 'success',
      summary: isEditMode.value ? 'Job updated' : 'Job created',
      detail: isEditMode.value ? 'Changes were saved successfully.' : 'New job saved successfully.',
      life: 2500,
    })
    await queryClient.invalidateQueries({ queryKey: ['jobs'] })
    await router.push({ name: 'job-details', params: { jobUuid: job.job_uuid } })
  },
  onError: () => {
    toast.add({
      severity: 'error',
      summary: 'Save failed',
      detail: 'Could not save the job. Please review the fields.',
      life: 3500,
    })
  },
})

const submitError = computed(() => {
  const error = submitMutation.error.value
  if (error instanceof ApiError) {
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return ''
})

const submit = async () => {
  if (validationError.value) {
    toast.add({
      severity: 'warn',
      summary: 'Validation issue',
      detail: validationError.value,
      life: 2500,
    })
    return
  }

  await submitMutation.mutateAsync()
}
</script>

<template>
  <section>
    <Card class="glass-card rounded-2xl">
      <template #title>
        <h2 class="text-2xl font-semibold text-ink-900">{{ isEditMode ? 'Edit job' : 'Create job' }}</h2>
      </template>
      <template #content>
        <div class="space-y-4">
          <Message v-if="isEditMode && jobsQuery.isLoading.value" severity="info" :closable="false">Loading job...</Message>
          <Message v-if="isEditMode && !jobsQuery.isLoading.value && !currentJob" severity="error" :closable="false">Job not found.</Message>
          <Message v-if="validationError" severity="warn" :closable="false">{{ validationError }}</Message>
          <Message v-if="submitMutation.isError.value && submitError" severity="error" :closable="false">{{ submitError }}</Message>

          <form class="grid gap-4 md:grid-cols-2" @submit.prevent="submit">
            <span class="p-float-label block">
              <InputText id="job-name" v-model="form.name" class="w-full" required />
              <label for="job-name">Name</label>
            </span>

            <span class="p-float-label block">
              <InputText id="station-uuid" v-model="form.station_uuid" class="w-full" required />
              <label for="station-uuid">Station UUID</label>
            </span>

            <span class="p-float-label block">
              <InputText id="limit-cm" v-model="form.limit_cm" class="w-full" inputmode="decimal" required />
              <label for="limit-cm">Limit (cm)</label>
            </span>

            <span class="p-float-label block">
              <Dropdown
                id="locale"
                v-model="form.locale"
                class="w-full"
                :options="[
                  { label: 'German (de)', value: 'de' },
                  { label: 'English (en)', value: 'en' },
                ]"
                option-label="label"
                option-value="value"
              />
              <label for="locale">Locale</label>
            </span>

            <span class="p-float-label block md:col-span-2">
              <InputText id="alert-recipient" v-model="form.alert_recipient" class="w-full" required />
              <label for="alert-recipient">Alert recipient</label>
            </span>

            <span class="p-float-label block md:col-span-2">
              <Textarea id="recipients" v-model="form.recipients" rows="3" class="w-full" required />
              <label for="recipients">Recipients (comma or newline separated)</label>
            </span>

            <span class="p-float-label block md:col-span-2">
              <InputText id="schedule-cron" v-model="form.schedule_cron" class="w-full" required />
              <label for="schedule-cron">Schedule cron (5 fields)</label>
            </span>

            <div class="md:col-span-2 flex flex-wrap items-center gap-4 text-sm text-ink-700">
              <div class="flex items-center gap-2">
                <Checkbox v-model="form.repeat_alerts_on_check" binary input-id="repeat-alerts" />
                <label for="repeat-alerts">Repeat alerts on check</label>
              </div>
              <div v-if="isEditMode" class="flex items-center gap-2">
                <Checkbox v-model="form.enabled" binary input-id="job-enabled" />
                <label for="job-enabled">Enabled</label>
              </div>
            </div>

            <div class="md:col-span-2 flex items-center justify-end gap-2 pt-2">
              <Button text label="Cancel" @click="router.push({ name: 'jobs' })" />
              <Button
                type="submit"
                :label="isEditMode ? 'Save changes' : 'Create job'"
                :loading="submitMutation.isPending.value"
                :disabled="Boolean(validationError) || (isEditMode && !currentJob)"
              />
            </div>
          </form>
        </div>
      </template>
    </Card>
  </section>
</template>
