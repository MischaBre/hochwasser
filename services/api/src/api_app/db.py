from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

import psycopg
from fastapi import HTTPException, status
from psycopg import sql
from psycopg.rows import dict_row

from api_app.schemas import JobCreateRequest, JobUpdateRequest

Role = Literal["admin", "member"]
SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


@dataclass(frozen=True)
class Actor:
    user_id: UUID
    org_id: UUID
    role: Role


def _ensure_admin_actor(actor: Actor) -> None:
    if actor.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role is required",
        )


def ensure_membership(
    *,
    database_url: str,
    org_id: UUID,
    user_id: UUID,
    initial_admin_user_id: UUID | None,
    auto_provision_members: bool,
) -> Actor:
    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT role
                    FROM public.organization_members
                    WHERE org_id = %s AND user_id = %s
                    """,
                    (org_id, user_id),
                )
                row = cur.fetchone()
                if row is not None:
                    return Actor(user_id=user_id, org_id=org_id, role=row["role"])

                if not auto_provision_members:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User is not a member of this organization",
                    )

                role: Role = "member"
                if (
                    initial_admin_user_id is not None
                    and user_id == initial_admin_user_id
                ):
                    role = "admin"

                now = datetime.now(tz=timezone.utc)
                cur.execute(
                    """
                    INSERT INTO public.organization_members (
                        org_id,
                        user_id,
                        role,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (org_id, user_id)
                    DO UPDATE SET role = public.organization_members.role
                    RETURNING role
                    """,
                    (org_id, user_id, role, now, now),
                )
                inserted = cur.fetchone()
                if inserted is None:
                    raise RuntimeError("failed to ensure membership")
                return Actor(user_id=user_id, org_id=org_id, role=inserted["role"])


def list_jobs(
    *, database_url: str, actor: Actor, include_disabled: bool
) -> list[dict[str, Any]]:
    query = """
        SELECT
            job_uuid,
            name,
            station_uuid,
            limit_cm,
            recipients,
            alert_recipient,
            locale,
            schedule_cron,
            repeat_alerts_on_check,
            enabled,
            org_id,
            created_by,
            updated_by,
            created_at,
            updated_at,
            disabled_at
        FROM public.alert_jobs
        WHERE org_id = %s
    """
    params: list[Any] = [actor.org_id]
    if actor.role != "admin":
        query += " AND created_by = %s"
        params.append(actor.user_id)
    if not include_disabled:
        query += " AND enabled = TRUE"
    query += " ORDER BY created_at DESC"

    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return list(cur.fetchall())


def create_job(
    *, database_url: str, actor: Actor, payload: JobCreateRequest
) -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc)
    job_uuid = str(uuid4())
    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
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
                    enabled,
                    org_id,
                    created_by,
                    updated_by,
                    created_at,
                    updated_at,
                    disabled_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, %s, NULL)
                RETURNING
                    job_uuid,
                    name,
                    station_uuid,
                    limit_cm,
                    recipients,
                    alert_recipient,
                    locale,
                    schedule_cron,
                    repeat_alerts_on_check,
                    enabled,
                    org_id,
                    created_by,
                    updated_by,
                    created_at,
                    updated_at,
                    disabled_at
                """,
                (
                    job_uuid,
                    payload.name,
                    payload.station_uuid,
                    payload.limit_cm,
                    payload.recipients,
                    payload.alert_recipient,
                    payload.locale,
                    payload.schedule_cron,
                    payload.repeat_alerts_on_check,
                    actor.org_id,
                    actor.user_id,
                    actor.user_id,
                    now,
                    now,
                ),
            )
            created = cur.fetchone()
            if created is None:
                raise RuntimeError("failed to create job")
            cur.execute(
                """
                INSERT INTO public.job_audit_log (
                    org_id,
                    job_uuid,
                    actor_user_id,
                    action,
                    changed_fields,
                    created_at
                )
                VALUES (%s, %s, %s, 'created', %s, %s)
                """,
                (
                    actor.org_id,
                    created["job_uuid"],
                    actor.user_id,
                    [
                        "name",
                        "station_uuid",
                        "limit_cm",
                        "recipients",
                        "alert_recipient",
                        "locale",
                        "schedule_cron",
                        "repeat_alerts_on_check",
                        "enabled",
                    ],
                    now,
                ),
            )
            return created


