DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'engine_role') THEN
    EXECUTE 'GRANT USAGE ON SCHEMA public TO engine_role';
    EXECUTE 'GRANT SELECT ON TABLE public.alert_jobs TO engine_role';
    EXECUTE 'GRANT SELECT ON TABLE public.organizations TO engine_role';
    EXECUTE 'GRANT SELECT ON TABLE public.organization_members TO engine_role';
    EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.alert_job_runtime_state TO engine_role';
    EXECUTE 'GRANT SELECT, INSERT, UPDATE ON TABLE public.email_outbox TO engine_role';
    EXECUTE 'GRANT USAGE, SELECT ON SEQUENCE public.email_outbox_id_seq TO engine_role';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api_role') THEN
    EXECUTE 'GRANT USAGE ON SCHEMA public TO api_role';
    EXECUTE 'GRANT SELECT, INSERT, UPDATE ON TABLE public.alert_jobs TO api_role';
    EXECUTE 'GRANT SELECT, INSERT, UPDATE ON TABLE public.organizations TO api_role';
    EXECUTE 'GRANT SELECT, INSERT, UPDATE ON TABLE public.organization_members TO api_role';
    EXECUTE 'GRANT SELECT ON TABLE public.alert_job_runtime_state TO api_role';
    EXECUTE 'GRANT SELECT ON TABLE public.email_outbox TO api_role';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'readonly_role') THEN
    EXECUTE 'GRANT USAGE ON SCHEMA public TO readonly_role';
    EXECUTE 'GRANT SELECT ON TABLE public.alert_jobs TO readonly_role';
    EXECUTE 'GRANT SELECT ON TABLE public.organizations TO readonly_role';
    EXECUTE 'GRANT SELECT ON TABLE public.organization_members TO readonly_role';
    EXECUTE 'GRANT SELECT ON TABLE public.alert_job_runtime_state TO readonly_role';
    EXECUTE 'GRANT SELECT ON TABLE public.email_outbox TO readonly_role';
  END IF;
END $$;

REVOKE ALL ON TABLE public.alert_jobs FROM PUBLIC;
REVOKE ALL ON TABLE public.organizations FROM PUBLIC;
REVOKE ALL ON TABLE public.organization_members FROM PUBLIC;
REVOKE ALL ON TABLE public.alert_job_runtime_state FROM PUBLIC;
REVOKE ALL ON TABLE public.email_outbox FROM PUBLIC;
REVOKE ALL ON SEQUENCE public.email_outbox_id_seq FROM PUBLIC;
