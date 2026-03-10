from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api_app.config import ApiSettings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: UUID


class JwtVerifier:
    def __init__(self, settings: ApiSettings) -> None:
        self._settings = settings
        self._jwk_client = jwt.PyJWKClient(settings.supabase_jwks_url)

    def verify(self, token: str) -> AuthenticatedUser:
        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token).key
            payload: dict[str, Any] = jwt.decode(
                token,
                signing_key,
                algorithms=["ES256", "RS256"],
                audience=self._settings.supabase_audience,
                issuer=self._settings.supabase_issuer,
                options={"require": ["exp", "iss", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
            ) from exc

        subject = payload.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token: missing sub",
            )

        try:
            user_id = UUID(str(subject))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token: sub is not a UUID",
            ) from exc

        return AuthenticatedUser(user_id=user_id)


@lru_cache(maxsize=1)
def get_jwt_verifier() -> JwtVerifier:
    return JwtVerifier(get_settings())


def parse_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unsupported auth scheme",
        )
    return credentials.credentials
