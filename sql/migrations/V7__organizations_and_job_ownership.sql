CREATE TABLE IF NOT EXISTS public.organizations (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.organization_members (
  org_id UUID NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (org_id, user_id)
);

INSERT INTO public.organizations (id, name)
VALUES ('11111111-1111-1111-1111-111111111111', 'default')
ON CONFLICT (id) DO NOTHING;

ALTER TABLE public.alert_jobs
ADD COLUMN IF NOT EXISTS org_id UUID;

ALTER TABLE public.alert_jobs
ADD COLUMN IF NOT EXISTS created_by UUID;

ALTER TABLE public.alert_jobs
ADD COLUMN IF NOT EXISTS updated_by UUID;

ALTER TABLE public.alert_jobs
ADD COLUMN IF NOT EXISTS disabled_at TIMESTAMPTZ;

UPDATE public.alert_jobs
SET org_id = '11111111-1111-1111-1111-111111111111'
WHERE org_id IS NULL;

UPDATE public.alert_jobs
SET created_by = '00000000-0000-0000-0000-000000000000'
WHERE created_by IS NULL;

UPDATE public.alert_jobs
SET updated_by = '00000000-0000-0000-0000-000000000000'
WHERE updated_by IS NULL;

ALTER TABLE public.alert_jobs
ALTER COLUMN org_id SET DEFAULT '11111111-1111-1111-1111-111111111111';

ALTER TABLE public.alert_jobs
ALTER COLUMN created_by SET DEFAULT '00000000-0000-0000-0000-000000000000';

ALTER TABLE public.alert_jobs
ALTER COLUMN updated_by SET DEFAULT '00000000-0000-0000-0000-000000000000';

ALTER TABLE public.alert_jobs
ALTER COLUMN org_id SET NOT NULL;

ALTER TABLE public.alert_jobs
ALTER COLUMN created_by SET NOT NULL;

ALTER TABLE public.alert_jobs
ALTER COLUMN updated_by SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'alert_jobs_org_id_fkey'
  ) THEN
    ALTER TABLE public.alert_jobs
    ADD CONSTRAINT alert_jobs_org_id_fkey
    FOREIGN KEY (org_id) REFERENCES public.organizations (id) ON DELETE RESTRICT;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_alert_jobs_org_id
  ON public.alert_jobs (org_id);

CREATE INDEX IF NOT EXISTS idx_alert_jobs_org_enabled
  ON public.alert_jobs (org_id, enabled);

CREATE INDEX IF NOT EXISTS idx_alert_jobs_created_by
  ON public.alert_jobs (created_by);

CREATE INDEX IF NOT EXISTS idx_organization_members_user
  ON public.organization_members (user_id);
