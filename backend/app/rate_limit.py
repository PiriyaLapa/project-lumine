"""
Shared rate limiter instance — lives in its own module so both main.py
(wiring) and individual routers (the @limiter.limit(...) decorator) can
import it without a circular import.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
