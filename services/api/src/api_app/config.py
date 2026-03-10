from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from uuid import UUID


def _required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def _bool_env(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(key: str, default: int, *, minimum: int = 1) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {key}: {raw}") from exc
    if value < minimum:
        raise ValueError(f"{key} must be >= {minimum}")
    return value


@dataclass(frozen=True)
class ApiSettings:
    database_url: str
    supabase_jwks_url: str
    supabase_issuer: str
    supabase_audience: str
    default_org_id: UUID
    initial_admin_user_id: UUID | None
    auto_provision_members: bool
    cors_allow_origins: tuple[str, ...]
    supabase_url: str
    supabase_service_role_key: str
    max_active_jobs_per_user: int
    max_alarm_recipients_per_job: int


@lru_cache(maxsize=1)
def get_settings() -> ApiSettings:
    initial_admin_raw = os.getenv("API_INITIAL_ADMIN_USER_ID", "").strip()
    initial_admin_user_id = UUID(initial_admin_raw) if initial_admin_raw else None
    cors_allow_origins = tuple(
        origin.strip()
        for origin in os.getenv("API_CORS_ALLOW_ORIGINS", "").split(",")
        if origin.strip()
    )
    return ApiSettings(
        database_url=_required_env("API_DATABASE_URL"),
        supabase_jwks_url=_required_env("SUPABASE_JWKS_URL"),
        supabase_issuer=_required_env("SUPABASE_ISSUER"),
        supabase_audience=os.getenv("SUPABASE_AUDIENCE", "authenticated").strip(),
        default_org_id=UUID(
            os.getenv("API_DEFAULT_ORG_ID", "11111111-1111-1111-1111-111111111111")
        ),
        initial_admin_user_id=initial_admin_user_id,
        auto_provision_members=_bool_env("API_AUTO_PROVISION_MEMBERS", True),
        cors_allow_origins=cors_allow_origins,
        supabase_url=os.getenv("SUPABASE_URL", "").strip(),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip(),
        max_active_jobs_per_user=_int_env("API_MAX_ACTIVE_JOBS_PER_USER", 10),
        max_alarm_recipients_per_job=_int_env("API_MAX_ALARM_RECIPIENTS_PER_JOB", 5),
    )
