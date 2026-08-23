"""
Lumine CRM — FastAPI entry point.
Run: uvicorn app.main:app --reload
All routes prefixed /api/v1/ as per SRS §11.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.routers import auth, upload, tasks, evidence, reports, stores, customers, auto_touch
from app.config import settings
from app.rate_limit import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

_docs_url = None if settings.ENV == "production" else "/docs"
_redoc_url = None if settings.ENV == "production" else "/redoc"
_openapi_url = None if settings.ENV == "production" else "/openapi.json"

app = FastAPI(
    title="Lumine CRM API",
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(stores.router)
app.include_router(upload.router)
app.include_router(tasks.router)
app.include_router(evidence.router)
app.include_router(reports.router)
app.include_router(customers.router)
app.include_router(auto_touch.router)


@app.get("/health")
def health():
    return {"status": "ok"}
