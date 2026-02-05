"""Authentication helpers for JWT-protected endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from config import get_settings
from database import fetch_user_by_id, fetch_user_by_username, get_db
from logger import get_logger

try:  # pragma: no cover - defensive patch for bcrypt>=4
    import bcrypt as _bcrypt

    if not hasattr(_bcrypt, "__about__") and hasattr(_bcrypt, "__version__"):
        _bcrypt.__about__ = SimpleNamespace(__version__=_bcrypt.__version__)  # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    pass

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
LOGGER = get_logger("auth")
SETTINGS = get_settings()


class AuthError(HTTPException):
    def __init__(self, detail: str = "Invalid authentication credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(*, user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=SETTINGS.access_token_expire_hours)
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    token = jwt.encode(payload, SETTINGS.secret_key, algorithm=SETTINGS.algorithm)
    return token


def authenticate_user(db_conn, username: str, password: str) -> Optional[dict]:
    user_row = fetch_user_by_username(db_conn, username)
    if not user_row:
        return None
    if not verify_password(password, user_row["password"]):
        return None
    return {"id": user_row["id"], "username": user_row["username"]}


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_conn=Depends(get_db),
) -> dict:
    if credentials is None:
        raise AuthError("Authorization header missing")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SETTINGS.secret_key, algorithms=[SETTINGS.algorithm])
        user_id = int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        LOGGER.info("Expired token rejected")
        raise AuthError("Token expired") from None
    except (jwt.InvalidTokenError, TypeError, ValueError) as exc:
        LOGGER.info("Invalid token rejected: %s", exc)
        raise AuthError("Could not validate credentials") from None

    user_row = fetch_user_by_id(db_conn, user_id)
    if not user_row:
        raise AuthError("User not found")

    user = {"id": user_row["id"], "username": user_row["username"]}
    request.state.user = user
    return user
