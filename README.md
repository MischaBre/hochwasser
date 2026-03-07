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
- Notification emails are rendered from Jinja templates in `templates/email/`
- Built-in health endpoint at `/health` (default port `8090`)
- API container (`hochwasser-api`) with Supabase JWT auth and job CRUD
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
   - `COMPOSE_PROFILES=dev`: starts local Postgres and frontend dev server, no watchdog
   - `COMPOSE_PROFILES=prod`: starts watchdog with external DB (base compose)
   - Public VM stack uses base + prod override: `docker-compose.yml` + `docker-compose.prod.yml`
4. Flyway (`hochwasser-flyway`) applies SQL migrations from `sql/migrations` before the alert service starts.
5. Frontend (`hochwasser-frontend`) starts in the `dev` profile on `http://localhost:5173`.
6. Insert at least one row into `public.alert_jobs`.
7. Edit non-secret values in `docker-compose.yml`:
   - `FORECAST_SERIES_SHORTNAME`
   - SMTP settings wiring
8. Follow logs:

```bash
docker compose logs -f
```

## Run Tests

```bash
uv venv
uv sync --dev --all-extras
uv run pytest
```

Or use Make targets:

```bash
make test
make check
make test-api-integration
```

`test-api-integration` runs API authorization tests marked `integration`.
It needs DB connectivity and uses one of:

- `API_TEST_DATABASE_URL`
- `API_DATABASE_URL`
- `DATABASE_URL`

Dependencies are managed with `uv` and locked in `uv.lock`.
Runtime extras are split into `alert` and `api`; local development and CI sync both via `--all-extras`.

## Linting And Formatting

Run Ruff locally:

```bash
uv run ruff check .
uv run ruff format .
```

Install pre-commit hooks:

```bash
uv sync --dev --all-extras
uv run pre-commit install
```

Ruff checks and pytest are enforced in GitHub Actions for pull requests into `main` and pushes to `main`.

## Production Readiness Checks

Use the Makefile to run repeatable production readiness checks:

```bash
make prod-ready
```

This runs linting, format checks, tests, gettext catalog freshness checks, and docker compose config validation.

## Configuration

Most values are set in `docker-compose.yml`; SMTP settings are read from `.env`.

For public VM deployment with TLS and host routing, see `.env.prod.example` and run with both compose files.

- `PROVIDER`: currently only `pegelonline`
- `COMPOSE_PROFILES`: use `dev` for local Postgres (no watchdog) or `prod` for watchdog with external DB
- `DATABASE_URL`: Postgres connection string used by `hochwasser-alert` engine
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
- `HEALTH_HOST`: bind host for health endpoint (default `0.0.0.0`)
- `HEALTH_PORT`: health endpoint port (default `8090`)
- `HEALTH_FAILURE_THRESHOLD`: consecutive failed cycles before `/health` returns unhealthy (default `3`)

API settings:

- `API_DATABASE_URL`: Postgres connection string used by `hochwasser-api` (use a separate DB user)
- `SUPABASE_JWKS_URL`: Supabase JWKS URL (`.../auth/v1/.well-known/jwks.json`)
- `SUPABASE_ISSUER`: Supabase issuer (`.../auth/v1`)
- `SUPABASE_AUDIENCE`: JWT audience expected by API (default `authenticated`)
- `API_DEFAULT_ORG_ID`: single-org UUID used to scope all API operations
- `API_INITIAL_ADMIN_USER_ID`: optional Supabase user UUID auto-assigned as admin on first request
- `API_AUTO_PROVISION_MEMBERS`: auto-insert unknown authenticated users as org members (`true`/`false`)
- `API_CORS_ALLOW_ORIGINS`: comma-separated allowed origins for browser calls (for local frontend use `http://localhost:5173`)

Frontend settings:

- `VITE_API_BASE_URL`: API base URL consumed by Vite frontend (`http://localhost:8080` for local compose)
- `VITE_SUPABASE_URL`: Supabase project URL
- `VITE_SUPABASE_PUBLISHABLE_KEY`: Supabase publishable key used by browser auth

Public runtime settings:

- `PUBLIC_APP_DOMAIN`: public frontend domain for Caddy routing (for example `app.example.com`)
- `PUBLIC_APP_WWW_DOMAIN`: www alias redirected to `PUBLIC_APP_DOMAIN` (for example `www.example.com`)
- `PUBLIC_API_DOMAIN`: public API domain for Caddy routing (for example `api.example.com`)

## Frontend (Local)

The frontend app lives in `frontend/` and is included in `docker-compose` via the `hochwasser-frontend` service.

With `COMPOSE_PROFILES=dev`, start everything with:

```bash
docker compose up -d --build
```

Then open:

- Frontend: `http://localhost:5173`
- API: `http://localhost:8080`

## Public VM Deployment (HTTPS)

Use this mode when deploying the app publicly on a VM.

What this starts:

