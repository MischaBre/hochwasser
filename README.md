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
- Runs at fixed daily times (default: 00:00 and 12:00)
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
- Each job supports: `name`, `station_uuid`, `limit_cm`, `recipients`, `locale` (`de` or `en`)
- Legacy fallback if `JOBS_FILE` is missing: `STATION_UUID` + `LIMIT_CM` + `ALERT_RECIPIENTS`
- `FORECAST_SERIES_SHORTNAME`: forecast timeseries shortname (default `WV`)
- `DEBUG_RUN_EVERY_MINUTE`: set `true` for test mode (run every minute)
- `ALERT_RECIPIENTS`: comma-separated fallback recipients (if `JOBS_FILE` is missing)
- `FORECAST_RUN_HOURS`: comma-separated check hours in local time (default `0,12`)
- Forecast horizon is derived automatically from station metadata (`includeForecastTimeseries=true`, `WV.start`/`WV.end`)
- `ALERT_DEDUPE_HOURS`: minimum hours before same predicted alert can repeat
- `LOG_LEVEL`: `DEBUG` for verbose fetch + measurement logs (default `DEBUG`)
- `TZ`: timezone for logs and mail timestamps
- `EMAIL_LOCALE`: fallback localization (`de` or `en`, default `de`) used for legacy single-job mode
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_SENDER`: From address
- `SMTP_USE_STARTTLS`: `true`/`false`
- `SMTP_USE_SSL`: `true`/`false`
- `STATE_FILE`: path to persistence file (default `/data/state.json`)
- `HEALTH_HOST`: bind host for health endpoint (default `0.0.0.0`)
- `HEALTH_PORT`: health endpoint port (default `8090`)
- `HEALTH_FAILURE_THRESHOLD`: consecutive failed cycles before `/health` returns unhealthy (default `3`)

Watchdog settings (from `docker-compose.yml` / `.env`):

- `WATCHDOG_WATCH_CONTAINERS`: comma-separated container names to watch
- `WATCHDOG_COOLDOWN_SECONDS`: suppress duplicate alerts for the same container/event
- `WATCHDOG_AUTO_RESTART_UNHEALTHY`: restart unhealthy containers automatically
- `WATCHDOG_ALERT_RECIPIENTS`: optional override for watchdog emails (falls back to `ALERT_RECIPIENTS`)

## Finding a Station UUID

Query station list and search by name:

```bash
curl -s "https://pegelonline.wsv.de/webservices/rest-api/v2/stations.json?includeTimeseries=true"

```

Then copy the station `uuid` for your `STATION_UUID` setting.

With jobs config, set that value in each job's `station_uuid` field.

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

## Test Mode (every minute)

For quick testing, set:

`DEBUG_RUN_EVERY_MINUTE=true`

Then the service checks once per minute instead of only at `FORECAST_RUN_HOURS`.
