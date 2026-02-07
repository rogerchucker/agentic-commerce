from dataclasses import dataclass

import jwt

from wallet_service.config import settings
from wallet_service.domain.errors import ForbiddenError, UnauthorizedError


@dataclass
class AuthContext:
    subject: str
    scope: set[str]


def decode_bearer_token(token: str) -> AuthContext:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=settings.jwt_algorithms,
            audience=settings.jwt_audience,
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("invalid token") from exc

    scope_str = claims.get("scope", "")
    scopes = {s.strip() for s in scope_str.split(" ") if s.strip()}
    return AuthContext(subject=claims.get("sub", "unknown"), scope=scopes)


def require_scope(ctx: AuthContext, required: str) -> None:
    if required not in ctx.scope:
        raise ForbiddenError(f"missing scope: {required}")
