# Hochwasser Alert Service (Raspberry Pi + Docker Compose)

This service monitors one or more Pegelonline stations and sends email alerts when a
configured water level limit is expected to be reached.

It checks:
- current water level (`currentmeasurement`)
- official forecast (`<FORECAST_SERIES_SHORTNAME>/measurements`)

## Features

- Supports multiple alert jobs via `JOBS_FILE` JSON config
- Alert deduplication (no repeated mail spam for the same predicted event)
- Persistent state in `./data/state.json`
- Runs one APScheduler cron job per alert job
- Alert email includes detailed station metadata and a forecast table
- Built-in health endpoint at `/health` (default port `8090`)
- Docker healthcheck on the alert container
- Watchdog container that alerts on container `die` / `unhealthy` events
- Optional auto-restart of unhealthy containers via watchdog

## Quick Start

1. Copy `.env.template` to `.env` and set SMTP values.
2. Copy `jobs.example.json` to your configured jobs path (default `/data/jobs.json`) and edit jobs.
3. Edit non-secret values in `docker-compose.yml`:
   - `FORECAST_SERIES_SHORTNAME`
   - SMTP settings wiring
4. Start service:
```bash
docker compose up -d --build
```

5. Follow logs:

```bash
docker compose logs -f
```

## Run Tests

```bash
python -m pip install -r requirements.txt
pytest
```

## Configuration

Most values are set in `docker-compose.yml`; SMTP settings are read from `.env`.

- `PROVIDER`: currently only `pegelonline`
- `JOBS_FILE`: path to JSON with alert jobs (default `/data/jobs.json`)
- Each job supports: `job_uuid`, `name`, `station_uuid`, `limit_cm`, `recipients`, `alert_recipient`, `locale` (`de` or `en`), `schedule_cron`
- `job_uuid` must be unique and stable across job reconfiguration
- `FORECAST_SERIES_SHORTNAME`: forecast timeseries shortname (default `WV`)
- Forecast horizon is derived automatically from station metadata (`includeForecastTimeseries=true`, `WV.start`/`WV.end`)
- `ALERT_DEDUPE_HOURS`: minimum hours before same predicted alert can repeat
- `LOG_LEVEL`: `DEBUG` for verbose fetch + measurement logs (default `DEBUG`)
- `TZ`: timezone for logs and mail timestamps
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_SENDER`: From address
- `SMTP_USE_STARTTLS`: `true`/`false`
- `SMTP_USE_SSL`: `true`/`false`
- `ALERT_RECIPIENTS`: admin recipients for job-down health alerts
- `STATE_FILE`: path to persistence file (default `/data/state.json`)
- `HEALTH_HOST`: bind host for health endpoint (default `0.0.0.0`)
- `HEALTH_PORT`: health endpoint port (default `8090`)
- `HEALTH_FAILURE_THRESHOLD`: consecutive failed cycles before `/health` returns unhealthy (default `3`)

Watchdog settings (from `docker-compose.yml` / `.env`):

- `WATCHDOG_WATCH_CONTAINERS`: comma-separated container names to watch
- `WATCHDOG_COOLDOWN_SECONDS`: suppress duplicate alerts for the same container/event
- `WATCHDOG_AUTO_RESTART_UNHEALTHY`: restart unhealthy containers automatically
- `WATCHDOG_ALERT_RECIPIENTS`: optional override for watchdog emails

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

## Job-Down Alerts

- If a job reaches the configured failure threshold, the service sends one "job down" email when it transitions to degraded.
- Recipients for this email are `ALERT_RECIPIENTS` (admin list) plus that job's `alert_recipient`.

## Deduplication Key

- Deduplication key format is `<job_uuid>|<sha256(...)>`.
- Hash input is `crossing_timestamp` and sorted `alert_recipients` (stringified and hashed).
- On job update, existing dedupe keys for that `job_uuid` are invalidated.
