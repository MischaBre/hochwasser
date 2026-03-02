# SQL Migrations

This directory contains schema SQL for the alert service.

- `sql/migrations/` is the Flyway source of truth used at container startup.
- `001_supabase_schema.sql` and `002_alert_state_machine.sql` remain available for manual `psql` execution.

## Files

- `001_supabase_schema.sql`: baseline schema for a fresh database.
- `002_alert_state_machine.sql`: additive migration for existing databases that were created before the alert state-machine update.
- `003_smtp_pending_notifications.sql`: adds pending-notification columns for SMTP outage handling.
- `004_email_outbox.sql`: creates durable email outbox table and indexes.
- `005_worsening_signal_columns.sql`: adds worsening-signal columns for runtime/outbox notifications.
- `migrations/V1__supabase_schema.sql`: Flyway baseline migration.
- `migrations/V2__alert_state_machine.sql`: Flyway additive migration.
- `migrations/V3__smtp_pending_notifications.sql`: Flyway migration for pending notification columns.
- `migrations/V4__email_outbox.sql`: Flyway migration for durable outbox delivery.
- `migrations/V5__worsening_signal_columns.sql`: Flyway migration for worsening-signal notification fields.

## Startup Flow (Docker Compose)

`docker compose up` starts services in this order:

1. `postgres` (persistent volume, only when `COMPOSE_PROFILES=local-db`)
2. `flyway` (`migrate` command against `sql/migrations`)
3. `hochwasser-alert` (only after Flyway exits successfully)

Flyway keeps migration history in `flyway_schema_history`.

## Manual Setup (Optional)

For a new local or Supabase Postgres database without Docker startup orchestration, apply:

```bash
psql "$DATABASE_URL" -f sql/001_supabase_schema.sql
```

This creates:

- `public.locales`
- `public.alert_jobs` (including `repeat_alerts_on_check`)
- `public.alert_job_runtime_state`

## Upgrading An Existing Database

If your DB was initialized earlier and does not yet have the state-machine columns/table,
apply:

```bash
psql "$DATABASE_URL" -f sql/002_alert_state_machine.sql
```

`002_alert_state_machine.sql` is safe to run multiple times (`IF NOT EXISTS`).

## Data Migration From Local JSON Files

After schema is ready, optionally migrate your local files:

```bash
python scripts/migrate_files_to_db.py --database-url "$DATABASE_URL"
```

Notes:

- Jobs are upserted into `public.alert_jobs`.
- Legacy dedupe rows from `data/state.json` are only counted/reported and are not imported in the new state-machine model.
