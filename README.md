# Hochwasser Alert Service (Raspberry Pi + Docker Compose)

This service monitors a Pegelonline station and sends email alerts when a configured
water level limit is expected to be reached.

It checks:
- current water level (`currentmeasurement`)
- official forecast (if available on API)
- fallback trend forecast from recent measurements (last 2 days)

## Features

- Configure everything via `docker-compose.yml`
- Alert deduplication (no repeated mail spam for the same predicted event)
- Persistent state in `./data/state.json`
- Runs at fixed daily times (default: 00:00 and 12:00)

## Quick Start

1. Edit values in `docker-compose.yml`:
   - `STATION_UUID`
   - `LIMIT_CM`
   - `ALERT_RECIPIENTS`
   - SMTP settings
2. Start service:

```bash
docker compose up -d --build
```

3. Follow logs:

```bash
docker compose logs -f
```

## Run Tests

```bash
python -m pip install -r requirements.txt
pytest
```

## Configuration

All values are environment variables in `docker-compose.yml`.

- `PROVIDER`: currently only `pegelonline`
- `STATION_UUID`: Pegelonline station UUID
- `LIMIT_CM`: threshold to alert on (in station unit, usually cm)
- `ALERT_RECIPIENTS`: comma-separated target emails
- `FORECAST_RUN_HOURS`: comma-separated check hours in local time (default `0,12`)
- `FORECAST_HORIZON_HOURS`: how far into future to alert (default `72`)
- `RISING_POINTS`: number of recent points for trend slope (default `12`)
- `MIN_SLOPE_CM_PER_HOUR`: minimum rising slope for trend prediction
- `ALERT_DEDUPE_HOURS`: minimum hours before same predicted alert can repeat
- `TZ`: timezone for logs and mail timestamps
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- `SMTP_SENDER`: From address
- `SMTP_USE_STARTTLS`: `true`/`false`
- `SMTP_USE_SSL`: `true`/`false`
- `STATE_FILE`: path to persistence file (default `/data/state.json`)

## Finding a Station UUID

Query station list and search by name:

```bash
curl -s "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations.json?includeTimeseries=true"
```

Then copy the station `uuid` for your `STATION_UUID` setting.

## Notes About Forecasts

Not every station exposes an official forecast endpoint. If no official forecast is
available, this service calculates a simple linear trend forecast from recent
measurements and marks it as `trend` in the email.

## Raspberry Pi Notes

- Use a 64-bit Raspberry Pi OS if possible.
- Keep `restart: unless-stopped` enabled so service comes back after reboot.
- If SMTP provider requires app passwords, use that password in `SMTP_PASSWORD`.
