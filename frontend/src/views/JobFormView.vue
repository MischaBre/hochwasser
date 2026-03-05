<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { Clock3, Gauge, Languages, MapPin, Send, Tag, Users } from 'lucide-vue-next'
import Alert from '@/components/ui/alert/Alert.vue'
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import Input from '@/components/ui/input/Input.vue'
import Label from '@/components/ui/label/Label.vue'
import Textarea from '@/components/ui/textarea/Textarea.vue'
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError, type ValidationIssue } from '@/api/client'
import { createJob, listJobs, updateJob } from '@/features/jobs/api'
import {
  hasJobFormErrors,
  toCreatePayload,
  validateJobForm,
  type JobFormErrors,
  type JobFormField,
  type JobFormState,
} from '@/features/jobs/validation'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()

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

const touched = reactive<Record<JobFormField, boolean>>({
  name: false,
  station_uuid: false,
  limit_cm: false,
  recipients: false,
  alert_recipient: false,
  locale: false,
  schedule_cron: false,
})

const submitAttempted = ref(false)
const serverErrors = reactive<JobFormErrors>({})
const clientErrors = computed(() => validateJobForm(form))

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

const clearServerError = (field: JobFormField | 'form'): void => {
  delete serverErrors[field]
}

const markTouched = (field: JobFormField): void => {
  touched[field] = true
}

const getFieldError = (field: JobFormField): string => {
  if (serverErrors[field]) {
    return serverErrors[field] as string
  }

  if (submitAttempted.value || touched[field]) {
    return clientErrors.value[field] ?? ''
  }

  return ''
}

const mapValidationIssues = (issues: ValidationIssue[]): JobFormErrors => {
  const nextErrors: JobFormErrors = {}

  for (const issue of issues) {
    const message = issue.msg?.trim()
    if (!message) {
      continue
    }

    const loc = issue.loc?.filter((value): value is string => typeof value === 'string') ?? []
    let field: JobFormField | undefined

    for (let index = loc.length - 1; index >= 0; index -= 1) {
      const value = loc[index]
      if (
        value === 'name'
        || value === 'station_uuid'
        || value === 'limit_cm'
        || value === 'recipients'
        || value === 'alert_recipient'
        || value === 'locale'
        || value === 'schedule_cron'
      ) {
        field = value
        break
      }
    }

    if (field && !nextErrors[field]) {
      nextErrors[field] = message
      continue
    }

    if (!nextErrors.form) {
      nextErrors.form = message
    }
  }

  return nextErrors
}

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

  for (const field of Object.keys(touched) as JobFormField[]) {
    touched[field] = false
  }

  submitAttempted.value = false
  for (const key of Object.keys(serverErrors) as Array<JobFormField | 'form'>) {
    delete serverErrors[key]
  }
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
    await queryClient.invalidateQueries({ queryKey: ['jobs'] })
    await router.push({ name: 'job-details', params: { jobUuid: job.job_uuid } })
  },
  onError: (error) => {
    if (error instanceof ApiError && error.validationIssues.length > 0) {
      const mappedErrors = mapValidationIssues(error.validationIssues)
      for (const key of Object.keys(serverErrors) as Array<JobFormField | 'form'>) {
        delete serverErrors[key]
      }
      for (const [key, value] of Object.entries(mappedErrors) as Array<[JobFormField | 'form', string]>) {
        serverErrors[key] = value
      }
    }
  },
})

