"""
TDD — Auth Service tests.
Tests written BEFORE auth_service.py logic.
All test cases from SRS §6.6 and §7 NFR-02.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.auth_service import AuthService, TokenPayload, AuthError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

STAFF_PAYLOAD = {
    "staff_id": 42,
    "role": "sales_associate",
    "store_id": 7,
}


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------


class TestTokenCreation:
    def test_create_access_token_returns_string(self):
        token = AuthService.create_access_token(STAFF_PAYLOAD)
        assert isinstance(token, str)
        assert len(token) > 10

    def test_create_refresh_token_returns_string(self):
        token = AuthService.create_refresh_token(STAFF_PAYLOAD)
        assert isinstance(token, str)
        assert len(token) > 10

    def test_access_and_refresh_tokens_differ(self):
        access = AuthService.create_access_token(STAFF_PAYLOAD)
        refresh = AuthService.create_refresh_token(STAFF_PAYLOAD)
        assert access != refresh


# ---------------------------------------------------------------------------
# Token validation — valid JWT passes
# ---------------------------------------------------------------------------


class TestTokenValidation:
    def test_valid_access_token_returns_payload(self):
        token = AuthService.create_access_token(STAFF_PAYLOAD)
        payload = AuthService.decode_token(token)
        assert payload.staff_id == 42
        assert payload.role == "sales_associate"
        assert payload.store_id == 7

    def test_payload_contains_exp(self):
        token = AuthService.create_access_token(STAFF_PAYLOAD)
        payload = AuthService.decode_token(token)
        assert payload.exp is not None
        assert payload.exp > datetime.now(timezone.utc).timestamp()

    def test_expired_token_raises_auth_error(self):
        """Expired JWT raises AuthError — not a raw jose exception."""
        from datetime import timedelta
        from jose import jwt as _jwt
        from app.config import settings

        expired_payload = {
            **STAFF_PAYLOAD,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "token_type": "access",
        }
        token = _jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(AuthError, match="expired"):
            AuthService.decode_token(token)

    def test_tampered_token_raises_auth_error(self):
        """Token with modified signature raises AuthError."""
        token = AuthService.create_access_token(STAFF_PAYLOAD)
        tampered = token[:-4] + "XXXX"
        with pytest.raises(AuthError):
            AuthService.decode_token(tampered)

    def test_wrong_role_rejected(self):
        """Token with unknown role value raises AuthError."""
        bad_payload = {**STAFF_PAYLOAD, "role": "super_admin"}
        token = AuthService.create_access_token(bad_payload)
        with pytest.raises(AuthError, match="role"):
            AuthService.decode_token(token)


# ---------------------------------------------------------------------------
# staff_id comes from token only — never from request body
# ---------------------------------------------------------------------------


class TestStaffIdFromToken:
    def test_get_current_staff_id_from_token(self):
        """staff_id extracted from token — not from any external input."""
        token = AuthService.create_access_token(STAFF_PAYLOAD)
        payload = AuthService.decode_token(token)
        assert payload.staff_id == 42

    def test_staff_id_in_payload_not_overrideable(self):
        """Creating a token with staff_id=99 returns 99, not something else."""
        token = AuthService.create_access_token({**STAFF_PAYLOAD, "staff_id": 99})
        payload = AuthService.decode_token(token)
        assert payload.staff_id == 99


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


class TestPasswordHashing:
    def test_hash_is_not_plain_text(self):
        hashed = AuthService.hash_password("secret123")
        assert hashed != "secret123"

    def test_verify_correct_password(self):
        hashed = AuthService.hash_password("secret123")
        assert AuthService.verify_password("secret123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = AuthService.hash_password("secret123")
        assert AuthService.verify_password("wrong", hashed) is False


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------


class TestRefreshToken:
    def test_refresh_token_yields_new_access_token(self):
        refresh = AuthService.create_refresh_token(STAFF_PAYLOAD)
        new_access = AuthService.refresh_access_token(refresh)
        payload = AuthService.decode_token(new_access)
        assert payload.staff_id == STAFF_PAYLOAD["staff_id"]

    def test_access_token_passed_to_refresh_raises_auth_error(self):
        """Passing an access token to refresh_access_token raises AuthError."""
        access = AuthService.create_access_token(STAFF_PAYLOAD)
        with pytest.raises(AuthError, match="not a refresh token"):
            AuthService.refresh_access_token(access)

    def test_expired_refresh_token_raises_auth_error(self):
        from datetime import timedelta
        from jose import jwt as _jwt
        from app.config import settings

        expired_payload = {
            **STAFF_PAYLOAD,
            "exp": datetime.now(timezone.utc) - timedelta(days=1),
            "token_type": "refresh",
        }
        expired_refresh = _jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(AuthError, match="expired"):
            AuthService.refresh_access_token(expired_refresh)
