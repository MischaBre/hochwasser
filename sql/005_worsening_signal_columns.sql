ALTER TABLE public.alert_job_runtime_state
ADD COLUMN IF NOT EXISTS predicted_peak_cm DOUBLE PRECISION;

ALTER TABLE public.alert_job_runtime_state
ADD COLUMN IF NOT EXISTS predicted_peak_at TIMESTAMPTZ;

ALTER TABLE public.alert_job_runtime_state
ADD COLUMN IF NOT EXISTS last_notified_predicted_crossing_at TIMESTAMPTZ;

ALTER TABLE public.alert_job_runtime_state
ADD COLUMN IF NOT EXISTS last_notified_predicted_end_at TIMESTAMPTZ;

ALTER TABLE public.alert_job_runtime_state
ADD COLUMN IF NOT EXISTS last_notified_peak_cm DOUBLE PRECISION;

ALTER TABLE public.alert_job_runtime_state
ADD COLUMN IF NOT EXISTS last_notified_peak_at TIMESTAMPTZ;

ALTER TABLE public.email_outbox
ADD COLUMN IF NOT EXISTS trigger_reason TEXT NOT NULL DEFAULT 'transition';

ALTER TABLE public.email_outbox
ADD COLUMN IF NOT EXISTS predicted_crossing_at TIMESTAMPTZ;

ALTER TABLE public.email_outbox
ADD COLUMN IF NOT EXISTS predicted_end_at TIMESTAMPTZ;

ALTER TABLE public.email_outbox
ADD COLUMN IF NOT EXISTS predicted_peak_cm DOUBLE PRECISION;

ALTER TABLE public.email_outbox
ADD COLUMN IF NOT EXISTS predicted_peak_at TIMESTAMPTZ;
