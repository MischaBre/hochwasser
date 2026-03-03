# Hochwasser Alert Service (Raspberry Pi + Docker Compose)

This service monitors one or more Pegelonline stations and sends email alerts when a
configured water level limit is expected to be reached.

It checks:
- current water level (`currentmeasurement`)
- official forecast (`<FORECAST_SERIES_SHORTNAME>/measurements`)

## Features

- Supports multiple alert jobs via Supabase/Postgres table `alert_jobs`
- Alert deduplication (no repeated mail spam for the same predicted event)
- Persistent runtime alert state in Supabase/Postgres table `alert_job_runtime_state`
- Durable email outbox in `email_outbox` with retry/backoff delivery
- Runs one APScheduler cron job per alert job
- Alert email includes detailed station metadata and a forecast table
- Built-in health endpoint at `/health` (default port `8090`)
- Docker healthcheck on the alert container
- Watchdog container that alerts on container `die` / `unhealthy` events
- Optional auto-restart of unhealthy containers via watchdog
- Alert container runs as non-root with read-only filesystem defaults

## Quick Start

1. Copy `.env.template` to `.env` and set SMTP values plus `DATABASE_URL`.
2. Start services:
```bash
docker compose up -d --build
```
3. Profiles:
   - `COMPOSE_PROFILES=dev`: starts local Postgres, no watchdog
   - `COMPOSE_PROFILES=prod`: starts watchdog, no local Postgres
4. Flyway (`hochwasser-flyway`) applies SQL migrations from `sql/migrations` before the alert service starts.
5. Insert at least one row into `public.alert_jobs`.
6. Edit non-secret values in `docker-compose.yml`:
   - `FORECAST_SERIES_SHORTNAME`
   - SMTP settings wiring
7. Follow logs:

```bash
docker compose logs -f
```

## Run Tests

```bash
uv venv
uv sync --dev
uv run pytest
```

If you prefer plain `venv` + `pip`, the existing commands from `requirements.txt` still work.

## Linting And Formatting

Run Ruff locally:

```bash
uv run ruff check .
uv run ruff format .
```

Install pre-commit hooks:

```bash
uv sync --dev
uv run pre-commit install
```

Ruff checks and pytest are enforced in GitHub Actions for pull requests into `main` and pushes to `main`.

## Configuration

Most values are set in `docker-compose.yml`; SMTP settings are read from `.env`.

- `PROVIDER`: currently only `pegelonline`
- `COMPOSE_PROFILES`: use `dev` for local Postgres (no watchdog) or `prod` for watchdog with external DB
- `DATABASE_URL`: Postgres connection string (local dev default points to `postgres` service)
- `FLYWAY_URL`: JDBC connection string for Flyway
- `FLYWAY_USER`, `FLYWAY_PASSWORD`: DB credentials for Flyway
- Each job supports: `job_uuid`, `name`, `station_uuid`, `limit_cm`, `recipients`, `alert_recipient`, `locale` (`de` or `en`), `schedule_cron`, `repeat_alerts_on_check` (bool, default `false`)
- `job_uuid` must be unique and stable across job reconfiguration
- `FORECAST_SERIES_SHORTNAME`: forecast timeseries shortname (default `WV`)
- Forecast horizon is derived automatically from station metadata (`includeForecastTimeseries=true`, `WV.start`/`WV.end`)
- `ALERT_DEDUPE_HOURS`: minimum hours before same predicted alert can repeat
- `LOG_LEVEL`: log level for alert service/watchdog (default `INFO`)
- `TZ`: timezone for logs and mail timestamps
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_SENDER`: From address
- `SMTP_USE_STARTTLS`: `true`/`false`
- `SMTP_USE_SSL`: `true`/`false`
- `ALERT_RECIPIENTS`: admin recipients for job-down health alerts
- `HEALTH_HOST`: bind host for health endpoint (default `0.0.0.0`)
- `HEALTH_PORT`: health endpoint port (default `8090`)
- `HEALTH_FAILURE_THRESHOLD`: consecutive failed cycles before `/health` returns unhealthy (default `3`)

Watchdog settings (from `docker-compose.yml` / `.env`):

- `WATCHDOG_WATCH_CONTAINERS`: comma-separated container names to watch
- `WATCHDOG_COOLDOWN_SECONDS`: suppress duplicate alerts for the same container/event
- `WATCHDOG_AUTO_RESTART_UNHEALTHY`: restart unhealthy containers automatically
- `WATCHDOG_ALERT_RECIPIENTS`: optional override for watchdog emails

Watchdog security note:

- `container-watchdog` mounts `/var/run/docker.sock` and therefore has host-level control over Docker.
- Keep it in the `prod` profile only, and run only on trusted hosts.

## Finding a Station UUID

Query station list and search by name:

```bash
curl -s "https://pegelonline.wsv.de/webservices/rest-api/v2/stations.json?includeTimeseries=true"

```

Then copy the station `uuid` and set it in each job's `station_uuid` field.

## Notes About Forecasts

This service first tries forecast measurements from the configured series, for example:

`https://pegelonline.wsv.de/webservices/rest-api/v2/stations/<STATION_UUID>/WV/measurements.json`

An alert is sent if either the current measurement at call time or a forecast value
within the dynamically derived horizon is above the configured threshold.

If the station does not expose forecast timeseries metadata for the configured
forecast shortname (for example `WV` is missing), the service evaluates only the
current measurement.

## Raspberry Pi Notes

- Use a 64-bit Raspberry Pi OS if possible.
- Keep `restart: unless-stopped` enabled so service comes back after reboot.
- If SMTP provider requires app passwords, use that password in `SMTP_PASSWORD`.
- Expose `8090/tcp` if you want to query `/health` from other devices.

## Tailscale Health Check

When Tailscale is installed on the Pi, you can check health from another Tailscale node:

```bash
curl -fsS "http://<pi-tailscale-ip>:8090/health"
```

Expected behavior:

- `200` with JSON `status: ok` when healthy
- `503` with JSON `status: degraded` while repeated monitoring failures happen

## Scheduling Model

- Main manager loop runs every minute, reloads config, and reconciles APScheduler jobs.
- Each job is scheduled independently with its own `schedule_cron` (5-field crontab) trigger.

## Migrating Existing Local Files

If you already have `data/jobs.json` and `data/state.json`, migrate them once:

```bash
python scripts/migrate_files_to_db.py --database-url "$DATABASE_URL"
```

If your database was initialized before Flyway integration and does not have migration tracking yet, bootstrap once:

```bash
psql "$DATABASE_URL" -f sql/002_alert_state_machine.sql
psql "$DATABASE_URL" -f sql/003_smtp_pending_notifications.sql
psql "$DATABASE_URL" -f sql/004_email_outbox.sql
psql "$DATABASE_URL" -f sql/005_worsening_signal_columns.sql
psql "$DATABASE_URL" -f sql/006_outbox_sending_recovery.sql
```

For host-side migration into the local dev database, use:

```bash
python scripts/migrate_files_to_db.py --database-url "postgresql://hochwasser:hochwasser@localhost:5432/hochwasser"
```

## Job-Down Alerts

- If a job reaches the configured failure threshold, the service sends one "job down" email when it transitions to degraded.
- Recipients for this email are `ALERT_RECIPIENTS` (admin list) plus that job's `alert_recipient`.

## Deduplication Key

- Alerts use per-job state transitions (`crossing_incoming`, `crossing_active`, `crossing_soon_over`, `no_crossing`).
- Notification is queued on state transition and delivered by an outbox dispatcher loop.
- If `repeat_alerts_on_check` is enabled for a job, repeated alerts are sent for `crossing_active` on each check.
