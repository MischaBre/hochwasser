from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from api_app.config import ApiSettings
from api_app.db import Actor
from api_app.main import _actor_dep, _settings_dep, app


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


def _resolve_db_url() -> str:
    raw = (
        os.getenv("API_TEST_DATABASE_URL")
        or _dotenv_value("API_TEST_DATABASE_URL")
        or os.getenv("API_DATABASE_URL")
        or _dotenv_value("API_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or _dotenv_value("DATABASE_URL")
        or ""
    )
    if not raw:
        return ""
    parsed = urlsplit(raw)
    if parsed.hostname != "postgres":
        return raw
    userinfo = ""
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo += f":{parsed.password}"
        userinfo += "@"
    port = f":{parsed.port}" if parsed.port else ""
    return urlunsplit(
        (
            parsed.scheme,
            f"{userinfo}localhost{port}",
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )


def _best_effort_cleanup(
    db_url: str, sql_text: str, params: tuple[object, ...]
) -> None:
    try:
        with psycopg.connect(db_url) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(sql_text, params)  # type: ignore[arg-type]
    except psycopg.Error:
        return


DB_URL = _resolve_db_url()
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def db_url() -> str:
    if not DB_URL:
        pytest.skip("integration DB url not configured")
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
                cur.execute(
                    """
                    SELECT count(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name IN ('job_audit_log', 'membership_audit_log')
                    """
                )
                table_count_row = cur.fetchone()
                if not table_count_row or int(table_count_row[0]) < 2:
                    pytest.skip(
                        "integration DB does not have audit tables (run migration V9)"
                    )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"integration DB unavailable: {exc}")
    return DB_URL


@dataclass(frozen=True)
class ActorSet:
    org_id: UUID
    owner: Actor
    other_member: Actor
    admin: Actor


@pytest.fixture()
def actors(db_url: str) -> Iterator[ActorSet]:
    org_id = uuid4()
    owner_id = uuid4()
    other_id = uuid4()
    admin_id = uuid4()
    now = datetime.now(tz=timezone.utc)

    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.organizations (id, name, created_at) VALUES (%s, %s, %s)",
                    (org_id, f"test-org-{org_id}", now),
                )
                cur.execute(
                    """
                    INSERT INTO public.organization_members (org_id, user_id, role, created_at, updated_at)
                    VALUES
                        (%s, %s, 'member', %s, %s),
                        (%s, %s, 'member', %s, %s),
                        (%s, %s, 'admin', %s, %s)
                    """,
                    (
                        org_id,
                        owner_id,
                        now,
                        now,
                        org_id,
                        other_id,
                        now,
                        now,
                        org_id,
                        admin_id,
                        now,
                        now,
                    ),
                )

    try:
        yield ActorSet(
            org_id=org_id,
            owner=Actor(user_id=owner_id, org_id=org_id, role="member"),
            other_member=Actor(user_id=other_id, org_id=org_id, role="member"),
            admin=Actor(user_id=admin_id, org_id=org_id, role="admin"),
        )
    finally:
        _best_effort_cleanup(
            db_url,
            "DELETE FROM public.alert_jobs WHERE org_id = %s",
            (org_id,),
        )
        _best_effort_cleanup(
            db_url,
            "DELETE FROM public.organization_members WHERE org_id = %s",
            (org_id,),
        )
        _best_effort_cleanup(
            db_url,
            "DELETE FROM public.organizations WHERE id = %s",
            (org_id,),
        )


