"""
Auth Router — POST /api/v1/auth/login and /refresh.
These are the only two endpoints that do NOT require a JWT.
All other endpoints use Depends(get_current_staff).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService, AuthError
from app.repositories import staff_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Request / Response schemas (match openapi.yaml exactly)
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    staff_id: int
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate staff and return access + refresh token pair.
    staff_id and role are embedded in the JWT — client does not set them.
    """
    staff = staff_repo.get_by_email(db, body.email)

    if not staff or not AuthService.verify_password(body.password, staff.hashed_password):
        logger.warning("Failed login attempt for email: %s", body.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "staff_id": staff.id,
        "role": staff.role,
        "store_id": staff.store_id,
    }

    logger.info("Login successful: staff_id=%s role=%s", staff.id, staff.role)

    return AuthResponse(
        access_token=AuthService.create_access_token(token_data),
        refresh_token=AuthService.create_refresh_token(token_data),
        staff_id=staff.id,
        role=staff.role,
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh(body: RefreshRequest):
    """
    Exchange a valid refresh token for a new access token.
    Refresh token expiry forces re-login (7 days).
    """
    try:
        new_access_token = AuthService.refresh_access_token(body.refresh_token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return RefreshResponse(access_token=new_access_token)
