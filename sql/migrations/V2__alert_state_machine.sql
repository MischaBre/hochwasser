ALTER TABLE public.alert_jobs
ADD COLUMN IF NOT EXISTS repeat_alerts_on_check BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS public.alert_job_runtime_state (
  job_uuid TEXT PRIMARY KEY REFERENCES public.alert_jobs (job_uuid) ON DELETE CASCADE,
  state TEXT NOT NULL,
  state_since TIMESTAMPTZ NOT NULL,
  predicted_crossing_at TIMESTAMPTZ,
  predicted_end_at TIMESTAMPTZ,
  last_notified_state TEXT,
  last_notified_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alert_runtime_state_state
  ON public.alert_job_runtime_state (state);
