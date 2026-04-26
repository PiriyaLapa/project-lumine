"""
Lumine CRM — FastAPI entry point.
Run: uvicorn app.main:app --reload
All routes prefixed /api/v1/ as per SRS §11.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, upload, tasks, evidence, reports, stores

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Lumine CRM API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — tighten origins before production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/health")
def health():
    return {"status": "ok"}
