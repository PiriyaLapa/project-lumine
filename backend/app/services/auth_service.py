"""
Auth Service — JWT creation, validation, and password hashing.
SRS §7 NFR-02: 60min access token, 7-day refresh token.
staff_id is ALWAYS read from JWT payload — never from request body.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt_lib
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

VALID_ROLES = {"sales_associate", "store_manager"}

# Token type marker stored in payload to distinguish access vs refresh
_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


class AuthError(Exception):
    """Raised for any JWT or credential failure."""


@dataclass
class TokenPayload:
    staff_id: int
    role: str
    store_id: int
    exp: float
    token_type: str


class AuthService:
    """
    Stateless service — all methods are class methods.
    No DB access here. DB lookups happen in auth router via staff_repo.
    """

    # ------------------------------------------------------------------
    # Token creation
    # ------------------------------------------------------------------

    @classmethod
    def create_access_token(cls, data: dict) -> str:
        """Create a short-lived access token (60 min)."""
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            **data,
            "exp": expire,
            "token_type": _ACCESS_TOKEN_TYPE,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @classmethod
    def create_refresh_token(cls, data: dict) -> str:
        """Create a long-lived refresh token (7 days)."""
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            **data,
            "exp": expire,
            "token_type": _REFRESH_TOKEN_TYPE,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # ------------------------------------------------------------------
    # Token validation
    # ------------------------------------------------------------------

    @classmethod
    def decode_token(cls, token: str) -> TokenPayload:
        """
        Decode and validate a JWT.

        Raises:
            AuthError: token is expired, tampered, or has an invalid role.
        """
        try:
            raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError as exc:
            msg = str(exc).lower()
            if "expired" in msg:
                raise AuthError("Token expired. Please refresh your session.") from exc
            raise AuthError(f"Invalid token: {exc}") from exc

        role = raw.get("role", "")
        if role not in VALID_ROLES:
            raise AuthError(f"Token contains invalid role: '{role}'.")

        return TokenPayload(
            staff_id=int(raw["staff_id"]),
            role=role,
            store_id=int(raw["store_id"]),
            exp=float(raw["exp"]),
            token_type=raw.get("token_type", _ACCESS_TOKEN_TYPE),
        )

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> str:
        """
        Exchange a valid refresh token for a new access token.

        Raises:
            AuthError: refresh token is expired or invalid.
        """
        payload = cls.decode_token(refresh_token)
        if payload.token_type != _REFRESH_TOKEN_TYPE:
            raise AuthError("Provided token is not a refresh token.")

        new_data = {
            "staff_id": payload.staff_id,
            "role": payload.role,
            "store_id": payload.store_id,
        }
        return cls.create_access_token(new_data)

    # ------------------------------------------------------------------
    # Password hashing
    # ------------------------------------------------------------------

    @staticmethod
    def hash_password(plain: str) -> str:
        return _bcrypt_lib.hashpw(plain.encode(), _bcrypt_lib.gensalt()).decode()

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return _bcrypt_lib.checkpw(plain.encode(), hashed.encode())
