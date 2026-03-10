from __future__ import annotations

from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from api_app.auth import JwtVerifier, parse_bearer_token
from api_app.config import ApiSettings


def _settings() -> ApiSettings:
    return ApiSettings(
        database_url="postgresql://irrelevant",
        supabase_jwks_url="https://example.test/auth/v1/.well-known/jwks.json",
        supabase_issuer="https://example.test/auth/v1",
        supabase_audience="authenticated",
        default_org_id=uuid4(),
        initial_admin_user_id=None,
        auto_provision_members=True,
        cors_allow_origins=(),
        supabase_url="https://example.test",
        supabase_service_role_key="service-role-key",
        max_active_jobs_per_user=10,
        max_alarm_recipients_per_job=5,
    )


def test_parse_bearer_token_rejects_missing_credentials() -> None:
    with pytest.raises(HTTPException, match="Missing bearer token"):
        parse_bearer_token(None)


def test_parse_bearer_token_rejects_non_bearer_scheme() -> None:
    with pytest.raises(HTTPException, match="Unsupported auth scheme"):
        parse_bearer_token(
            HTTPAuthorizationCredentials(scheme="Basic", credentials="abc")
        )


def test_parse_bearer_token_accepts_bearer_scheme() -> None:
    token = parse_bearer_token(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-123")
    )
    assert token == "token-123"


def test_verify_rejects_invalid_subject_uuid(monkeypatch: pytest.MonkeyPatch) -> None:
    verifier = JwtVerifier(_settings())

    class _Key:
        key = object()

    monkeypatch.setattr(
        verifier._jwk_client,
        "get_signing_key_from_jwt",
        lambda _token: _Key(),
    )
    monkeypatch.setattr(
        jwt,
        "decode",
        lambda *_args, **_kwargs: {
            "sub": "not-a-uuid",
            "iss": "https://example.test/auth/v1",
            "aud": "authenticated",
            "exp": 9999999999,
        },
    )

    with pytest.raises(HTTPException, match="sub is not a UUID"):
        verifier.verify("token")


def test_verify_maps_pyjwt_error_to_http_401(monkeypatch: pytest.MonkeyPatch) -> None:
    verifier = JwtVerifier(_settings())

    class _Key:
        key = object()

    monkeypatch.setattr(
        verifier._jwk_client,
        "get_signing_key_from_jwt",
        lambda _token: _Key(),
    )

    def _raise_decode(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise jwt.InvalidAudienceError("bad audience")

    monkeypatch.setattr(jwt, "decode", _raise_decode)

    with pytest.raises(HTTPException, match="Invalid bearer token"):
        verifier.verify("token")
