"""
Shared rate limiter instance — lives in its own module so both main.py
(wiring) and individual routers (the @limiter.limit(...) decorator) can
import it without a circular import.

Storage: uses REDIS_URL when set (required for correct enforcement across
more than one backend process/instance — in-memory storage keeps a separate
counter per process, so a client's burst can get split across instances and
never reliably hit the limit). Falls back to in-memory when REDIS_URL is
unset, which is correct for local dev/e2e/CI (always single-process there).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL or "memory://",
    in_memory_fallback_enabled=True,
)
