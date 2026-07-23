"""JWT verify helpers — Station Service (no login endpoint)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.errors import AppError

_bearer = HTTPBearer(auto_error=False)


class Role(str, Enum):
    VIEWER = "VIEWER"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class Principal:
    username: str
    role: Role


def decode_token(token: str) -> Principal:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
        role_raw = payload.get("role")
        if not username or not role_raw:
            raise AppError(status_code=401, error="UNAUTHORIZED", message="Invalid token claims")
        return Principal(username=username, role=Role(role_raw))
    except AppError:
        raise
    except Exception as exc:
        raise AppError(status_code=401, error="UNAUTHORIZED", message="Invalid or expired token") from exc


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(status_code=401, error="UNAUTHORIZED", message="Missing bearer token")
    return decode_token(credentials.credentials)


def require_roles(*allowed: Role):
    allowed_set = set(allowed)

    def _dep(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in allowed_set:
            raise AppError(
                status_code=403,
                error="FORBIDDEN",
                message=f"Role {principal.role.value} is not allowed",
            )
        return principal

    return _dep
