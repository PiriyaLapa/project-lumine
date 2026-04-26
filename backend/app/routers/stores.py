"""
Stores Router — GET /api/v1/stores
Public endpoint (no JWT) — required for self-registration store picker.
See CLAUDE.md Auth Rules for the approved exception list.
"""
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import store_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["stores"])


# ---------------------------------------------------------------------------
# Response schema — field names match openapi.yaml Store schema exactly
# ---------------------------------------------------------------------------

class StoreResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("/stores", response_model=list[StoreResponse])
def list_stores(db: Session = Depends(get_db)):
    """
    Return all stores. Public — no JWT required.
    Used by RegisterScreen to populate the store picker.
    """
    stores = store_repo.get_all(db)
    logger.info("Stores list requested — %d stores returned.", len(stores))
    return stores
