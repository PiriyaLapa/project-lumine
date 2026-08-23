"""
Synthetic demo-data generator — Faker-based customers, transactions, and
follow-up tasks for safely recapturing screenshots / recording a demo video
without ever touching real customer or SAP data.

Usage:
    cd backend
    .venv/bin/python scripts/seed_demo_data.py

Every generated ID is DEMO-prefixed (customer_id, idoc_number, ean, store,
staff employee_code) so it's unambiguous even in a partial screenshot crop —
see the 2026-08-23 audit that found real data had been used for this exact
purpose before. Reuses the app's own TaskScheduler so follow-up due dates
match production logic exactly (2D/2W/2M), rather than reimplementing it.

Safe to re-run — skips if DEMO customers already exist. Delete rows matching
customer_id LIKE 'DEMO%' (customers, transactions, follow_up_tasks) first to
reseed from scratch.
"""
import sys
import os
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings

if settings.ENV == "production":
    sys.exit(
        "Refusing to run: ENV=production. This script populates a demo/dev "
        "database with synthetic data only and must never run against "
        "production."
    )

from faker import Faker

from app.database import SessionLocal
from app.models.store import Store
from app.models.staff import Staff
from app.models.customer import Customer
from app.services.auth_service import AuthService
from app.services.task_scheduler import TaskScheduler
from app.repositories import customer_repo, transaction_repo

fake = Faker("th_TH")

DEMO_STORE_ID = 9001
DEMO_STORE_NAME = "DEMO Store — Synthetic Data"
DEMO_STAFF_EMAIL = "demo.associate@lumine.test"
DEMO_STAFF_PASSWORD = "demo-password-123"
DEMO_STAFF_EMPLOYEE_CODE = "DEMO001"
NUM_CUSTOMERS = 18

MATERIALS = [
    "Wool Blend Suit Jacket",
    "Leather Chelsea Boot",
    "Silk Tie — Micro Pattern",
    "Cotton Oxford Shirt",
    "Cashmere Overcoat",
    "Leather Card Holder",
    "Merino Crewneck Sweater",
    "Chino Trouser — Slim Fit",
    "Canvas Sneaker",
    "Leather Belt — Reversible",
]


def ensure_store(db):
    store = db.query(Store).filter(Store.id == DEMO_STORE_ID).first()
    if store:
        return store
    store = Store(id=DEMO_STORE_ID, name=DEMO_STORE_NAME)
    db.add(store)
    db.flush()
    print(f"  CREATE store id={DEMO_STORE_ID} name={DEMO_STORE_NAME!r}")
    return store


def ensure_staff(db):
    staff = db.query(Staff).filter(Staff.email == DEMO_STAFF_EMAIL).first()
    if staff:
        return staff
    staff = Staff(
        name="Demo Associate",
        employee_code=DEMO_STAFF_EMPLOYEE_CODE,
        role="sales_associate",
        store_id=DEMO_STORE_ID,
        email=DEMO_STAFF_EMAIL,
        hashed_password=AuthService.hash_password(DEMO_STAFF_PASSWORD),
        deleted_at=None,
    )
    db.add(staff)
    db.flush()
    print(f"  CREATE staff {DEMO_STAFF_EMAIL}  password={DEMO_STAFF_PASSWORD}")
    return staff


def main():
    db = SessionLocal()
    try:
        store = ensure_store(db)
        staff = ensure_staff(db)

        existing = db.query(Customer).filter(Customer.customer_id.like("DEMO%")).count()
        if existing:
            print(f"  SKIP  {existing} DEMO customers already exist — nothing to do.")
            print("  (delete rows matching customer_id LIKE 'DEMO%' first to reseed)")
            return

        created_customers = 0
        created_transactions = 0
        created_tasks = 0

        for i in range(NUM_CUSTOMERS):
            customer_id = f"DEMO{1000 + i}"
            name = fake.name()

            customer_repo.create(
                db,
                {
                    "customer_id": customer_id,
                    "name": name,
                    "phone": fake.phone_number(),
                    "email": fake.email(),
                    "line_id": None,
                    "language": "th",
                    "language_source": "auto_detected",
                    "do_not_contact": False,
                    "source": "crm_import",
                    "staff_id": staff.id,
                },
            )
            created_customers += 1

            posting_date = date.today() - timedelta(days=random.randint(1, 90))
            idoc_number = f"DEMO-IDOC-{1000 + i}"
            transaction, _ = transaction_repo.upsert(
                db,
                {
                    "idoc_number": idoc_number,
                    "posting_date": posting_date,
                    "ean": f"DEMO-EAN-{1000 + i}",
                    "material_desc": random.choice(MATERIALS),
                    "customer_id": customer_id,
                    "staff_id": staff.id,
                    "sales_rep_name": staff.name,
                    "customer_name": name,
                    "price": round(random.uniform(2500, 45000), 2),
                    "returned": False,
                },
            )
            created_transactions += 1

            result = TaskScheduler.schedule(db, transaction)
            created_tasks += result.tasks_created

        db.commit()
        print(
            f"\nDone — {created_customers} customers, {created_transactions} "
            f"transactions, {created_tasks} follow-up tasks created "
            f"(store_id={store.id}, staff={staff.email}). All IDs prefixed "
            "DEMO — synthetic only, zero real data."
        )
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
