"""
JWT Auth Middleware — FastAPI dependency.
Every protected endpoint uses: current_staff: TokenPayload = Depends(get_current_staff)
staff_id is ALWAYS extracted from the JWT payload — never from the request body.
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth_service import AuthService, AuthError, TokenPayload

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer()


def get_current_staff(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> TokenPayload:
    """
    Extract and validate JWT from Authorization: Bearer header.
    Returns TokenPayload with staff_id, role, store_id.

    Raises:
        401 Unauthorized — token missing, expired, or invalid.
    """
    try:
        payload = AuthService.decode_token(credentials.credentials)
    except AuthError as exc:
        logger.warning("Auth failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_manager(
    current_staff: TokenPayload = Depends(get_current_staff),
) -> TokenPayload:
    """
    Dependency for manager-only endpoints.
    Raises 403 if the staff role is not store_manager.
    """
    if current_staff.role != "store_manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires store_manager role.",
        )
    return current_staff
