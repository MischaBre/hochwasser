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
    )
