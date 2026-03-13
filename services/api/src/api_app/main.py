from __future__ import annotations

import os
import threading
from collections import deque
from time import monotonic
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials

from api_app.auth import (
    JwtVerifier,
    bearer_scheme,
    get_jwt_verifier,
    parse_bearer_token,
)
from api_app.config import ApiSettings, get_settings
from api_app.db import (
    Actor,
    count_active_jobs_for_user,
    create_job,
    delete_user_account_data,
    ensure_membership,
    get_job_status,
    list_job_audit_log,
    list_members,
    list_membership_audit_log,
    list_job_outbox,
    list_jobs,
    set_member_role,
    soft_delete_job,
    update_job,
)
from api_app.schemas import (
    JobCreateRequest,
    JobAuditEntryResponse,
    JobAuditListResponse,
    JobResponse,
    JobStatusResponse,
    JobUpdateRequest,
    MembershipAuditEntryResponse,
    MembershipAuditListResponse,
    MeResponse,
    OrganizationMemberResponse,
    OrganizationMembersListResponse,
    OutboxEntryResponse,
    OutboxListResponse,
    StationListResponse,
    StationMeasurementResponse,
    StationSummaryResponse,
)
from api_app.stations import (
    list_station_forecast,
    list_station_measurements,
    list_stations,
)
from api_app.supabase_admin import delete_auth_user

app = FastAPI(title="Hochwasser API", version="0.1.0")

_rate_limit_lock = threading.Lock()
_rate_limit_buckets: dict[str, deque[float]] = {}
_WRITE_WINDOW_SECONDS = 60
_WRITE_MAX_REQUESTS = 30
_ADMIN_WINDOW_SECONDS = 60
_ADMIN_MAX_REQUESTS = 20


def _cors_allow_origins_from_env() -> tuple[str, ...]:
    return tuple(
        origin.strip()
        for origin in os.getenv("API_CORS_ALLOW_ORIGINS", "").split(",")
        if origin.strip()
    )


def _settings_dep() -> ApiSettings:
    return get_settings()


SettingsDep = Annotated[ApiSettings, Depends(_settings_dep)]


_cors_origins = _cors_allow_origins_from_env()
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_cors_origins),
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=True,
    )


def _actor_dep(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: SettingsDep,
    verifier: Annotated[JwtVerifier, Depends(get_jwt_verifier)],
) -> Actor:
    token = parse_bearer_token(credentials)
    user = verifier.verify(token)
    return ensure_membership(
        database_url=settings.database_url,
        org_id=settings.default_org_id,
        user_id=user.user_id,
        initial_admin_user_id=settings.initial_admin_user_id,
        auto_provision_members=settings.auto_provision_members,
    )


ActorDep = Annotated[Actor, Depends(_actor_dep)]


