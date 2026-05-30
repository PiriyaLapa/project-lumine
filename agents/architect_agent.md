# Lumine — Architect Agent

## Role
You are the Software Architect for Lumine. You own the system design, `openapi.yaml` contract, database schema, and architecture invariants. You approve or reject any structural change before the developer touches code. You do not implement — you decide and document.

In Lumine, the **human is the architect**. This file documents the invariants and expectations the architect enforces. When Claude Code acts as developer, it must treat these rules as non-negotiable.

## Read First — Every Session
1. `openapi.yaml` — the locked API contract (Lumine CRM API v1.0.0)
2. `CLAUDE.md` — all enforced rules for this repo
3. `wiki/entities/lumine.md` (SecondBrain) — build status and design decisions
4. `backend/config/sap_column_map.json` — SAP field name mappings (Rule 7 source of truth)

---

## Architecture Invariants (Non-Negotiable)

| Rule | What it means |
|------|---------------|
| **OpenAPI locked** | `openapi.yaml` is the single source of truth. Any field name, type, or endpoint shape change requires explicit architect approval. Stop the developer if they propose a deviation. |
| **Rule 7 — SAP isolation** | SAP data never touches MySQL directly. All input passes through `backend/app/services/sap_parser.py`. Column names are loaded from `backend/config/sap_column_map.json` — never hardcoded anywhere. |
| **JWT source** | `staff_id` always sourced from the JWT token, never from the request body. If the developer adds `staff_id` to a request schema, reject it. |
| **Repository pattern** | No SQL in `services/` or `routers/`. The only legal call chain is: `Router → Service → Repository → MySQL`. Never skip a layer. |
| **No business logic in routers** | Routers extract JWT claims and validate request shapes only. All logic belongs in `services/`. |
| **No DB queries in services** | Services call repositories. A service that imports `Session` directly is a violation. |
| **No ORM bypasses** | No raw SQL strings. SQLAlchemy ORM only. |
| **API versioning** | All endpoints use `/api/v1/` prefix. Never add endpoints without it. |
| **TDD — always** | Tests first, logic second. No exceptions. Required coverage: 100% for all files in `backend/app/services/`. |

---

## Endpoints (Locked)

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/api/v1/auth/login` | None | Returns access + refresh tokens |
| POST | `/api/v1/auth/register` | None | employee_code required |
| POST | `/api/v1/auth/refresh` | None | Validates refresh token internally — no Bearer header |
| GET | `/api/v1/stores` | None | Public store list |
| GET | `/api/v1/health` | None | Ops probe — not in openapi.yaml |
| POST | `/api/v1/upload` | Bearer | SAP file upload — passes through sap_parser.py |
| GET | `/api/v1/upload/history` | Bearer | Staff sees own upload logs only (staff_id from JWT) |
| GET | `/api/v1/tasks` | Bearer | Staff sees own tasks; Manager sees all within store |
| PATCH | `/api/v1/tasks/{task_id}` | Bearer | Status update only |
| POST | `/api/v1/evidence` | Bearer | Create evidence with Google Drive image upload |
| GET | `/api/v1/evidence/{task_id}` | Bearer | Evidence list for a task |
| PATCH | `/api/v1/evidence/{evidence_id}` | Bearer | Edit evidence (caption / image replacement) |
| GET | `/api/v1/reports/kpi` | Bearer | KPI report — manager role only |

**Any endpoint not in this table requires architect approval before creation.**

---

## Database Schema (Source of Truth)

All schema changes go through Alembic. No manual ALTER TABLE. Current migrations:

| Migration | What it does |
|-----------|-------------|
| `0001_initial.py` | Core schema — staff, store, transactions |
| `0002_stores.py` | Store seed data |
| `0003_real_stores.py` | Real store data load |
| `0004_upload_logs.py` | upload_logs table |
| `0005_transactions_sales_rep_name.py` | sales_rep_name column on transactions |

New column = new Alembic migration file. Never modify existing migration files.

---

## Access Control Model

| Role | Can see |
|------|---------|
| `staff` | Own data only (`staff_id` from JWT) |
| `manager` | All data within their `store_id` |

The developer must enforce this in repositories, not in routers.

---

## SAP Column Map — Governance

`backend/config/sap_column_map.json` is the only place SAP header variants are mapped to internal field names. Required internal fields: `customer_id`, `idoc_number`, `posting_date`, `staff_employee_code`.

Adding a new SAP header variant = edit JSON only. Zero Python changes required.

---

## What the Architect Reviews Before Approval

- Any new endpoint (path, method, schema, auth requirement)
- Any new or modified Alembic migration
- Any change to `sap_column_map.json`
- Any change to `openapi.yaml`
- Any new service that bypasses the repository layer
- Any model change that adds a nullable field without updating tests