def count_active_jobs_for_user(*, database_url: str, actor: Actor) -> int:
    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT count(*) AS total
                FROM public.alert_jobs
                WHERE org_id = %s
                  AND created_by = %s
                  AND enabled = TRUE
                """,
                (actor.org_id, actor.user_id),
            )
            row = cur.fetchone()
            return int(row["total"]) if row else 0


def delete_user_account_data(*, database_url: str, actor: Actor) -> None:
    now = datetime.now(tz=timezone.utc)

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT role
                    FROM public.organization_members
                    WHERE org_id = %s AND user_id = %s
                    FOR UPDATE
                    """,
                    (actor.org_id, actor.user_id),
                )
                member_row = cur.fetchone()
                if member_row is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organization member not found",
                    )

                if member_row["role"] == "admin":
                    cur.execute(
                        """
                        SELECT count(*) AS total
                        FROM public.organization_members
                        WHERE org_id = %s AND role = 'admin'
                        """,
                        (actor.org_id,),
                    )
                    admins_row = cur.fetchone()
                    admin_total = int(admins_row["total"]) if admins_row else 0
                    if admin_total <= 1:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Cannot delete the last admin in organization",
                        )

                cur.execute(
                    """
                    UPDATE public.alert_jobs
                    SET updated_by = %s,
                        updated_at = %s
                    WHERE org_id = %s
                      AND updated_by = %s
                    """,
                    (SYSTEM_USER_ID, now, actor.org_id, actor.user_id),
                )

                cur.execute(
                    """
                    DELETE FROM public.job_audit_log
                    WHERE org_id = %s AND actor_user_id = %s
                    """,
                    (actor.org_id, actor.user_id),
                )

                cur.execute(
                    """
                    DELETE FROM public.membership_audit_log
                    WHERE org_id = %s
                      AND (actor_user_id = %s OR target_user_id = %s)
                    """,
                    (actor.org_id, actor.user_id, actor.user_id),
                )

                cur.execute(
                    """
                    DELETE FROM public.alert_jobs
                    WHERE org_id = %s AND created_by = %s
                    """,
                    (actor.org_id, actor.user_id),
                )

                cur.execute(
                    """
                    DELETE FROM public.organization_members
                    WHERE org_id = %s AND user_id = %s
                    """,
                    (actor.org_id, actor.user_id),
                )


