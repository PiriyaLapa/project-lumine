"""
Development seed script — inserts test staff into MySQL.
Run AFTER `alembic upgrade head`.

Usage:
    cd backend
    .venv/bin/python scripts/seed.py

Creates:
    - 1 store_manager    (manager@lumine.test    / password123)
    - 2 sales_associates (associate1@lumine.test / password123,
                          associate2@lumine.test / password123)

Safe to re-run — skips existing records by email.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.database import SessionLocal
from app.models.staff import Staff
from app.services.auth_service import AuthService

if settings.ENV == "production":
    sys.exit(
        "Refusing to run: ENV=production. This script inserts hardcoded "
        "test accounts and must never run against the production database."
    )

SEED_STAFF = [
    {
        "name": "Store Manager",
        "employee_code": "MGR001",
        "role": "store_manager",
        "store_id": 8901,
        "email": "manager@lumine.test",
        "password": "password123",
    },
    {
        "name": "Associate One",
        "employee_code": "EMP001",
        "role": "sales_associate",
        "store_id": 8901,
        "email": "associate1@lumine.test",
        "password": "password123",
    },
    {
        "name": "Associate Two",
        "employee_code": "EMP002",
        "role": "sales_associate",
        "store_id": 8901,
        "email": "associate2@lumine.test",
        "password": "password123",
    },
]


def main():
    db = SessionLocal()
    try:
        created = 0
        skipped = 0
        for data in SEED_STAFF:
            existing = db.query(Staff).filter(Staff.email == data["email"]).first()
            if existing:
                print(f"  SKIP  {data['email']} (already exists)")
                skipped += 1
                continue

            staff = Staff(
                name=data["name"],
                employee_code=data["employee_code"],
                role=data["role"],
                store_id=data["store_id"],
                email=data["email"],
                hashed_password=AuthService.hash_password(data["password"]),
                deleted_at=None,
            )
            db.add(staff)
            print(f"  CREATE {data['email']}  role={data['role']}  password={data['password']}")
            created += 1

        db.commit()
        print(f"\nDone — {created} created, {skipped} skipped.")
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
