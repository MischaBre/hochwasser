# Hochwasser Alert Service (Raspberry Pi + Docker Compose)

This service monitors a Pegelonline station and sends email alerts when a configured
water level limit is expected to be reached.

It checks:
- current water level (`currentmeasurement`)
- official forecast (`<FORECAST_SERIES_SHORTNAME>/measurements`)

## Features

- Configure everything via `docker-compose.yml`
- Alert deduplication (no repeated mail spam for the same predicted event)
- Persistent state in `./data/state.json`
- Runs at fixed daily times (default: 00:00 and 12:00)
- Alert email includes detailed station metadata and a forecast table

## Quick Start

1. Copy `.env.template` to `.env` and set SMTP values.
2. Edit non-secret values in `docker-compose.yml`:
   - `STATION_UUID`
   - `LIMIT_CM`
   - `ALERT_RECIPIENTS`
   - SMTP settings
3. Start service:

```bash
docker compose up -d --build
```

4. Follow logs:

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
- `STATION_UUID`: Pegelonline station UUID
- `LIMIT_CM`: threshold to alert on (in station unit, usually cm)
- `FORECAST_SERIES_SHORTNAME`: forecast timeseries shortname (default `WV`)
- `RUN_EVERY_MINUTE`: set `true` for test mode (run every minute)
- `ALERT_RECIPIENTS`: comma-separated target emails
- `FORECAST_RUN_HOURS`: comma-separated check hours in local time (default `0,12`)
- `FORECAST_HORIZON_HOURS`: how far into future to alert (default `72`)
- `ALERT_DEDUPE_HOURS`: minimum hours before same predicted alert can repeat
- `LOG_LEVEL`: `DEBUG` for verbose fetch + measurement logs (default `DEBUG`)
- `TZ`: timezone for logs and mail timestamps
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_SENDER`: From address
- `SMTP_USE_STARTTLS`: `true`/`false`
- `SMTP_USE_SSL`: `true`/`false`
- `STATE_FILE`: path to persistence file (default `/data/state.json`)

## Finding a Station UUID

Query station list and search by name:

```bash
curl -s "https://pegelonline.wsv.de/webservices/rest-api/v2/stations.json?includeTimeseries=true"

```

Then copy the station `uuid` for your `STATION_UUID` setting.

## Notes About Forecasts

This service first tries forecast measurements from the configured series, for example:

`https://pegelonline.wsv.de/webservices/rest-api/v2/stations/<STATION_UUID>/WV/measurements.json`

An alert is sent if either the current measurement at call time or a forecast value
within the horizon is above the configured threshold.

## Raspberry Pi Notes

- Use a 64-bit Raspberry Pi OS if possible.
- Keep `restart: unless-stopped` enabled so service comes back after reboot.
- If SMTP provider requires app passwords, use that password in `SMTP_PASSWORD`.

## Test Mode (every minute)

For quick testing, set:

`RUN_EVERY_MINUTE=true`

Then the service checks once per minute instead of only at `FORECAST_RUN_HOURS`.
