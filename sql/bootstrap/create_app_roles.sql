-- Run this manually as a privileged database user.
-- Replace the passwords before executing.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'engine_role') THEN
    CREATE ROLE engine_role NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api_role') THEN
    CREATE ROLE api_role NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'readonly_role') THEN
    CREATE ROLE readonly_role NOLOGIN;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'engine_user') THEN
    CREATE ROLE engine_user LOGIN PASSWORD 'CHANGE_ME_ENGINE_PASSWORD';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'api_user') THEN
    CREATE ROLE api_user LOGIN PASSWORD 'CHANGE_ME_API_PASSWORD';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'readonly_user') THEN
    CREATE ROLE readonly_user LOGIN PASSWORD 'CHANGE_ME_READONLY_PASSWORD';
  END IF;
END $$;

GRANT engine_role TO engine_user;
GRANT api_role TO api_user;
GRANT readonly_role TO readonly_user;
