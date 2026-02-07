import jwt
import pytest

from wallet_service.auth.jwt import decode_bearer_token, require_scope
from wallet_service.config import settings
from wallet_service.domain.errors import ForbiddenError, UnauthorizedError


def test_decode_bearer_token():
    token = jwt.encode(
        {"sub": "svc", "aud": settings.jwt_audience, "scope": "wallet:read wallet:write"},
        settings.jwt_secret,
        algorithm="HS256",
    )
    ctx = decode_bearer_token(token)
    assert ctx.subject == "svc"
    assert "wallet:read" in ctx.scope


def test_decode_invalid_token_raises():
    with pytest.raises(UnauthorizedError):
        decode_bearer_token("bad-token")


def test_require_scope_raises():
    token = jwt.encode(
        {"sub": "svc", "aud": settings.jwt_audience, "scope": "wallet:read"},
        settings.jwt_secret,
        algorithm="HS256",
    )
    ctx = decode_bearer_token(token)
    with pytest.raises(ForbiddenError):
        require_scope(ctx, "wallet:admin")
