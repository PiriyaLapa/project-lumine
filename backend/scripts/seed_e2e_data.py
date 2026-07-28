"""
E2E seed script — inserts the one throwaway staff account the E2E suite
logs in as. Run against the isolated docker-compose.e2e.yml stack only —
never against the dev/QA database.

Usage (from inside the e2e-backend container, or with DATABASE_URL pointed
at the e2e-mysql service):
    docker compose -f docker-compose.e2e.yml exec e2e-backend python scripts/seed_e2e_data.py

Migration 0003 replaces the placeholder store with 5 real Hugo Boss
Thailand stores (8901/8902/8904/8907/8918) — no separate Store row is
needed here, mirrors scripts/seed.py's existing convention of using
store_id=8901 ("BOSS Siam Paragon").

Safe to re-run — skips if the account already exists.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models.store import Store  # noqa: F401 — registers `stores` table for staff.store_id FK resolution
from app.models.staff import Staff
from app.services.auth_service import AuthService

E2E_STAFF_EMAIL = "e2e@lumine.test"
E2E_STAFF_PASSWORD = "e2e-password-123"
E2E_STAFF_EMPLOYEE_CODE = "E2E001"
E2E_STAFF_STORE_ID = 8901


def main():
    db = SessionLocal()
    try:
        existing = db.query(Staff).filter(Staff.email == E2E_STAFF_EMAIL).first()
        if existing:
            print(f"  SKIP  {E2E_STAFF_EMAIL} (already exists)")
            return

        staff = Staff(
            name="E2E Test Staff",
            employee_code=E2E_STAFF_EMPLOYEE_CODE,
            role="sales_associate",
            store_id=E2E_STAFF_STORE_ID,
            email=E2E_STAFF_EMAIL,
            hashed_password=AuthService.hash_password(E2E_STAFF_PASSWORD),
            deleted_at=None,
        )
        db.add(staff)
        db.commit()
        print(f"  CREATE {E2E_STAFF_EMAIL}  employee_code={E2E_STAFF_EMPLOYEE_CODE}  password={E2E_STAFF_PASSWORD}")
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