@contextmanager
def _client_for_actor(db_url: str, actor: Actor) -> Iterator[TestClient]:
    settings = ApiSettings(
        database_url=db_url,
        supabase_jwks_url="https://example.test/auth/v1/.well-known/jwks.json",
        supabase_issuer="https://example.test/auth/v1",
        supabase_audience="authenticated",
        default_org_id=actor.org_id,
        initial_admin_user_id=None,
        auto_provision_members=False,
        cors_allow_origins=(),
    )

    app.dependency_overrides[_settings_dep] = lambda: settings
    app.dependency_overrides[_actor_dep] = lambda: actor
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def _create_job_for_owner(
    db_url: str, actors: ActorSet, name: str = "owned-job"
) -> str:
    job_uuid = str(uuid4())
    now = datetime.now(tz=timezone.utc)
    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
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
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE, TRUE, %s, %s, %s, %s, %s)
                    """,
                    (
                        job_uuid,
                        name,
                        str(uuid4()),
                        500.0,
                        ["alerts@example.com"],
                        "ops@example.com",
                        "en",
                        "*/10 * * * *",
                        actors.org_id,
                        actors.owner.user_id,
                        actors.owner.user_id,
                        now,
                        now,
                    ),
                )
    return job_uuid


def test_owner_can_patch_own_job(db_url: str, actors: ActorSet) -> None:
    job_uuid = _create_job_for_owner(db_url, actors)
    with _client_for_actor(db_url, actors.owner) as client:
        response = client.patch(f"/v1/jobs/{job_uuid}", json={"name": "renamed"})
    assert response.status_code == 200
    assert response.json()["name"] == "renamed"


def test_member_cannot_patch_other_members_job(db_url: str, actors: ActorSet) -> None:
    job_uuid = _create_job_for_owner(db_url, actors)
    with _client_for_actor(db_url, actors.other_member) as client:
        response = client.patch(f"/v1/jobs/{job_uuid}", json={"name": "forbidden"})
    assert response.status_code == 403
    assert "owner or admin" in response.json()["detail"]


def test_admin_can_patch_any_job_in_org(db_url: str, actors: ActorSet) -> None:
    job_uuid = _create_job_for_owner(db_url, actors)
    with _client_for_actor(db_url, actors.admin) as client:
        response = client.patch(f"/v1/jobs/{job_uuid}", json={"limit_cm": 600.0})
    assert response.status_code == 200
    assert response.json()["limit_cm"] == 600.0


def test_delete_is_soft_delete(db_url: str, actors: ActorSet) -> None:
    job_uuid = _create_job_for_owner(db_url, actors)

    with _client_for_actor(db_url, actors.owner) as client:
        response = client.delete(f"/v1/jobs/{job_uuid}")
    assert response.status_code == 204

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT enabled, disabled_at FROM public.alert_jobs WHERE org_id = %s AND job_uuid = %s",
                (actors.org_id, job_uuid),
            )
            row = cur.fetchone()
    assert row is not None
    enabled, disabled_at = row
    assert enabled is False
    assert disabled_at is not None


def test_jobs_endpoint_is_org_scoped(db_url: str, actors: ActorSet) -> None:
    own_job_uuid = _create_job_for_owner(db_url, actors, name="visible-job")

    other_org_id = uuid4()
    other_job_uuid = str(uuid4())
    now = datetime.now(tz=timezone.utc)
    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.organizations (id, name, created_at) VALUES (%s, %s, %s)",
                    (other_org_id, f"other-org-{other_org_id}", now),
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
                        enabled,
                        org_id,
                        created_by,
                        updated_by,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE, TRUE, %s, %s, %s, %s, %s)
                    """,
                    (
                        other_job_uuid,
                        "hidden-job",
                        str(uuid4()),
                        700.0,
                        ["alerts@example.com"],
                        "ops@example.com",
                        "en",
                        "*/15 * * * *",
                        other_org_id,
                        uuid4(),
                        uuid4(),
                        now,
                        now,
                    ),
                )

    try:
        with _client_for_actor(db_url, actors.owner) as client:
            response = client.get("/v1/jobs")
        assert response.status_code == 200
        job_uuids = {item["job_uuid"] for item in response.json()}
        assert own_job_uuid in job_uuids
        assert other_job_uuid not in job_uuids
    finally:
        _best_effort_cleanup(
            db_url,
            "DELETE FROM public.alert_jobs WHERE org_id = %s",
            (other_org_id,),
        )
        _best_effort_cleanup(
            db_url,
            "DELETE FROM public.organizations WHERE id = %s",
            (other_org_id,),
        )


