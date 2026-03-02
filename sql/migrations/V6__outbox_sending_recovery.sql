ALTER TABLE public.email_outbox
ADD COLUMN IF NOT EXISTS sending_started_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_email_outbox_sending
  ON public.email_outbox (status, sending_started_at);
