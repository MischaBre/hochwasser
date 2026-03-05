from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel, Field, field_validator


def _validate_cron(expression: str) -> str:
    candidate = expression.strip()
    if not candidate:
        raise ValueError("schedule_cron must not be empty")
    try:
        CronTrigger.from_crontab(candidate)
    except ValueError as exc:
        raise ValueError(
            "schedule_cron must be a valid 5-field crontab expression"
        ) from exc
    return candidate


class JobBaseRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    station_uuid: str = Field(min_length=1, max_length=120)
    limit_cm: float = Field(gt=-10000, lt=100000)
    recipients: list[str] = Field(min_length=1, max_length=25)
    alert_recipient: str = Field(min_length=3, max_length=254)
    locale: Literal["de", "en"]
    schedule_cron: str
    repeat_alerts_on_check: bool = False

    @field_validator("station_uuid", "alert_recipient")
    @classmethod
    def _strip_required_strings(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty")
        return stripped

    @field_validator("recipients")
    @classmethod
    def _validate_recipients(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in value:
            candidate = raw.strip()
            if not candidate:
                continue
            lowered = candidate.lower()
            if lowered in seen:
                continue
            if "@" not in candidate:
                raise ValueError(f"invalid recipient address: {candidate}")
            seen.add(lowered)
            cleaned.append(candidate)
        if not cleaned:
            raise ValueError("recipients must contain at least one address")
        return cleaned

    @field_validator("schedule_cron")
    @classmethod
    def _validate_schedule_cron(cls, value: str) -> str:
        return _validate_cron(value)


class JobCreateRequest(JobBaseRequest):
    pass


class JobUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    station_uuid: str | None = Field(default=None, min_length=1, max_length=120)
    limit_cm: float | None = Field(default=None, gt=-10000, lt=100000)
    recipients: list[str] | None = Field(default=None, min_length=1, max_length=25)
    alert_recipient: str | None = Field(default=None, min_length=3, max_length=254)
    locale: Literal["de", "en"] | None = None
    schedule_cron: str | None = None
    repeat_alerts_on_check: bool | None = None
    enabled: bool | None = None

    @field_validator("station_uuid", "alert_recipient")
    @classmethod
    def _strip_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty")
        return stripped

    @field_validator("recipients")
    @classmethod
    def _validate_optional_recipients(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in value:
            candidate = raw.strip()
            if not candidate:
                continue
            lowered = candidate.lower()
            if lowered in seen:
                continue
            if "@" not in candidate:
                raise ValueError(f"invalid recipient address: {candidate}")
            seen.add(lowered)
            cleaned.append(candidate)
        if not cleaned:
            raise ValueError("recipients must contain at least one address")
        return cleaned

    @field_validator("schedule_cron")
    @classmethod
    def _validate_optional_schedule_cron(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_cron(value)


class JobResponse(BaseModel):
    job_uuid: str
    name: str
    station_uuid: str
    limit_cm: float
    recipients: list[str]
    alert_recipient: str
    locale: Literal["de", "en"]
    schedule_cron: str
    repeat_alerts_on_check: bool
    enabled: bool
    org_id: UUID
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime
    disabled_at: datetime | None


class MeResponse(BaseModel):
    user_id: UUID
    org_id: UUID
    role: Literal["admin", "member"]


class JobStatusResponse(BaseModel):
    job_uuid: str
    state: str | None
    state_since: datetime | None
    predicted_crossing_at: datetime | None
    predicted_end_at: datetime | None
    predicted_peak_cm: float | None
    predicted_peak_at: datetime | None
    last_notified_state: str | None
    last_notified_at: datetime | None
    updated_at: datetime | None


class OutboxEntryResponse(BaseModel):
    id: int
    target_state: str
    trigger_reason: str
    status: str
    attempt_count: int
    next_attempt_at: datetime
    sent_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class OutboxListResponse(BaseModel):
    items: list[OutboxEntryResponse]
    limit: int
    offset: int


class StationSummaryResponse(BaseModel):
    uuid: str
    number: str
    shortname: str
    longname: str
    km: float | None
    agency: str
    longitude: float | None
    latitude: float | None
    water_shortname: str
    water_longname: str


class StationListResponse(BaseModel):
    items: list[StationSummaryResponse]
    limit: int
    offset: int


class OrganizationMemberResponse(BaseModel):
    user_id: UUID
    role: Literal["admin", "member"]
    created_at: datetime
    updated_at: datetime


class OrganizationMembersListResponse(BaseModel):
    items: list[OrganizationMemberResponse]


class JobAuditEntryResponse(BaseModel):
    id: int
    org_id: UUID
    job_uuid: str
    actor_user_id: UUID
    action: Literal["created", "updated", "soft_deleted"]
    changed_fields: list[str]
    created_at: datetime


class JobAuditListResponse(BaseModel):
    items: list[JobAuditEntryResponse]
    limit: int
    offset: int


class MembershipAuditEntryResponse(BaseModel):
    id: int
    org_id: UUID
    actor_user_id: UUID
    target_user_id: UUID
    action: Literal["promoted_to_admin", "demoted_to_member"]
    old_role: Literal["admin", "member"]
    new_role: Literal["admin", "member"]
    created_at: datetime


class MembershipAuditListResponse(BaseModel):
    items: list[MembershipAuditEntryResponse]
    limit: int
    offset: int
