from fastapi import Header

from wallet_service.auth.jwt import AuthContext, decode_bearer_token
from wallet_service.domain.errors import UnauthorizedError


def get_auth_context(authorization: str | None = Header(default=None)) -> AuthContext:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    return decode_bearer_token(token)


def require_idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> str:
    if not idempotency_key:
        raise UnauthorizedError("missing Idempotency-Key header")
    return idempotency_key
