"""
Auth Router — POST /api/v1/auth/login and /refresh.
These are the only two endpoints that do NOT require a JWT.
All other endpoints use Depends(get_current_staff).
"""
import logging
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator, model_validator
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


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    confirm_password: str
    role: str
    store_id: int

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email format.")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in {"sales_associate", "store_manager"}:
            raise ValueError("Role must be sales_associate or store_manager.")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


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
        logger.warning("Failed login attempt — invalid credentials.")
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


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Self-register a new staff account.
    # TODO: Restrict role selection in production — any visitor can currently register as store_manager.
    Returns access + refresh token pair for immediate session creation.
    """
    existing = staff_repo.get_by_email(db, body.email)
    if existing:
        logger.warning("Registration attempt with duplicate email.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    employee_code = f"REG-{uuid.uuid4()}"
    hashed = AuthService.hash_password(body.password)

    new_staff = staff_repo.create_staff(
        db,
        name=body.full_name,
        email=body.email,
        hashed_password=hashed,
        role=body.role,
        store_id=body.store_id,
        employee_code=employee_code,
    )

    token_data = {
        "staff_id": new_staff.id,
        "role": new_staff.role,
        "store_id": new_staff.store_id,
    }

    logger.info("New registration: staff_id=%s role=%s", new_staff.id, new_staff.role)

    return AuthResponse(
        access_token=AuthService.create_access_token(token_data),
        refresh_token=AuthService.create_refresh_token(token_data),
        staff_id=new_staff.id,
        role=new_staff.role,
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