def _enforce_rate_limit(
    *, key: str, max_requests: int, window_seconds: int, now: float | None = None
) -> None:
    current = monotonic() if now is None else now

    with _rate_limit_lock:
        bucket = _rate_limit_buckets.get(key)
        if bucket is None:
            bucket = deque()
            _rate_limit_buckets[key] = bucket

        cutoff = current - window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= max_requests:
            retry_after = max(1, int(window_seconds - (current - bucket[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please retry later.",
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(current)


def _write_rate_limit_dep(actor: ActorDep) -> None:
    _enforce_rate_limit(
        key=f"write:{actor.user_id}",
        max_requests=_WRITE_MAX_REQUESTS,
        window_seconds=_WRITE_WINDOW_SECONDS,
    )


def _admin_rate_limit_dep(actor: ActorDep) -> None:
    _enforce_rate_limit(
        key=f"admin:{actor.user_id}",
        max_requests=_ADMIN_MAX_REQUESTS,
        window_seconds=_ADMIN_WINDOW_SECONDS,
    )


WriteRateLimitDep = Annotated[None, Depends(_write_rate_limit_dep)]
AdminRateLimitDep = Annotated[None, Depends(_admin_rate_limit_dep)]


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready(settings: SettingsDep) -> dict[str, str]:
    try:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from exc
    return {"status": "ok"}


@app.get("/v1/me", response_model=MeResponse)
def me(actor: ActorDep, settings: SettingsDep) -> MeResponse:
    active_jobs_count = count_active_jobs_for_user(
        database_url=settings.database_url,
        actor=actor,
    )
    return MeResponse(
        user_id=actor.user_id,
        org_id=actor.org_id,
        role=actor.role,
        active_jobs_count=active_jobs_count,
        max_active_jobs=settings.max_active_jobs_per_user,
        max_alarm_recipients_per_job=settings.max_alarm_recipients_per_job,
    )


def _raise_validation_error(field: str, message: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[
            {
                "loc": ["body", field],
                "msg": message,
                "type": "value_error",
            }
        ],
    )


def _enforce_recipients_limit(*, recipients: list[str], max_recipients: int) -> None:
    if len(recipients) > max_recipients:
        _raise_validation_error(
            "recipients",
            f"recipients must contain at most {max_recipients} addresses",
        )


@app.get("/v1/jobs", response_model=list[JobResponse])
def get_jobs(
    actor: ActorDep,
    settings: SettingsDep,
    include_disabled: bool = Query(default=False),
) -> list[JobResponse]:
    rows = list_jobs(
        database_url=settings.database_url,
        actor=actor,
        include_disabled=include_disabled,
    )
    return [JobResponse(**row) for row in rows]


@app.get("/v1/stations", response_model=StationListResponse)
def get_stations(
    actor: ActorDep,
    search: str = Query(default="", max_length=120),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    uuids: str = Query(default="", max_length=10000),
) -> StationListResponse:
    del actor

    requested_uuids = tuple(
        candidate.strip() for candidate in uuids.split(",") if candidate.strip()
    )
    rows = list_stations(
        search=search,
        limit=limit,
        offset=offset,
        uuids=requested_uuids,
    )
    return StationListResponse(
        items=[StationSummaryResponse(**row.__dict__) for row in rows],
        limit=limit,
        offset=offset,
    )


@app.get(
    "/v1/stations/{station_uuid}/measurements",
    response_model=list[StationMeasurementResponse],
)
def get_station_measurements(
    station_uuid: str,
    actor: ActorDep,
    start: str = Query(default="P3D", max_length=32),
) -> list[StationMeasurementResponse]:
    del actor
    rows = list_station_measurements(station_uuid=station_uuid, start=start)
    return [StationMeasurementResponse(**row.__dict__) for row in rows]


@app.get(
    "/v1/stations/{station_uuid}/forecast",
    response_model=list[StationMeasurementResponse],
)
def get_station_forecast(
    station_uuid: str,
    actor: ActorDep,
) -> list[StationMeasurementResponse]:
    del actor
    rows = list_station_forecast(station_uuid=station_uuid)
    return [StationMeasurementResponse(**row.__dict__) for row in rows]


@app.get("/v1/public/stations", response_model=StationListResponse)
def get_public_stations(
    search: str = Query(default="", max_length=120),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    uuids: str = Query(default="", max_length=10000),
) -> StationListResponse:
    requested_uuids = tuple(
        candidate.strip() for candidate in uuids.split(",") if candidate.strip()
    )
    rows = list_stations(
        search=search,
        limit=limit,
        offset=offset,
        uuids=requested_uuids,
    )
    return StationListResponse(
        items=[StationSummaryResponse(**row.__dict__) for row in rows],
        limit=limit,
        offset=offset,
    )


@app.get(
    "/v1/public/stations/{station_uuid}/measurements",
    response_model=list[StationMeasurementResponse],
)
def get_public_station_measurements(
    station_uuid: str,
    start: str = Query(default="P3D", max_length=32),
) -> list[StationMeasurementResponse]:
    rows = list_station_measurements(station_uuid=station_uuid, start=start)
    return [StationMeasurementResponse(**row.__dict__) for row in rows]


@app.get(
    "/v1/public/stations/{station_uuid}/forecast",
    response_model=list[StationMeasurementResponse],
)
def get_public_station_forecast(station_uuid: str) -> list[StationMeasurementResponse]:
    rows = list_station_forecast(station_uuid=station_uuid)
    return [StationMeasurementResponse(**row.__dict__) for row in rows]


@app.post("/v1/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def post_job(
    payload: JobCreateRequest,
    actor: ActorDep,
    settings: SettingsDep,
    _rate_limit: WriteRateLimitDep,
) -> JobResponse:
    del _rate_limit
    _enforce_recipients_limit(
        recipients=payload.recipients,
        max_recipients=settings.max_alarm_recipients_per_job,
    )
    active_jobs_count = count_active_jobs_for_user(
        database_url=settings.database_url,
        actor=actor,
    )
    if active_jobs_count >= settings.max_active_jobs_per_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Active jobs limit reached "
                f"({settings.max_active_jobs_per_user} max per user)"
            ),
        )

    created = create_job(
        database_url=settings.database_url, actor=actor, payload=payload
    )
    return JobResponse(**created)


@app.patch("/v1/jobs/{job_uuid}", response_model=JobResponse)
def patch_job(
    job_uuid: str,
    payload: JobUpdateRequest,
    actor: ActorDep,
    settings: SettingsDep,
    _rate_limit: WriteRateLimitDep,
) -> JobResponse:
    del _rate_limit
    if payload.recipients is not None:
        _enforce_recipients_limit(
            recipients=payload.recipients,
            max_recipients=settings.max_alarm_recipients_per_job,
        )

    updated = update_job(
        database_url=settings.database_url,
        actor=actor,
        job_uuid=job_uuid,
        payload=payload,
    )
    return JobResponse(**updated)


@app.delete("/v1/jobs/{job_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_uuid: str,
    actor: ActorDep,
    settings: SettingsDep,
    _rate_limit: WriteRateLimitDep,
) -> Response:
    del _rate_limit
    soft_delete_job(database_url=settings.database_url, actor=actor, job_uuid=job_uuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/v1/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    actor: ActorDep,
    settings: SettingsDep,
    _rate_limit: WriteRateLimitDep,
) -> Response:
    del _rate_limit
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account deletion is not configured",
        )

    delete_user_account_data(database_url=settings.database_url, actor=actor)
    delete_auth_user(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        user_id=actor.user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/v1/jobs/{job_uuid}/status", response_model=JobStatusResponse)
def job_status(
    job_uuid: str,
    actor: ActorDep,
    settings: SettingsDep,
) -> JobStatusResponse:
    row = get_job_status(
        database_url=settings.database_url,
        actor=actor,
        job_uuid=job_uuid,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return JobStatusResponse(**row)


@app.get("/v1/jobs/{job_uuid}/outbox", response_model=OutboxListResponse)
def job_outbox(
    job_uuid: str,
    actor: ActorDep,
    settings: SettingsDep,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> OutboxListResponse:
    rows = list_job_outbox(
        database_url=settings.database_url,
        actor=actor,
        job_uuid=job_uuid,
        limit=limit,
        offset=offset,
    )
    return OutboxListResponse(
        items=[OutboxEntryResponse(**row) for row in rows],
        limit=limit,
        offset=offset,
    )


@app.get("/v1/admin/members", response_model=OrganizationMembersListResponse)
def admin_list_members(
    actor: ActorDep,
    settings: SettingsDep,
    _rate_limit: AdminRateLimitDep,
) -> OrganizationMembersListResponse:
    del _rate_limit
    rows = list_members(database_url=settings.database_url, actor=actor)
    return OrganizationMembersListResponse(
        items=[OrganizationMemberResponse(**row) for row in rows]
    )


@app.post(
    "/v1/admin/members/{user_id}/promote",
    response_model=OrganizationMemberResponse,
)
def admin_promote_member(
    user_id: UUID,
    actor: ActorDep,
    settings: SettingsDep,
    _rate_limit: AdminRateLimitDep,
) -> OrganizationMemberResponse:
    del _rate_limit
    row = set_member_role(
        database_url=settings.database_url,
        actor=actor,
        target_user_id=user_id,
        new_role="admin",
    )
    return OrganizationMemberResponse(**row)


@app.post(
    "/v1/admin/members/{user_id}/demote",
    response_model=OrganizationMemberResponse,
)
def admin_demote_member(
    user_id: UUID,
    actor: ActorDep,
    settings: SettingsDep,
    _rate_limit: AdminRateLimitDep,
) -> OrganizationMemberResponse:
    del _rate_limit
    row = set_member_role(
        database_url=settings.database_url,
        actor=actor,
        target_user_id=user_id,
        new_role="member",
    )
    return OrganizationMemberResponse(**row)


@app.get("/v1/admin/audit/jobs", response_model=JobAuditListResponse)
def admin_job_audit(
    actor: ActorDep,
    settings: SettingsDep,
    _rate_limit: AdminRateLimitDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> JobAuditListResponse:
    del _rate_limit
    rows = list_job_audit_log(
        database_url=settings.database_url,
        actor=actor,
        limit=limit,
        offset=offset,
    )
    return JobAuditListResponse(
        items=[JobAuditEntryResponse(**row) for row in rows],
        limit=limit,
        offset=offset,
    )


@app.get("/v1/admin/audit/memberships", response_model=MembershipAuditListResponse)
def admin_membership_audit(
    actor: ActorDep,
    settings: SettingsDep,
    _rate_limit: AdminRateLimitDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> MembershipAuditListResponse:
    del _rate_limit
    rows = list_membership_audit_log(
        database_url=settings.database_url,
        actor=actor,
        limit=limit,
        offset=offset,
    )
    return MembershipAuditListResponse(
        items=[MembershipAuditEntryResponse(**row) for row in rows],
        limit=limit,
        offset=offset,
    )