def test_status_returns_404_for_job_outside_org(db_url: str, actors: ActorSet) -> None:
    other_org_id = uuid4()
    other_job_uuid = str(uuid4())
    now = datetime.now(tz=timezone.utc)
    with psycopg.connect(db_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.organizations (id, name, created_at) VALUES (%s, %s, %s)",
                    (other_org_id, f"status-org-{other_org_id}", now),
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
                        enabled,
                        org_id,
                        created_by,
                        updated_by,
                        created_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE, TRUE, %s, %s, %s, %s, %s)
                    """,
                    (
                        other_job_uuid,
                        "status-hidden-job",
                        str(uuid4()),
                        800.0,
                        ["alerts@example.com"],
                        "ops@example.com",
                        "en",
                        "*/15 * * * *",
                        other_org_id,
                        uuid4(),
                        uuid4(),
                        now,
                        now,
                    ),
                )

    try:
        with _client_for_actor(db_url, actors.owner) as client:
            response = client.get(f"/v1/jobs/{other_job_uuid}/status")
        assert response.status_code == 404
    finally:
        _best_effort_cleanup(
            db_url,
            "DELETE FROM public.alert_jobs WHERE org_id = %s",
            (other_org_id,),
        )
        _best_effort_cleanup(
            db_url,
            "DELETE FROM public.organizations WHERE id = %s",
            (other_org_id,),
        )


def test_non_admin_cannot_manage_members(db_url: str, actors: ActorSet) -> None:
    with _client_for_actor(db_url, actors.other_member) as client:
        response = client.post(f"/v1/admin/members/{actors.owner.user_id}/promote")
    assert response.status_code == 403
    assert "Admin role is required" in response.json()["detail"]


def test_admin_can_promote_member_and_writes_audit(
    db_url: str, actors: ActorSet
) -> None:
    with _client_for_actor(db_url, actors.admin) as client:
        response = client.post(
            f"/v1/admin/members/{actors.other_member.user_id}/promote"
        )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT action, old_role, new_role
                FROM public.membership_audit_log
                WHERE org_id = %s AND actor_user_id = %s AND target_user_id = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (actors.org_id, actors.admin.user_id, actors.other_member.user_id),
            )
            row = cur.fetchone()
    assert row == ("promoted_to_admin", "member", "admin")


def test_cannot_demote_last_admin(db_url: str, actors: ActorSet) -> None:
    with _client_for_actor(db_url, actors.admin) as client:
        response = client.post(f"/v1/admin/members/{actors.admin.user_id}/demote")
    assert response.status_code == 409
    assert "last admin" in response.json()["detail"]


def test_admin_can_list_members(db_url: str, actors: ActorSet) -> None:
    with _client_for_actor(db_url, actors.admin) as client:
        response = client.get("/v1/admin/members")
    assert response.status_code == 200
    user_ids = {item["user_id"] for item in response.json()["items"]}
    assert str(actors.owner.user_id) in user_ids
    assert str(actors.other_member.user_id) in user_ids
    assert str(actors.admin.user_id) in user_ids


def test_job_updates_write_job_audit_log(db_url: str, actors: ActorSet) -> None:
    job_uuid = _create_job_for_owner(db_url, actors)
    with _client_for_actor(db_url, actors.owner) as client:
        response = client.patch(f"/v1/jobs/{job_uuid}", json={"name": "audited"})
    assert response.status_code == 200

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT action
                FROM public.job_audit_log
                WHERE org_id = %s AND job_uuid = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (actors.org_id, job_uuid),
            )
            row = cur.fetchone()
    assert row == ("updated",)


def test_admin_can_read_job_audit_endpoint(db_url: str, actors: ActorSet) -> None:
    job_uuid = _create_job_for_owner(db_url, actors)
    with _client_for_actor(db_url, actors.owner) as client:
        patch_response = client.patch(
            f"/v1/jobs/{job_uuid}", json={"name": "audit-read"}
        )
    assert patch_response.status_code == 200

    with _client_for_actor(db_url, actors.admin) as client:
        response = client.get("/v1/admin/audit/jobs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    assert any(item["job_uuid"] == job_uuid for item in payload["items"])


def test_admin_can_read_membership_audit_endpoint(
    db_url: str, actors: ActorSet
) -> None:
    with _client_for_actor(db_url, actors.admin) as client:
        promote_response = client.post(
            f"/v1/admin/members/{actors.other_member.user_id}/promote"
        )
    assert promote_response.status_code == 200

    with _client_for_actor(db_url, actors.admin) as client:
        response = client.get("/v1/admin/audit/memberships")
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    assert any(
        item["target_user_id"] == str(actors.other_member.user_id)
        and item["action"] == "promoted_to_admin"
        for item in payload["items"]
    )


def test_non_admin_cannot_read_audit_endpoints(db_url: str, actors: ActorSet) -> None:
    with _client_for_actor(db_url, actors.other_member) as client:
        jobs_response = client.get("/v1/admin/audit/jobs")
        members_response = client.get("/v1/admin/audit/memberships")
    assert jobs_response.status_code == 403
    assert members_response.status_code == 403