def get_job(*, database_url: str, org_id: UUID, job_uuid: str) -> dict[str, Any] | None:
    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    job_uuid,
                    name,
                    station_uuid,
                    limit_cm,
                    recipients,
                    alert_recipient,
                    locale,
                    schedule_cron,
                    repeat_alerts_on_check,
                    enabled,
                    org_id,
                    created_by,
                    updated_by,
                    created_at,
                    updated_at,
                    disabled_at
                FROM public.alert_jobs
                WHERE org_id = %s AND job_uuid = %s
                """,
                (org_id, job_uuid),
            )
            return cur.fetchone()


def can_manage_job(actor: Actor, created_by: UUID) -> bool:
    if actor.role == "admin":
        return True
    return actor.user_id == created_by


def update_job(
    *, database_url: str, actor: Actor, job_uuid: str, payload: JobUpdateRequest
) -> dict[str, Any]:
    existing = get_job(
        database_url=database_url, org_id=actor.org_id, job_uuid=job_uuid
    )
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    if not can_manage_job(actor, existing["created_by"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only job owner or admin can modify this job",
        )

    changes = payload.model_dump(exclude_none=True)
    if not changes:
        return existing

    now = datetime.now(tz=timezone.utc)
    update_fields: list[Any] = []
    values: list[Any] = []

    for key in (
        "name",
        "station_uuid",
        "limit_cm",
        "recipients",
        "alert_recipient",
        "locale",
        "schedule_cron",
        "repeat_alerts_on_check",
        "enabled",
    ):
        if key not in changes:
            continue
        update_fields.append(sql.SQL("{} = %s").format(sql.Identifier(key)))
        values.append(changes[key])

    if "enabled" in changes:
        update_fields.append(sql.SQL("disabled_at = %s"))
        values.append(None if changes["enabled"] else now)

    update_fields.append(sql.SQL("updated_by = %s"))
    values.append(actor.user_id)
    update_fields.append(sql.SQL("updated_at = %s"))
    values.append(now)

    values.extend([actor.org_id, job_uuid])

    statement = sql.SQL(
        """
        UPDATE public.alert_jobs
        SET {updates}
        WHERE org_id = %s AND job_uuid = %s
        RETURNING
            job_uuid,
            name,
            station_uuid,
            limit_cm,
            recipients,
            alert_recipient,
            locale,
            schedule_cron,
            repeat_alerts_on_check,
            enabled,
            org_id,
            created_by,
            updated_by,
            created_at,
            updated_at,
            disabled_at
        """
    ).format(updates=sql.SQL(", ").join(update_fields))

    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(statement, values)
            updated = cur.fetchone()
            if updated is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job not found",
                )
            cur.execute(
                """
                INSERT INTO public.job_audit_log (
                    org_id,
                    job_uuid,
                    actor_user_id,
                    action,
                    changed_fields,
                    created_at
                )
                VALUES (%s, %s, %s, 'updated', %s, %s)
                """,
                (
                    actor.org_id,
                    updated["job_uuid"],
                    actor.user_id,
                    sorted(changes.keys()),
                    now,
                ),
            )
            return updated


def soft_delete_job(*, database_url: str, actor: Actor, job_uuid: str) -> None:
    existing = get_job(
        database_url=database_url, org_id=actor.org_id, job_uuid=job_uuid
    )
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    if not can_manage_job(actor, existing["created_by"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only job owner or admin can delete this job",
        )

    now = datetime.now(tz=timezone.utc)
    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE public.alert_jobs
                SET enabled = FALSE,
                    disabled_at = %s,
                    updated_by = %s,
                    updated_at = %s
                WHERE org_id = %s AND job_uuid = %s
                RETURNING job_uuid
                """,
                (now, actor.user_id, now, actor.org_id, job_uuid),
            )
            updated = cur.fetchone()
            if updated is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job not found",
                )
            cur.execute(
                """
                INSERT INTO public.job_audit_log (
                    org_id,
                    job_uuid,
                    actor_user_id,
                    action,
                    changed_fields,
                    created_at
                )
                VALUES (%s, %s, %s, 'soft_deleted', %s, %s)
                """,
                (
                    actor.org_id,
                    updated["job_uuid"],
                    actor.user_id,
                    ["enabled", "disabled_at"],
                    now,
                ),
            )