const submitError = computed(() => {
  const error = submitMutation.error.value
  if (error instanceof ApiError) {
    if (error.validationIssues.length > 0) {
      return ''
    }
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return ''
})

const submit = async () => {
  submitAttempted.value = true
  clearServerError('form')

  if (hasJobFormErrors(clientErrors.value)) {
    return
  }

  await submitMutation.mutateAsync()
}
</script>

<template>
  <section>
    <Card>
      <CardHeader>
        <CardTitle>{{ isEditMode ? 'Edit job' : 'Create job' }}</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <Alert v-if="isEditMode && jobsQuery.isLoading.value">Loading job...</Alert>
          <Alert v-if="isEditMode && !jobsQuery.isLoading.value && !currentJob" variant="destructive">Job not found.</Alert>
          <Alert v-if="serverErrors.form" variant="destructive">{{ serverErrors.form }}</Alert>
          <Alert v-if="submitMutation.isError.value && submitError" variant="destructive">{{ submitError }}</Alert>

          <form class="grid gap-x-4 gap-y-6 md:grid-cols-2" @submit.prevent="submit">
            <div class="space-y-2">
              <Label for="job-name">Name</Label>
              <div class="relative">
                <Tag class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input id="job-name" v-model="form.name" class="pl-9" required @blur="markTouched('name')" @input="clearServerError('name')" />
              </div>
              <p v-if="getFieldError('name')" class="text-sm text-destructive">{{ getFieldError('name') }}</p>
            </div>

            <div class="space-y-2">
              <Label for="station-uuid">Station UUID</Label>
              <div class="relative">
                <MapPin class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="station-uuid"
                  v-model="form.station_uuid"
                  class="pl-9"
                  placeholder="e.g. 123e4567-e89b-12d3-a456-426614174000"
                  required
                  @blur="markTouched('station_uuid')"
                  @input="clearServerError('station_uuid')"
                />
              </div>
              <p v-if="getFieldError('station_uuid')" class="text-sm text-destructive">{{ getFieldError('station_uuid') }}</p>
            </div>

            <div class="space-y-2">
              <Label for="limit-cm">Limit (cm)</Label>
              <div class="relative">
                <Gauge class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="limit-cm"
                  v-model="form.limit_cm"
                  class="pl-9"
                  inputmode="decimal"
                  required
                  @blur="markTouched('limit_cm')"
                  @input="clearServerError('limit_cm')"
                />
              </div>
              <p v-if="getFieldError('limit_cm')" class="text-sm text-destructive">{{ getFieldError('limit_cm') }}</p>
            </div>

            <div class="space-y-2">
              <Label for="locale">Locale</Label>
              <div class="relative">
                <Languages class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <select
                  id="locale"
                  v-model="form.locale"
                  class="flex h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  @blur="markTouched('locale')"
                  @change="clearServerError('locale')"
                >
                  <option value="de">German (de)</option>
                  <option value="en">English (en)</option>
                </select>
              </div>
              <p v-if="getFieldError('locale')" class="text-sm text-destructive">{{ getFieldError('locale') }}</p>
            </div>

            <div class="space-y-2 md:col-span-2">
              <Label for="alert-recipient">Alert recipient</Label>
              <div class="relative">
                <Send class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="alert-recipient"
                  v-model="form.alert_recipient"
                  class="pl-9"
                  type="email"
                  placeholder="alerts@example.com"
                  required
                  @blur="markTouched('alert_recipient')"
                  @input="clearServerError('alert_recipient')"
                />
              </div>
              <p v-if="getFieldError('alert_recipient')" class="text-sm text-destructive">{{ getFieldError('alert_recipient') }}</p>
            </div>

            <div class="space-y-2 md:col-span-2">
              <Label for="recipients">Recipients (comma or newline separated)</Label>
              <div class="relative">
                <Users class="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Textarea
                  id="recipients"
                  v-model="form.recipients"
                  rows="3"
                  class="pl-9"
                  placeholder="alice@example.com, bob@example.com"
                  required
                  @blur="markTouched('recipients')"
                  @input="clearServerError('recipients')"
                />
              </div>
              <p class="text-xs text-muted-foreground">Separate addresses with commas, semicolons, or new lines.</p>
              <p v-if="getFieldError('recipients')" class="text-sm text-destructive">{{ getFieldError('recipients') }}</p>
            </div>

            <div class="space-y-2 md:col-span-2">
              <Label for="schedule-cron">Schedule cron (5 fields)</Label>
              <div class="relative">
                <Clock3 class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="schedule-cron"
                  v-model="form.schedule_cron"
                  class="pl-9"
                  placeholder="*/15 * * * *"
                  required
                  @blur="markTouched('schedule_cron')"
                  @input="clearServerError('schedule_cron')"
                />
              </div>
              <p class="text-xs text-muted-foreground">Cron format: minute hour day month weekday.</p>
              <p v-if="getFieldError('schedule_cron')" class="text-sm text-destructive">{{ getFieldError('schedule_cron') }}</p>
            </div>

            <div class="md:col-span-2 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
              <div class="flex items-center gap-2">
                <input id="repeat-alerts" v-model="form.repeat_alerts_on_check" type="checkbox" class="h-4 w-4 rounded border-input" />
                <Label for="repeat-alerts">Repeat alerts on check</Label>
              </div>
              <div v-if="isEditMode" class="flex items-center gap-2">
                <input id="job-enabled" v-model="form.enabled" type="checkbox" class="h-4 w-4 rounded border-input" />
                <Label for="job-enabled">Enabled</Label>
              </div>
            </div>

            <div class="md:col-span-2 flex items-center justify-end gap-2 pt-2">
              <Button variant="ghost" @click="router.push({ name: 'jobs' })">Cancel</Button>
              <Button
                type="submit"
                :disabled="submitMutation.isPending.value || hasJobFormErrors(clientErrors) || (isEditMode && !currentJob)"
              >
                {{ submitMutation.isPending.value ? 'Saving...' : (isEditMode ? 'Save changes' : 'Create job') }}
              </Button>
            </div>
          </form>
        </div>
      </CardContent>
    </Card>
  </section>
</template>
