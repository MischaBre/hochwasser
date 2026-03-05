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

export type JobFormField =
  | 'name'
  | 'station_uuid'
  | 'limit_cm'
  | 'recipients'
  | 'alert_recipient'
  | 'locale'
  | 'schedule_cron'

export type JobFormErrors = Partial<Record<JobFormField | 'form', string>>

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

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const cronFieldPattern = /^[\d*/,-]+$/

const isValidCron = (expression: string): boolean => {
  const trimmed = expression.trim()
  const fields = trimmed.split(/\s+/)

  return fields.length === 5 && fields.every((field) => cronFieldPattern.test(field))
}

const isValidEmail = (email: string): boolean => emailPattern.test(email)

export const validateJobForm = (state: JobFormState): JobFormErrors => {
  const errors: JobFormErrors = {}
  const name = state.name.trim()
  const stationUuid = state.station_uuid.trim()
  const alertRecipient = state.alert_recipient.trim()
  const scheduleCron = state.schedule_cron.trim()
  const recipients = parseRecipients(state.recipients)
  const invalidRecipient = recipients.find((email) => !isValidEmail(email))

  if (!name) {
    errors.name = 'Name is required.'
  } else if (name.length > 120) {
    errors.name = 'Name must be 120 characters or fewer.'
  }

  if (!stationUuid) {
    errors.station_uuid = 'Station UUID is required.'
  } else if (stationUuid.length > 120) {
    errors.station_uuid = 'Station UUID must be 120 characters or fewer.'
  }

  if (!alertRecipient) {
    errors.alert_recipient = 'Alert recipient is required.'
  } else if (alertRecipient.length > 254) {
    errors.alert_recipient = 'Alert recipient must be 254 characters or fewer.'
  } else if (!isValidEmail(alertRecipient)) {
    errors.alert_recipient = 'Alert recipient must be a valid email address.'
  }

  if (recipients.length < 1) {
    errors.recipients = 'At least one recipient is required.'
  } else if (recipients.length > 25) {
    errors.recipients = 'You can provide at most 25 recipients.'
  } else if (invalidRecipient) {
    errors.recipients = `Invalid recipient address: ${invalidRecipient}`
  }

  if (!['de', 'en'].includes(state.locale)) {
    errors.locale = 'Locale must be either German or English.'
  }

  if (!scheduleCron) {
    errors.schedule_cron = 'Schedule is required.'
  } else if (!isValidCron(scheduleCron)) {
    errors.schedule_cron = 'Schedule must be a valid 5-field crontab expression.'
  }

  const limitCm = Number(state.limit_cm)
  if (Number.isNaN(limitCm) || limitCm <= -10000 || limitCm >= 100000) {
    errors.limit_cm = 'Limit must be between -10000 and 100000.'
  }

  return errors
}

export const hasJobFormErrors = (errors: JobFormErrors): boolean => Object.keys(errors).length > 0

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
