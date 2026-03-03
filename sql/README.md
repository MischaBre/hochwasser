# SQL Migrations

This directory contains schema SQL for the alert service.

- `sql/migrations/` is the Flyway source of truth used at container startup.

## Files

- `migrations/V1__supabase_schema.sql`: Flyway baseline migration.
- `migrations/V2__alert_state_machine.sql`: Flyway additive migration.
- `migrations/V3__smtp_pending_notifications.sql`: Flyway migration for pending notification columns.
- `migrations/V4__email_outbox.sql`: Flyway migration for durable outbox delivery.
- `migrations/V5__worsening_signal_columns.sql`: Flyway migration for worsening-signal notification fields.
- `migrations/V6__outbox_sending_recovery.sql`: Flyway migration for reclaiming stale `sending` outbox rows.

## Startup Flow (Docker Compose)

`docker compose up` starts services in this order:

1. `postgres` (persistent volume, only when `COMPOSE_PROFILES=dev`)
2. `flyway` (`migrate` command against `sql/migrations`)
3. `hochwasser-alert` (only after Flyway exits successfully)

Flyway keeps migration history in `flyway_schema_history`.

## Manual Setup (Optional)

For a new local or Supabase Postgres database without Docker startup orchestration, run Flyway migrations from `sql/migrations`.

```bash
flyway \
  -url="$FLYWAY_URL" \
  -user="$FLYWAY_USER" \
  -password="$FLYWAY_PASSWORD" \
  -locations=filesystem:sql/migrations \
  migrate
```

This creates:

- `public.locales`
- `public.alert_jobs` (including `repeat_alerts_on_check`)
- `public.alert_job_runtime_state`

## Upgrading An Existing Database

For existing databases, keep using Flyway as the only migration path. If your database predates Flyway tracking, initialize `flyway_schema_history` once and then run the same `migrate` command above.

## Data Migration From Local JSON Files

After schema is ready, optionally migrate your local files:

```bash
python scripts/migrate_files_to_db.py --database-url "$DATABASE_URL"
```

Notes:

- Jobs are upserted into `public.alert_jobs`.
- Legacy dedupe rows from `data/state.json` are only counted/reported and are not imported in the new state-machine model.
