CREATE TABLE IF NOT EXISTS public.email_outbox (
  id BIGSERIAL PRIMARY KEY,
  job_uuid TEXT NOT NULL REFERENCES public.alert_jobs (job_uuid) ON DELETE CASCADE,
  target_state TEXT NOT NULL,
  trigger_reason TEXT NOT NULL DEFAULT 'transition',
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

CREATE INDEX IF NOT EXISTS idx_email_outbox_due
  ON public.email_outbox (status, next_attempt_at, created_at);
