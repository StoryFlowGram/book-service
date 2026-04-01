import os
import secrets

from fastapi import Depends, Header, HTTPException, status


def token_verifier():
    raise NotImplementedError("Must be overridden in infrastructure layer")


async def book_protocol():
    raise NotImplementedError("Must be overridden in infrastructure layer")


async def chapter_protocol():
    raise NotImplementedError("Must be overridden in infrastructure layer")


async def storage():
    raise NotImplementedError("Must be overridden in infrastructure layer")


def _gateway_token() -> str:
    token = os.getenv("INTERNAL_GATEWAY_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_GATEWAY_TOKEN is not configured",
        )
    return token


async def ensure_gateway_request(
    x_gateway_token: str | None = Header(default=None, alias="X-Gateway-Token"),
):
    expected_token = _gateway_token()
    if not x_gateway_token or not secrets.compare_digest(x_gateway_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request must come through trusted gateway",
        )


async def get_current_user(
    _: None = Depends(ensure_gateway_request),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header is missing",
        )

    try:
        return int(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-Id header must be integer",
        )


async def get_check_admin(
    x_admin: str | None = Header(default=None, alias="X-User-Role"),
    x_user_id=Depends(get_current_user),
):
    if x_admin != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return {"x-admin": x_admin, "x-user-id": x_user_id}