- `hochwasser-alert`
- `hochwasser-api`
- `hochwasser-frontend-prod` (static built frontend)
- `caddy` (TLS + reverse proxy)
- `container-watchdog`

What this does not start:

- local `postgres` (use external DB, recommended Supabase)
- frontend Vite dev server

1. Copy production env template and fill real values:

```bash
cp .env.prod.example .env
```

2. Set required domains and CORS:

- `PUBLIC_APP_DOMAIN`, `PUBLIC_APP_WWW_DOMAIN`, `PUBLIC_API_DOMAIN`
- `API_CORS_ALLOW_ORIGINS=https://<PUBLIC_APP_DOMAIN>`

3. Start the public stack:

```bash
COMPOSE_PROFILES=prod docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Or use the deployment helper (validates required env vars and runs smoke checks):

```bash
make deploy-public
```

4. Smoke checks:

```bash
curl -fsS "https://<PUBLIC_API_DOMAIN>/health/live"
curl -fsS "https://<PUBLIC_API_DOMAIN>/health/ready"
curl -fsS "https://<PUBLIC_APP_DOMAIN>"
```

5. Follow logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f caddy hochwasser-api hochwasser-alert
```

Alternative smoke checks via Make target:

```bash
make smoke-public
```

Notes:

- Caddy automatically provisions and renews Let's Encrypt certificates for valid public domains.
- Expose only ports `80` and `443` publicly on the VM.
- Keep secrets in VM `.env` only; never commit real credentials.
- In public mode, frontend and Caddy run with dropped Linux capabilities and read-only filesystems.

If you run frontend outside Docker, use:

```bash
cd frontend
npm install
npm run dev
```

Environment source of truth:

- Compose workflow (`docker compose ...`) reads `VITE_*` values from root `.env`.
- Standalone frontend workflow (`npm --prefix frontend run dev`) reads `frontend/.env`.

### Database Roles And Grants

Phase 1 introduces role-based DB grants in `sql/migrations/V8__rbac_grants.sql`:

- `engine_role`: read jobs/org tables, write runtime/outbox tables
- `api_role`: write jobs/org tables, read runtime/outbox tables
- `readonly_role`: read-only access to all application tables

The migration is safe if roles do not exist yet. It only applies grants for roles that are present.

To bootstrap local roles/users, use `sql/bootstrap/create_app_roles.sql` and then point:

- `DATABASE_URL` at `engine_user`
- `API_DATABASE_URL` at `api_user`

Verify role boundaries after bootstrap and migration:

```bash
make db-rbac-verify
```

Expected checks:

- engine can read jobs and write runtime/outbox
- engine cannot update jobs
- api can read/update jobs
- api cannot update runtime/outbox

## API Endpoints

`hochwasser-api` exposes port `8080` and provides:

- `GET /health/live`
- `GET /health/ready`
- `GET /v1/me`
- `GET /v1/jobs`
- `POST /v1/jobs`
- `PATCH /v1/jobs/{job_uuid}`
- `DELETE /v1/jobs/{job_uuid}` (soft delete: sets `enabled=false`)
- `GET /v1/jobs/{job_uuid}/status`
- `GET /v1/jobs/{job_uuid}/outbox`
- `GET /v1/admin/members` (admin only)
- `POST /v1/admin/members/{user_id}/promote` (admin only)
- `POST /v1/admin/members/{user_id}/demote` (admin only)
- `GET /v1/admin/audit/jobs` (admin only)
- `GET /v1/admin/audit/memberships` (admin only)

Audit logging:

- Job mutations are written to `public.job_audit_log`
- Membership role changes are written to `public.membership_audit_log`

Email templates:

- Alert templates live in `templates/email/alert_*.j2`
- State update templates live in `templates/email/state_update_*.j2`
- Templates use Jinja's i18n extension with translation keys (for example `{{ _('label_station_uuid') }}`)
- GNU gettext catalogs are in `locales/<lang>/LC_MESSAGES/emails.po` and compiled to `emails.mo`
- Recompile catalogs after edits with `msgfmt -o locales/<lang>/LC_MESSAGES/emails.mo locales/<lang>/LC_MESSAGES/emails.po`

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

If your database was initialized before Flyway integration and does not have migration tracking yet, bootstrap migration tracking and then run Flyway against `sql/migrations`.

For host-side migration into the local dev database, use:

```bash
python scripts/migrate_files_to_db.py --database-url "postgresql://hochwasser:hochwasser@localhost:5432/hochwasser"
```

## Job-Down Alerts

- If a job reaches the configured failure threshold, the service sends one "job down" email when it transitions to degraded.
- Recipients for this email are that job's `alert_recipient` only.

## Deduplication Key

- Alerts use per-job state transitions (`crossing_incoming`, `crossing_active`, `crossing_soon_over`, `no_crossing`).
- Notification is queued on state transition and delivered by an outbox dispatcher loop.
- If `repeat_alerts_on_check` is enabled for a job, repeated alerts are sent for `crossing_active` on each check.
