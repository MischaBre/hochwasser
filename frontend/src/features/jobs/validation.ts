import type { JobCreatePayload } from '@/features/jobs/types'
import { i18n } from '@/plugins/i18n'

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
    errors.name = i18n.global.t('validation.nameRequired')
  } else if (name.length > 120) {
    errors.name = i18n.global.t('validation.nameTooLong')
  }

  if (!stationUuid) {
    errors.station_uuid = i18n.global.t('validation.stationUuidRequired')
  } else if (stationUuid.length > 120) {
    errors.station_uuid = i18n.global.t('validation.stationUuidTooLong')
  }

  if (!alertRecipient) {
    errors.alert_recipient = i18n.global.t('validation.alertRecipientRequired')
  } else if (alertRecipient.length > 254) {
    errors.alert_recipient = i18n.global.t('validation.alertRecipientTooLong')
  } else if (!isValidEmail(alertRecipient)) {
    errors.alert_recipient = i18n.global.t('validation.alertRecipientInvalid')
  }

  if (recipients.length < 1) {
    errors.recipients = i18n.global.t('validation.recipientsRequired')
  } else if (recipients.length > 25) {
    errors.recipients = i18n.global.t('validation.recipientsTooMany')
  } else if (invalidRecipient) {
    errors.recipients = i18n.global.t('validation.recipientsInvalidAddress', { email: invalidRecipient })
  }

  if (!['de', 'en'].includes(state.locale)) {
    errors.locale = i18n.global.t('validation.localeUnsupported')
  }

  if (!scheduleCron) {
    errors.schedule_cron = i18n.global.t('validation.scheduleRequired')
  } else if (!isValidCron(scheduleCron)) {
    errors.schedule_cron = i18n.global.t('validation.scheduleInvalid')
  }

  const limitRaw = state.limit_cm.trim()
  if (!limitRaw) {
    errors.limit_cm = i18n.global.t('validation.limitRequired')
    return errors
  }

  if (!/^\d+$/.test(limitRaw)) {
    errors.limit_cm = i18n.global.t('validation.limitWholeNumber')
    return errors
  }

  const limitCm = Number(limitRaw)
  if (limitCm < 0 || limitCm >= 100000) {
    errors.limit_cm = i18n.global.t('validation.limitRange')
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
