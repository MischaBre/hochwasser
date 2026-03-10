DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api_role') THEN
    EXECUTE 'GRANT DELETE ON TABLE public.job_audit_log TO api_role';
    EXECUTE 'GRANT DELETE ON TABLE public.membership_audit_log TO api_role';
    EXECUTE 'GRANT DELETE ON TABLE public.alert_jobs TO api_role';
    EXECUTE 'GRANT DELETE ON TABLE public.organization_members TO api_role';
  END IF;
END $$;
