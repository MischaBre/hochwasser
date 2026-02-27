CREATE TABLE IF NOT EXISTS public.locales (
  code TEXT PRIMARY KEY
);

INSERT INTO public.locales (code)
VALUES ('de'), ('en')
ON CONFLICT (code) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.alert_jobs (
  job_uuid TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  station_uuid TEXT NOT NULL,
  limit_cm DOUBLE PRECISION NOT NULL,
  recipients TEXT[] NOT NULL CHECK (cardinality(recipients) > 0),
  alert_recipient TEXT NOT NULL,
  locale TEXT NOT NULL REFERENCES public.locales (code),
  schedule_cron TEXT NOT NULL,
  repeat_alerts_on_check BOOLEAN NOT NULL DEFAULT FALSE,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.alert_job_runtime_state (
  job_uuid TEXT PRIMARY KEY REFERENCES public.alert_jobs (job_uuid) ON DELETE CASCADE,
  state TEXT NOT NULL,
  state_since TIMESTAMPTZ NOT NULL,
  predicted_crossing_at TIMESTAMPTZ,
  predicted_end_at TIMESTAMPTZ,
  predicted_peak_cm DOUBLE PRECISION,
  predicted_peak_at TIMESTAMPTZ,
  last_notified_state TEXT,
  last_notified_at TIMESTAMPTZ,
  last_notified_predicted_crossing_at TIMESTAMPTZ,
  last_notified_predicted_end_at TIMESTAMPTZ,
  last_notified_peak_cm DOUBLE PRECISION,
  last_notified_peak_at TIMESTAMPTZ,
  pending_notification_state TEXT,
  pending_notification_since TIMESTAMPTZ,
  pending_notification_error TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.email_outbox (
  id BIGSERIAL PRIMARY KEY,
  job_uuid TEXT NOT NULL REFERENCES public.alert_jobs (job_uuid) ON DELETE CASCADE,
  target_state TEXT NOT NULL,
  trigger_reason TEXT NOT NULL,
  state_since TIMESTAMPTZ NOT NULL,
  predicted_crossing_at TIMESTAMPTZ,
  predicted_end_at TIMESTAMPTZ,
  predicted_peak_cm DOUBLE PRECISION,
  predicted_peak_at TIMESTAMPTZ,
  recipients TEXT[] NOT NULL CHECK (cardinality(recipients) > 0),
  subject TEXT NOT NULL,
  body_text TEXT NOT NULL,
  body_html TEXT,
  status TEXT NOT NULL,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TIMESTAMPTZ NOT NULL,
  sent_at TIMESTAMPTZ,
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alert_jobs_enabled
  ON public.alert_jobs (enabled);

CREATE INDEX IF NOT EXISTS idx_alert_runtime_state_state
  ON public.alert_job_runtime_state (state);

CREATE INDEX IF NOT EXISTS idx_email_outbox_due
  ON public.email_outbox (status, next_attempt_at, created_at);
