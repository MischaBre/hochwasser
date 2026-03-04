CREATE TABLE IF NOT EXISTS public.job_audit_log (
  id BIGSERIAL PRIMARY KEY,
  org_id UUID NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  job_uuid TEXT NOT NULL REFERENCES public.alert_jobs (job_uuid) ON DELETE CASCADE,
  actor_user_id UUID NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('created', 'updated', 'soft_deleted')),
  changed_fields TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_job_audit_log_org_created
  ON public.job_audit_log (org_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_job_audit_log_job_created
  ON public.job_audit_log (job_uuid, created_at DESC);

CREATE TABLE IF NOT EXISTS public.membership_audit_log (
  id BIGSERIAL PRIMARY KEY,
  org_id UUID NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  actor_user_id UUID NOT NULL,
  target_user_id UUID NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('promoted_to_admin', 'demoted_to_member')),
  old_role TEXT NOT NULL CHECK (old_role IN ('admin', 'member')),
  new_role TEXT NOT NULL CHECK (new_role IN ('admin', 'member')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_membership_audit_log_org_created
  ON public.membership_audit_log (org_id, created_at DESC);

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api_role') THEN
    EXECUTE 'GRANT SELECT, INSERT ON TABLE public.job_audit_log TO api_role';
    EXECUTE 'GRANT USAGE, SELECT ON SEQUENCE public.job_audit_log_id_seq TO api_role';
    EXECUTE 'GRANT SELECT, INSERT ON TABLE public.membership_audit_log TO api_role';
    EXECUTE 'GRANT USAGE, SELECT ON SEQUENCE public.membership_audit_log_id_seq TO api_role';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'readonly_role') THEN
    EXECUTE 'GRANT SELECT ON TABLE public.job_audit_log TO readonly_role';
    EXECUTE 'GRANT SELECT ON TABLE public.membership_audit_log TO readonly_role';
  END IF;
END $$;

REVOKE ALL ON TABLE public.job_audit_log FROM PUBLIC;
REVOKE ALL ON TABLE public.membership_audit_log FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.job_audit_log_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.membership_audit_log_id_seq FROM PUBLIC;
