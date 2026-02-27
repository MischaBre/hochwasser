ALTER TABLE public.alert_job_runtime_state
ADD COLUMN IF NOT EXISTS pending_notification_state TEXT;

ALTER TABLE public.alert_job_runtime_state
ADD COLUMN IF NOT EXISTS pending_notification_since TIMESTAMPTZ;

ALTER TABLE public.alert_job_runtime_state
ADD COLUMN IF NOT EXISTS pending_notification_error TEXT;