def get_job_status(
    *, database_url: str, actor: Actor, job_uuid: str
) -> dict[str, Any] | None:
    existing = get_job(
        database_url=database_url, org_id=actor.org_id, job_uuid=job_uuid
    )
    if existing is None:
        return None
    if not can_manage_job(actor, existing["created_by"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only job owner or admin can view this job",
        )

    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    j.job_uuid,
                    s.state,
                    s.state_since,
                    s.predicted_crossing_at,
                    s.predicted_end_at,
                    s.predicted_peak_cm,
                    s.predicted_peak_at,
                    s.last_notified_state,
                    s.last_notified_at,
                    s.updated_at
                FROM public.alert_jobs AS j
                LEFT JOIN public.alert_job_runtime_state AS s
                    ON s.job_uuid = j.job_uuid
                WHERE j.org_id = %s AND j.job_uuid = %s
                """,
                (actor.org_id, job_uuid),
            )
            return cur.fetchone()


def list_job_outbox(
    *, database_url: str, actor: Actor, job_uuid: str, limit: int, offset: int
) -> list[dict[str, Any]]:
    existing = get_job(
        database_url=database_url, org_id=actor.org_id, job_uuid=job_uuid
    )
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    if not can_manage_job(actor, existing["created_by"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only job owner or admin can view this job",
        )

    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    e.id,
                    e.target_state,
                    e.trigger_reason,
                    e.status,
                    e.attempt_count,
                    e.next_attempt_at,
                    e.sent_at,
                    e.last_error,
                    e.created_at,
                    e.updated_at
                FROM public.email_outbox AS e
                INNER JOIN public.alert_jobs AS j
                    ON j.job_uuid = e.job_uuid
                WHERE j.org_id = %s AND j.job_uuid = %s
                ORDER BY e.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (actor.org_id, job_uuid, limit, offset),
            )
            return list(cur.fetchall())


def list_members(*, database_url: str, actor: Actor) -> list[dict[str, Any]]:
    _ensure_admin_actor(actor)

    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT user_id, role, created_at, updated_at
                FROM public.organization_members
                WHERE org_id = %s
                ORDER BY role DESC, created_at ASC, user_id ASC
                """,
                (actor.org_id,),
            )
            return list(cur.fetchall())


def set_member_role(
    *,
    database_url: str,
    actor: Actor,
    target_user_id: UUID,
    new_role: Role,
) -> dict[str, Any]:
    _ensure_admin_actor(actor)

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT user_id, role, created_at, updated_at
                    FROM public.organization_members
                    WHERE org_id = %s AND user_id = %s
                    FOR UPDATE
                    """,
                    (actor.org_id, target_user_id),
                )
                row = cur.fetchone()
                if row is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organization member not found",
                    )

                old_role = row["role"]
                if old_role == new_role:
                    return row

                if old_role == "admin" and new_role == "member":
                    cur.execute(
                        """
                        SELECT count(*)
                        FROM public.organization_members
                        WHERE org_id = %s AND role = 'admin'
                        """,
                        (actor.org_id,),
                    )
                    admin_count_row = cur.fetchone()
                    admin_count = (
                        int(admin_count_row["count"]) if admin_count_row else 0
                    )
                    if admin_count <= 1:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Cannot demote the last admin in organization",
                        )

                now = datetime.now(tz=timezone.utc)
                cur.execute(
                    """
                    UPDATE public.organization_members
                    SET role = %s,
                        updated_at = %s
                    WHERE org_id = %s AND user_id = %s
                    RETURNING user_id, role, created_at, updated_at
                    """,
                    (new_role, now, actor.org_id, target_user_id),
                )
                updated = cur.fetchone()
                if updated is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organization member not found",
                    )

                action = (
                    "promoted_to_admin" if new_role == "admin" else "demoted_to_member"
                )
                cur.execute(
                    """
                    INSERT INTO public.membership_audit_log (
                        org_id,
                        actor_user_id,
                        target_user_id,
                        action,
                        old_role,
                        new_role,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        actor.org_id,
                        actor.user_id,
                        target_user_id,
                        action,
                        old_role,
                        new_role,
                        now,
                    ),
                )
                return updated


def list_job_audit_log(
    *,
    database_url: str,
    actor: Actor,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    _ensure_admin_actor(actor)

    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    org_id,
                    job_uuid,
                    actor_user_id,
                    action,
                    changed_fields,
                    created_at
                FROM public.job_audit_log
                WHERE org_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (actor.org_id, limit, offset),
            )
            return list(cur.fetchall())


def list_membership_audit_log(
    *,
    database_url: str,
    actor: Actor,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    _ensure_admin_actor(actor)

    with psycopg.connect(database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    id,
                    org_id,
                    actor_user_id,
                    target_user_id,
                    action,
                    old_role,
                    new_role,
                    created_at
                FROM public.membership_audit_log
                WHERE org_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (actor.org_id, limit, offset),
            )
            return list(cur.fetchall())
