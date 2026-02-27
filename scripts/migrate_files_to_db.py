from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg


def _load_jobs(jobs_file: Path) -> list[dict[str, object]]:
    payload = json.loads(jobs_file.read_text(encoding="utf-8"))
    raw_jobs = payload.get("jobs") if isinstance(payload, dict) else payload
    if not isinstance(raw_jobs, list):
        raise ValueError("jobs payload must be a list or contain a 'jobs' list")
    return raw_jobs


def _load_dedupe(state_file: Path) -> dict[str, str]:
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    sent_keys = payload.get("sent_keys") if isinstance(payload, dict) else None
    if not isinstance(sent_keys, dict):
        return {}
    return {str(key): str(value) for key, value in sent_keys.items()}


def migrate(database_url: str, jobs_file: Path, state_file: Path) -> tuple[int, int]:
    jobs = _load_jobs(jobs_file)
    dedupe = _load_dedupe(state_file)

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                migrated_jobs = 0
                for job in jobs:
                    limit_raw = job.get("limit_cm", 0)
                    recipients = job.get("recipients", [])
                    if isinstance(recipients, str):
                        recipients = [
                            addr.strip()
                            for addr in recipients.split(",")
                            if addr.strip()
                        ]
                    if not isinstance(recipients, list):
                        raise ValueError(
                            "job recipients must be an array or comma-separated string"
                        )

                    cur.execute(
                        """
                        INSERT INTO public.alert_jobs (
                            job_uuid,
                            name,
                            station_uuid,
                            limit_cm,
                            recipients,
                            alert_recipient,
                            locale,
                            schedule_cron,
                            repeat_alerts_on_check,
                            enabled
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                        ON CONFLICT (job_uuid)
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            station_uuid = EXCLUDED.station_uuid,
                            limit_cm = EXCLUDED.limit_cm,
                            recipients = EXCLUDED.recipients,
                            alert_recipient = EXCLUDED.alert_recipient,
                            locale = EXCLUDED.locale,
                            schedule_cron = EXCLUDED.schedule_cron,
                            repeat_alerts_on_check = EXCLUDED.repeat_alerts_on_check,
                            enabled = EXCLUDED.enabled,
                            updated_at = now()
                        """,
                        (
                            str(job.get("job_uuid", "")).strip(),
                            str(job.get("name", "")).strip(),
                            str(job.get("station_uuid", "")).strip(),
                            float(str(limit_raw)),
                            [
                                str(addr).strip()
                                for addr in recipients
                                if str(addr).strip()
                            ],
                            str(job.get("alert_recipient", "")).strip(),
                            str(job.get("locale", "")).strip().lower(),
                            str(job.get("schedule_cron", "")).strip(),
                            bool(job.get("repeat_alerts_on_check", False)),
                        ),
                    )
                    migrated_jobs += 1

                migrated_dedupe = len(dedupe)

    return migrated_jobs, migrated_dedupe


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate local jobs/state JSON into Postgres"
    )
    parser.add_argument("--jobs-file", default="data/jobs.json")
    parser.add_argument("--state-file", default="data/state.json")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    args = parser.parse_args()

    if not args.database_url:
        raise ValueError("DATABASE_URL is required (set env var or --database-url)")

    jobs_file = Path(args.jobs_file)
    state_file = Path(args.state_file)
    migrated_jobs, migrated_dedupe = migrate(args.database_url, jobs_file, state_file)
    print(
        "Migrated "
        f"{migrated_jobs} job(s). "
        f"Read {migrated_dedupe} legacy dedupe row(s) (not imported with state-machine alerts)."
    )


if __name__ == "__main__":
    main()
