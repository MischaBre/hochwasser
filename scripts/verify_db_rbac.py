from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import psycopg


@dataclass(frozen=True)
class Check:
    name: str
    sql: str
    should_succeed: bool


def _run_check(database_url: str, check: Check) -> tuple[bool, str]:
    last_exc: Exception | None = None
    for candidate_url in _candidate_database_urls(database_url):
        try:
            with psycopg.connect(candidate_url) as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(check.sql)  # type: ignore[arg-type]
            last_exc = None
            break
        except Exception as exc:  # noqa: BLE001
            last_exc = exc

    if last_exc is not None:
        exc = last_exc
        if check.should_succeed:
            return False, f"failed unexpectedly: {exc}"
        if getattr(exc, "sqlstate", None) == "42501":
            return True, "denied as expected"
        return False, f"failed with unexpected error: {exc}"

    if check.should_succeed:
        return True, "succeeded as expected"
    return False, "succeeded but should have been denied"


def _dotenv_value(key: str) -> str:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return ""
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        current_key, current_value = line.split("=", 1)
        if current_key.strip() != key:
            continue
        return current_value.strip().strip('"').strip("'")
    return ""


def _candidate_database_urls(database_url: str) -> tuple[str, ...]:
    parsed = urlsplit(database_url)
    hostname = parsed.hostname or ""
    if hostname != "postgres":
        return (database_url,)

    userinfo = ""
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo += f":{parsed.password}"
        userinfo += "@"
    port = f":{parsed.port}" if parsed.port else ""
    localhost_netloc = f"{userinfo}localhost{port}"
    fallback = urlunsplit(
        (parsed.scheme, localhost_netloc, parsed.path, parsed.query, parsed.fragment)
    )
    return (database_url, fallback)


def verify_engine(database_url: str) -> tuple[int, int]:
    checks = (
        Check(
            name="engine can read alert_jobs",
            sql="SELECT 1 FROM public.alert_jobs LIMIT 1",
            should_succeed=True,
        ),
        Check(
            name="engine can update runtime state",
            sql="UPDATE public.alert_job_runtime_state SET updated_at = updated_at WHERE FALSE",
            should_succeed=True,
        ),
        Check(
            name="engine cannot update alert_jobs",
            sql="UPDATE public.alert_jobs SET updated_at = updated_at WHERE FALSE",
            should_succeed=False,
        ),
    )
    return _run_suite("engine", database_url, checks)


def verify_api(database_url: str) -> tuple[int, int]:
    checks = (
        Check(
            name="api can read alert_jobs",
            sql="SELECT 1 FROM public.alert_jobs LIMIT 1",
            should_succeed=True,
        ),
        Check(
            name="api can update alert_jobs",
            sql="UPDATE public.alert_jobs SET updated_at = updated_at WHERE FALSE",
            should_succeed=True,
        ),
        Check(
            name="api cannot update runtime state",
            sql="UPDATE public.alert_job_runtime_state SET updated_at = updated_at WHERE FALSE",
            should_succeed=False,
        ),
        Check(
            name="api cannot update outbox",
            sql="UPDATE public.email_outbox SET updated_at = updated_at WHERE FALSE",
            should_succeed=False,
        ),
    )
    return _run_suite("api", database_url, checks)


def _run_suite(
    label: str, database_url: str, checks: tuple[Check, ...]
) -> tuple[int, int]:
    passed = 0
    total = len(checks)
    print(f"[{label}] using {database_url}")
    for check in checks:
        ok, detail = _run_check(database_url, check)
        status = "PASS" if ok else "FAIL"
        print(f"  {status} - {check.name} ({detail})")
        if ok:
            passed += 1
    return passed, total


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify DB role boundaries for engine/api"
    )
    parser.add_argument(
        "--engine-database-url",
        default=os.getenv("DATABASE_URL", "") or _dotenv_value("DATABASE_URL"),
        help="Connection URL used by engine",
    )
    parser.add_argument(
        "--api-database-url",
        default=os.getenv("API_DATABASE_URL", "") or _dotenv_value("API_DATABASE_URL"),
        help="Connection URL used by API",
    )
    args = parser.parse_args()

    if not args.engine_database_url:
        raise ValueError("--engine-database-url is required (or set DATABASE_URL)")
    if not args.api_database_url:
        raise ValueError("--api-database-url is required (or set API_DATABASE_URL)")

    engine_passed, engine_total = verify_engine(args.engine_database_url)
    api_passed, api_total = verify_api(args.api_database_url)
    passed = engine_passed + api_passed
    total = engine_total + api_total
    print(f"RBAC checks: {passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
