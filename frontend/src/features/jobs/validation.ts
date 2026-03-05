import type { JobCreatePayload } from '@/features/jobs/types'

export type JobFormState = {
  name: string
  station_uuid: string
  limit_cm: string
  recipients: string
  alert_recipient: string
  locale: 'de' | 'en'
  schedule_cron: string
  repeat_alerts_on_check: boolean
  enabled: boolean
}

export const parseRecipients = (input: string): string[] => {
  const seen = new Set<string>()
  const recipients: string[] = []

  input
    .split(/[\n,;]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .forEach((item) => {
      const normalized = item.toLowerCase()
      if (!seen.has(normalized)) {
        seen.add(normalized)
        recipients.push(item)
      }
    })

  return recipients
}

const cronPattern = /^\S+\s+\S+\s+\S+\s+\S+\s+\S+$/

export const validateJobForm = (state: JobFormState): string | null => {
  if (!state.name.trim()) {
    return 'Name is required.'
  }

  if (!state.station_uuid.trim()) {
    return 'Station UUID is required.'
  }

  if (!state.alert_recipient.trim() || !state.alert_recipient.includes('@')) {
    return 'Alert recipient must be a valid email address.'
  }

  const recipients = parseRecipients(state.recipients)
  if (recipients.length < 1) {
    return 'At least one recipient is required.'
  }

  if (!recipients.every((email) => email.includes('@'))) {
    return 'Recipients must contain valid email addresses.'
  }

  if (!cronPattern.test(state.schedule_cron.trim())) {
    return 'Schedule must be a valid 5-field crontab expression.'
  }

  const limitCm = Number(state.limit_cm)
  if (Number.isNaN(limitCm) || limitCm <= -10000 || limitCm >= 100000) {
    return 'Limit must be between -10000 and 100000.'
  }

  return null
}

export const toCreatePayload = (state: JobFormState): JobCreatePayload => ({
  name: state.name.trim(),
  station_uuid: state.station_uuid.trim(),
  limit_cm: Number(state.limit_cm),
  recipients: parseRecipients(state.recipients),
  alert_recipient: state.alert_recipient.trim(),
  locale: state.locale,
  schedule_cron: state.schedule_cron.trim(),
  repeat_alerts_on_check: state.repeat_alerts_on_check,
})
