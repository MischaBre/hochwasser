from __future__ import annotations

from http import HTTPStatus
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from fastapi import HTTPException, status


def delete_auth_user(
    *, supabase_url: str, service_role_key: str, user_id: UUID
) -> None:
    url = f"{supabase_url.rstrip('/')}/auth/v1/admin/users/{user_id}"
    request = Request(
        url=url,
        method="DELETE",
        headers={
            "Authorization": f"Bearer {service_role_key}",
            "apikey": service_role_key,
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=10) as response:
            if response.status in {HTTPStatus.OK, HTTPStatus.NO_CONTENT}:
                return
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Supabase admin delete failed with status {response.status}",
            )
    except HTTPError as exc:
        if exc.code == HTTPStatus.NOT_FOUND:
            return
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase admin delete failed",
        ) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase admin endpoint unavailable",
        ) from exc
