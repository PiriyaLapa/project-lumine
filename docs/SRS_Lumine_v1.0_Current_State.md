# Project Lumine — Software Requirements Specification (Current State)

**Version**: 1.0 (Code-Verified As-Built)
**Generated**: 2026-08-17
**Companion to, not a replacement for**: `Lumine_SRS_v4.1_Integration_Complete.md` (the CLAUDE.md-referenced source of truth for architect-approved design decisions). This document was independently built by reading the live codebase — every claim below traces to a real file, not to v4.1 or to memory. Where this document and v4.1 disagree, v4.1 remains authoritative until the architect reconciles them.

---

## 1. Introduction

### 1.1 Purpose

Lumine is an evidence-based CRM for luxury retail sales associates (built for a luxury retail employer's Thailand operations). It ingests SAP transaction exports, automatically schedules a "T1/T2/T3" follow-up cadence per purchase, and requires photographic/written evidence before a follow-up task can be marked complete. This document describes the system **as it is actually built and deployed today**, not as originally planned.

### 1.2 Scope

Two deployables, one shared contract:
- **Backend**: Python FastAPI + SQLAlchemy + MySQL-compatible database, deployed to Render (`lumine-api-qi77`), 8 routers / 24 REST endpoints.
- **Mobile**: React Native + Expo (TypeScript), 14 screens, distributed as Android APK via EAS Build.
- **Contract**: `openapi.yaml` at the repo root — field names are locked; neither side may rename or add a field without architect approval (CLAUDE.md rule).

### 1.3 Definitions

| Term | Meaning |
|---|---|
| T1/T2/T3 | Follow-up cadence: touch a customer 2 days, 2 weeks, and 2 months after a purchase |
| Cycle Reset | When a customer buys again, all their Pending follow-up tasks are superseded and a fresh T1/T2/T3 cycle starts from the new purchase date |
| Evidence | Photo + notes an associate logs to prove a follow-up actually happened |
| Auto-Touch | AI-assisted follow-up: drafts a personalized message via Claude, associate reviews and sends manually (or, if enabled, the backend can dispatch via LINE/email) |
| PDPA | Thailand's Personal Data Protection Act — governs how customer phone/email/LINE ID are stored, logged, and (not) contacted |
| Rule 7 | CLAUDE.md's standing rule: SAP data never touches MySQL directly — it always passes through `sap_parser.py` |

---

## 2. Overall Description

### 2.1 Product Functions (verified against actual routers)

| Function | Backend Router | Endpoints |
|---|---|---|
| Authentication | `auth.py` | login, register, refresh, me |
| Store lookup | `stores.py` | list stores (public) |
| SAP import | `upload.py` | upload, upload history |
| Follow-up tasks | `tasks.py` | list, mark done |
| Evidence | `evidence.py` | submit, get, patch |
| Reports/KPI | `reports.py` | KPI, dashboard |
| Customers | `customers.py` | CRM import, register, profile, transactions, tasks |
| Auto-Touch | `auto_touch.py` | today list, generate message, send, skip, status |

### 2.2 Operating Environment

| Layer | Actual (verified) |
|---|---|
| Backend hosting | Render, free tier, service `lumine-api-qi77`, **no `render.yaml`/Procfile — deployment is manual dashboard configuration**, not infrastructure-as-code |
| Database | TiDB Cloud (MySQL-wire-protocol compatible), connection via `DATABASE_URL` env var, SQLAlchemy `mysql+pymysql://` dialect |
| Local dev database | MySQL 8.0 via Docker Compose |
| Mobile runtime | React Native 0.74.5 + Expo SDK ~51, TypeScript |
| Mobile distribution | EAS Build → Android APK (no App Store/iOS build config present in `app.json`) |
| CI/CD | **None exists.** No `.github/workflows/` for this repo. Tests and deploys are run manually. |
| Container | `backend/Dockerfile`: `python:3.11-slim`, non-root user, `uvicorn` on port 8000; docker-compose overrides to run `alembic upgrade head && uvicorn ...` locally — **Render does not run this migration step automatically** (see §10). |

---

## 3. System Architecture

Strict layering, enforced by convention (CLAUDE.md "Repository Pattern — Always"):

```
Mobile (React Native) --HTTPS+JWT--> Routers --> Services --> Repositories --> MySQL/TiDB
```

- **Routers** (`app/routers/*.py`) — HTTP concerns only: request parsing, auth dependency injection, response shaping. No business logic, no SQL.
- **Services** (`app/services/*.py`) — business logic. Never receive a raw `Session` to hand back to a router without going through a repository.
- **Repositories** (`app/repositories/*.py`) — the only layer allowed to write SQLAlchemy queries.
- **Rule 7 enforcement point**: `sap_parser.py` is the single gate SAP data passes through before touching MySQL; column names are loaded from `backend/config/sap_column_map.json`, never hardcoded.

External integrations, all called from the Services layer only:
| Integration | Client | Purpose |
|---|---|---|
| Google Drive API v3 | `google_drive_client.py` | Evidence photo storage (failure is non-fatal — see §5 FR-04) |
| Anthropic (Claude) API | `message_generator.py` | Auto-Touch draft message generation |
| LINE Messaging API | `line_client.py` | Auto-Touch message dispatch (channel 1) |
| SMTP (company Gmail) | `smtp_client.py` | Auto-Touch message dispatch (channel 2) — **replaced SendGrid** as of commit ~2026-07-23 |

Full visual diagrams (Use Case, ERD, Architecture, DFD Levels 0-2, Sequence, BPMN) live in `docs/diagrams/lumine_diagrams.drawio` (13 tabs) — this document is the prose companion to those diagrams, both independently verified against the same codebase on the same date.

---

## 4. Data Design

8 tables, verified field-by-field against `backend/app/models/*.py`:

| Table | Key Fields | Notes |
|---|---|---|
| `stores` | id PK, name | Only 2 fields — no timestamps |
| `staff` | id PK, employee_code UK, name, role, store_id FK, email UK, hashed_password, deleted_at | `deleted_at` = soft-delete for PDPA compliance |
| `customers` | customer_id PK (str), name, phone (PII), email (PII), line_id, language, **language_source** (`auto_detected`\|`manual_override`), do_not_contact, source (`crm_import`\|`manual_registration`\|`sap_only`), staff_id FK nullable | `language_source` is a real field not present in the diagram set's ER tab — should be backfilled there |
| `transactions` | idoc_number PK, posting_date, ean, material_desc, customer_id (SAP code, **not an enforced FK**), staff_id FK, sales_rep_name, customer_name (nullable, migration 0010), price (nullable, migration 0009), returned | `customer_id` intentionally not FK-enforced — registration is optional |
| `follow_up_tasks` | id PK, customer_id, idoc_number FK, task_type (T1\|T2\|T3), task_basis, due_date, calculated_from, status (Pending\|Done\|Superseded), skipped_until | `skipped_until` powers Auto-Touch's skip/defer flow |
| `evidence_logs` | id PK, task_id FK, notes, image_uri (nullable if Drive upload failed), image_size_kb, timestamp, staff_id FK | |
| `messages` | id PK, customer_id FK, staff_id FK, task_id FK nullable, touchpoint_type, message_text, channel_line, channel_email, status_line, status_email, sent_at | Auto-Touch's send-attempt log |
| `upload_logs` | id PK, store_id FK, staff_id FK, filename, uploaded_at, row_count, tasks_created, date_range_start/end, status | |

**Flag**: `backend/app/models/__init__.py`'s `__all__` only exports 6 of the 8 models (`Store` and `UploadLog` are defined but not listed there — imported directly elsewhere instead). Not a functional bug, but the models package's export list understates the real schema.

**Schema evolution** (11 migrations, linear chain, no branches):

| Rev | Change |
|---|---|
| 0001 | Initial schema |
| 0002 | Add `stores` table |
| 0003 | Replace placeholder store with real store locations |
| 0004 | Add `upload_logs` |
| 0005 | Add `transactions.sales_rep_name` |
| 0006 | Add `customers` table (unified customer record) |
| 0007 | Add `messages` table |
| 0008 | Add `follow_up_tasks.skipped_until` (Auto-Touch skip tracking) |
| 0009 | Add `transactions.price` / `returned` |
| 0010 | Add `transactions.customer_name` |
| 0011 | Index `follow_up_tasks.idoc_number` |

---

## 5. Functional Requirements

### FR-01 · SAP Data Processing
`POST /api/v1/upload` (`upload.py` → `sap_parser.py` → `transaction_repo` → `CycleReset`). Parses SAP CSV/Excel export, columns mapped via `sap_column_map.json` (Rule 7 — never hardcoded), filters rows to the uploader's own `employee_code`. Default (`force=false`) rejects on date-range overlap with a conflict response; `force=true` bypasses the check and upserts instead of inserting.

### FR-02 · Automated T1/T2/T3 Follow-up Scheduling
`task_scheduler.py`. Fixed offsets from `posting_date` only — T1 = +2 days, T2 = +14 days, T3 = +60 days. No weekend/holiday adjustment; due dates display as-is. `task_basis` is always `posting_date`, never "today."

### FR-03 · Cycle Reset Logic
`cycle_reset.py`. On a new purchase for an existing customer: supersede all their currently-Pending tasks first, *then* create a fresh T1/T2/T3 cycle from the new `posting_date`. Order is load-bearing — never both old and new Pending simultaneously.

### FR-04 · Evidence Logging
`POST /api/v1/evidence`, `PATCH /api/v1/evidence/{evidence_id}` (`evidence_service.py`). Photo ≤800KB / ≤1280px (client-compresses via `expo-image-manipulator`, server re-checks as a safety net), notes up to 2000 chars. **Google Drive upload failure is non-fatal by design** — the evidence record is still saved with `image_uri=null` rather than blocking the associate.

### FR-05 · Multi-Staff Data Isolation
Enforced per-endpoint, not globally:
| Endpoint pattern | sales_associate | store_manager |
|---|---|---|
| `GET /tasks`, `PATCH /tasks/{id}` | own tasks only (staff-scoped via `Transaction.staff_id`) | all tasks in own store |
| `GET /upload/history` | 403 (manager-only) | own store only |
| `GET/PATCH /evidence/{evidence_id}` | own evidence only | any evidence in own store |
| Auto-Touch endpoints | staff-scoped (own customers) | (not explicitly extended to manager view) |

### FR-06 · Customer Profile (store-wide exception)
`GET /customers/{id}`, `.../transactions`, `.../tasks`. **Deliberately store-wide for any role** — any staff member sees a customer's full purchase + follow-up history with all staff in their own `store_id`, never cross-store. Approved 2026-07-28 (CLAUDE.md). Identity response excludes phone/email/line_id (PII-restricted); 404 on customers with no transactions in the requester's store, to avoid a cross-store existence leak.

### FR-07 · Reports & KPI Dashboard *(not present in v4.1's FR list)*
`GET /reports/kpi`, `GET /reports/dashboard?period=today|week|month|all` (`report_service.py`, `dashboard_service.py`). `completion_rate = Done / (Pending + Done)`, Superseded tasks excluded from the denominator. `store_manager` sees a store-wide/per-staff breakdown; `sales_associate` sees a single own-row in the same response shape.

### FR-08 · Auto-Touch — AI-Assisted Follow-up *(not present in v4.1's FR list; the most substantial subsystem built since v4.1)*
5 endpoints (`auto_touch.py`, `auto_touch_service.py`):
1. `GET /auto-touch/today` — due-today list, excludes `do_not_contact` customers and actively `skipped_until` tasks, ordered overdue-first then T1→T2→T3.
2. `POST /auto-touch/generate-message` — drafts a message via Claude (`message_generator.py`); PDPA opt-out sentence is hardcoded into the system prompt, not JSON-editable; draft-only, never sends.
3. `POST /auto-touch/send/{customer_id}` — dispatches via LINE and/or email. **Gated by `AUTO_TOUCH_SEND_ENABLED`, checked before any DB lookup or dispatch** — an independent kill-switch on top of whatever credentials are configured. Marks the task Done only if at least one channel succeeds.
4. `POST /auto-touch/skip/{customer_id}` — defers `skipped_until` to tomorrow; task stays Pending.
5. `GET /auto-touch/status` — today's due/sent/pending/skipped counts.

Generate and send are **always two separate calls** — auto-send without human review is a permanent product rule, not a current limitation (per `docs/sprint1-backlog.md`).

### FR-09 · CRM Import & Customer Registration
`POST /customers/import-crm` (bulk Excel import, fixed columns — not SAP, no JSON column-map) and `POST /customers/register` (point-of-sale quick registration; register-not-upsert semantics, 409 if `customer_id` already exists).

### FR-10 · Barcode/QR Customer Identification
Mobile-only, no backend endpoint. `BarcodeScreen.tsx` renders a QR code encoding `customer_id` (via `react-native-qrcode-svg`) for a MOCCA iPad scan integration; works fully offline.

---

## 6. Non-Functional Requirements

### NFR-01 · Security & Authentication
JWT via `python-jose`, `HS256`, 60-minute access token / 7-day refresh token. `bcrypt` password hashing. `staff_id` is **always** read from the JWT server-side — never accepted from the request body (enforced convention, and explicitly documented in the mobile API client as a security note). Public endpoints (no JWT): `POST /auth/login`, `/auth/register`, `/auth/refresh`, `GET /stores`, `GET /health`.

**Known gap, not yet reconciled with any approval record**: `GET /evidence/{task_id}` has no ownership or store scoping in the router — any authenticated staff member can fetch any task's evidence by ID. This differs from the Customer Profile exception (which *is* documented and approved) — this one has no such record. Flagged for architect review.

### NFR-02 · PDPA / PII Compliance
Customer `phone`, `email`, `line_id` are PII — never logged, never in JWT claims or URL params. `customer_id` and customer **name** are not treated as PII (name storage confirmed intentional 2026-07-26). `do_not_contact` is enforced in the repository WHERE clause only, never left to router/service logic. Staff soft-delete (`deleted_at`) supports right-to-erasure-adjacent handling without losing referential integrity on historical transactions.

### NFR-03 · Performance
`follow_up_tasks.idoc_number` indexed (migration 0011) after a production incident where its absence made every `GET /tasks` call materially heavier. `transactions.idoc_number`, `posting_date`, `customer_id` indexed; FK columns generally indexed.

### NFR-04 · Usability
Light theme only (`mobile/src/styles/theme.ts`, single source of truth); dark theme explicitly retired, "never re-introduce dark values."

**Non-conformance found**: 10 files still contain raw hex color literals despite the "always use THEME tokens" rule — `LoginScreen.tsx`, `UploadScreen.tsx`, `UploadHistoryScreen.tsx` are almost entirely un-migrated; `EvidenceForm.tsx`, `EvidenceScreen.tsx`, `TaskCard.tsx`, `OfflineBanner.tsx`, `RegisterScreen.tsx`, `BarcodeScreen.tsx`, `BarcodeDisplay.tsx` have one or two leftover literals each. Additionally, `app.json`'s splash screen and Android adaptive icon background (`#1a1a2e`, dark navy) contradicts the "dark retired" rule — likely a pre-migration leftover in native config, outside `theme.ts`'s reach.

### NFR-05 · Offline Behavior
Read-only cache only (`offlineCache.ts`, AsyncStorage-backed, tasks list only) — Dashboard falls back to cached tasks on network failure. **No offline write queue**: evidence upload, SAP upload, mark-Done, and all Auto-Touch actions require a live connection; nothing is queued for later sync. Network error vs. server error are deliberately distinguished throughout the app (silent cache fallback for the former, explicit error message for the latter) to avoid a misleading empty state.

### NFR-06 · Send-Gate Safety (Auto-Touch)
`AUTO_TOUCH_SEND_ENABLED` (default `false`) is a config-level kill-switch, independent of whether LINE/SMTP credentials are configured — checked first, before any DB lookup or dispatch. Currently **off in production**; the mobile app's Auto-Touch detail screen only offers manual Copy/Share of the AI draft, and never calls the send endpoint while this flag is off.

---

## 7. API Contract

`openapi.yaml` (repo root) — `openapi: 3.0.0`, `title: Lumine CRM API`, `version: 1.0.0`. **24 paths, 36 component schemas** (both counts verified by direct grep against the file, 2026-08-17). This file is the single source of truth for field names — CLAUDE.md rule: never rename a field, never add a field not in `openapi.yaml` without architect approval.

---

## 8. Mobile Application

### 8.1 Screens (14) and Navigation
Single flat native stack (`@react-navigation/native-stack`) — **no drawer or tab navigation library installed**; the "hamburger drawer" UI (`AppDrawer.tsx`) is a hand-rolled `Modal` + `Animated` component, not `@react-navigation/drawer`. `headerShown: false` globally — every screen implements its own header. Auth gating is by initial-route decision (token present → Dashboard, else → Login) plus backend 401/403 enforcement, not per-route guards.

| Screen | Purpose |
|---|---|
| LoginScreen | Email/password login |
| RegisterScreen | Self-registration (role always forced to `sales_associate` server-side) |
| DashboardScreen | Today's task list — home screen |
| TaskDetailScreen | Single task detail + mark-Done |
| EvidenceScreen | Submit evidence (photo + notes) |
| EvidenceDetailScreen | View/edit evidence on a completed task |
| CompletedTasksScreen | Done-task history |
| BarcodeScreen | Customer QR code display |
| UploadScreen | SAP file upload |
| UploadHistoryScreen | Upload log (manager-only) |
| FollowUpDashboardScreen | KPI/report dashboard with PDF export |
| AutoTouchScreen | Today's Auto-Touch queue |
| AutoTouchDetailScreen | Draft/edit/send AI-generated message |
| CustomerProfileScreen | Customer 360 view (purchases + follow-ups) |

### 8.2 State Management
No global store (no Redux/Zustand/MobX/Context for app state) — 100% local `useState` + direct API calls. Three documented "laws" govern cross-screen data freshness:
- **Law 1 — Pull on Focus**: `useFocusEffect` refetches on every screen foreground.
- **Law 2 — Optimistic Update with Rollback**: mutations (e.g. mark-Done) update the UI immediately, roll back + show an Alert on failure.
- **Law 3 — No Real-Time**: no WebSockets/data polling; all data changes are user-triggered. (The one UI-only exception: `OfflineBanner` polls network state every 5s, a local convenience, not app data sync.)

### 8.3 Auth Token Handling
JWT stored in `AsyncStorage`; axios request interceptor attaches `Authorization: Bearer <token>` on every call. Response interceptor catches 401, calls `/auth/refresh`, retries the original request once; concurrent 401s share one in-flight refresh promise. On refresh failure, tokens are cleared and a `logout` event fires, which the navigator listens for to reset to Login.

---

## 9. Testing & Quality

- **33 test files, 331 test functions** (both counts verified by direct search, 2026-08-17) — matches CLAUDE.md's "331/331 backend tests pass" claim exactly.
- **No coverage config is committed anywhere in `backend/`** (no `pytest.ini`, `pyproject.toml`, `.coveragerc`) — the `--cov=` target/threshold is passed at the CLI, not repo-enforced. CLAUDE.md's "100% coverage on backend/app/services/" claim is dated 2026-07-29 — **~3 weeks stale as of this document** and not independently re-verified this session (per instructions, the suite was not re-run).
- Run via `backend/venv/bin/pytest` or `.venv/bin/pytest` **only** — bare `pytest` resolves to system Python 3.12, missing `pandas`.
- Stale artifact: `tests/__pycache__/test_sendgrid_client.*.pyc` exists with no corresponding source file — a SendGrid→SMTP migration leftover, not a real test.

---

## 10. Deployment & Operations

- **Render**: manual dashboard configuration, no `render.yaml`/IaC. **Confirmed operational gap**: Render's deploy does not auto-run `alembic upgrade head`. A real production incident (2026-08-15) occurred because migration 0010 was merged but never applied to production TiDB — `GET /tasks` failed on every single call until the migration was applied manually. `alembic current` should be checked against production after every migration merge.
- **TiDB Cloud**: free tier, MySQL-wire-protocol compatible.
- **No CI/CD pipeline** — no `.github/workflows/` for this repo; tests, lint, and deploys are all manual.
- **Mobile release**: EAS Build → Android APK. `app.json`'s `expo.version` + `expo.android.versionCode` are the authoritative version source (per CLAUDE.md). Current: `1.5.1` / versionCode `8`. **Git tags lag behind** — latest tag is `v1.5.0`, with `v1.5.1` shipped via commit but not tagged. `package.json`'s own `"version": "1.0.0"` field is unrelated and not kept in sync — do not use it as a version reference.

---

## 11. Known Limitations / Technical Debt

All items below are code-verified, not speculative:

1. **`GET /evidence/{task_id}` lacks ownership/store scoping** — any authenticated staff can fetch any task's evidence by ID. No documented approval on record (unlike the Customer Profile exception). Needs an architect decision.
2. **Theme non-conformance** — 10 files with raw hex colors; dark splash/icon color leftover in `app.json` contradicts the "dark retired" rule.
3. **`package.json` (1.0.0) vs `app.json` (1.5.1)** version drift — use `app.json` as authoritative.
4. **`GOOGLE_DRIVE_CREDENTIALS_FILE`** (defined in `config.py`'s `Settings` class) is dead config — the actual runtime code reads `GOOGLE_DRIVE_CREDENTIALS_PATH` directly via `os.environ`, bypassing `settings` entirely.
5. **`auto_touch.py` docstring says "6 endpoints"** — only 5 are implemented. Minor doc/code mismatch.
6. **No committed test-coverage configuration** — the "100% coverage on services/" figure is a manually-recorded, unenforced claim, last verified 2026-07-29.
7. **No CI/CD pipeline** for this repo.
8. **Auto-Touch send is fully built but disabled in production** (`AUTO_TOUCH_SEND_ENABLED=false`) — mobile currently only supports manual Copy/Share of AI drafts, not automated dispatch.
9. **Git tags lag the real mobile version** by one patch release (`v1.5.0` tagged, `v1.5.1` shipped untagged).
10. **`docs/arch-sprint1-decisions.md` is stale** on env vars — still lists `SENDGRID_API_KEY`, superseded by the SMTP variable set.
11. **13 open GitHub issues** (`PiriyaLapa/project-lumine`), notably: #26 (Maestro↔emulator WSL2 networking), #19 (Auto-Touch draft content unverified live pending `ANTHROPIC_API_KEY`), #14 (customer email backfill), #2 (Auto-Touch integration test QA-6 still unwritten), #28 (no re-adding evidence after a task is marked Done).

---

## 12. Appendix

**Diagram cross-reference**: `docs/diagrams/lumine_diagrams.drawio` — 13 tabs: Use Case, ER Diagram, Sequence - Lumine, Sequence - Auto-Touch, Architecture, DFD Level 0/1, DFD Level 2 ×5 (one per feature), BPMN. Both this document and that file were independently built and verified against the live codebase on 2026-08-17.

**Sample data**: `docs/samples/customer_master_extracted.xlsx` (CRM export sample), `docs/samples/sap-sample.xlsx` (SAP transaction export sample).

**Glossary**: see §1.3.
