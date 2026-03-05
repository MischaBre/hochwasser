export type Job = {
  job_uuid: string
  name: string
  station_uuid: string
  limit_cm: number
  recipients: string[]
  alert_recipient: string
  locale: 'de' | 'en'
  schedule_cron: string
  repeat_alerts_on_check: boolean
  enabled: boolean
  org_id: string
  created_by: string
  updated_by: string
  created_at: string
  updated_at: string
  disabled_at: string | null
}

export type JobCreatePayload = {
  name: string
  station_uuid: string
  limit_cm: number
  recipients: string[]
  alert_recipient: string
  locale: 'de' | 'en'
  schedule_cron: string
  repeat_alerts_on_check: boolean
}

export type JobUpdatePayload = Partial<JobCreatePayload> & {
  enabled?: boolean
}

export type JobStatus = {
  job_uuid: string
  state: string | null
  state_since: string | null
  predicted_crossing_at: string | null
  predicted_end_at: string | null
  predicted_peak_cm: number | null
  predicted_peak_at: string | null
  last_notified_state: string | null
  last_notified_at: string | null
  updated_at: string | null
}

export type OutboxEntry = {
  id: number
  target_state: string
  trigger_reason: string
  status: string
  attempt_count: number
  next_attempt_at: string
  sent_at: string | null
  last_error: string | null
  created_at: string
  updated_at: string
}

export type OutboxListResponse = {
  items: OutboxEntry[]
  limit: number
  offset: number
}
