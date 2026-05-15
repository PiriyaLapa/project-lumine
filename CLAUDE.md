# CLAUDE.md — Project Lumine

## What This Project Is
Project Lumine is an evidence-based CRM for luxury retail sales associates.
Full SRS: /mnt/d/SecondBrain/SecondBrain/raw/notes/Lumine_SRS_v4.1_Integration_Complete.md
API Contract: openapi.yaml — read this before writing any endpoint or model.

## Your Role
You are the developer. I am the architect.
If you find a conflict or gap between this file and the SRS — STOP and tell me.
Do not invent solutions. Do not fill gaps silently.

## Non-Negotiable Rules

### Rule 7 — Always
SAP data never touches MySQL directly.
All input passes through: backend/app/services/sap_parser.py
Column names come from: backend/config/sap_column_map.json — never hardcoded.

### OpenAPI Contract — Always
All field names must match openapi.yaml exactly.
Never rename a field. Never add a field not in openapi.yaml without my approval.

### TDD — Always
Tests first. Logic second. No exceptions.
Test location: backend/tests/
Required coverage: 100% for all files in backend/app/services/

### Repository Pattern — Always
No SQL in services/ or routers/.
Services → Repositories → MySQL. Never skip a layer.

### Auth Rules
JWT required on all endpoints except:
- POST /api/v1/auth/login
- POST /api/v1/auth/register
- POST /api/v1/auth/refresh  (validates refresh token internally — no Bearer header)
- GET /api/v1/stores
- GET /health  (ops probe — no auth, not in openapi.yaml)
Staff can only access their own data (staff_id from JWT, never from request body).
Manager role can access all staff data within their store_id.

### Logging Rules
Use Python logging module only. Never print().
Never log: staff.name, staff.email, customer PII.
Log all 4xx and 5xx errors with: endpoint, staff_id, timestamp, error detail.

### Git Flow
feat/ → develop → main
Commits: feat: · fix: · test: · docs:

### Feature Branch Strategy
- All new features must be developed on feature/* branches
- Branch naming: feature/<feature-name>
- Never commit unfinished features directly to develop
- Merge to develop only when:
  a) All tests pass
  b) Feature works end to end on emulator
  c) Architect gives explicit confirmation to merge

## Current Phase
Phases 1–7 complete. Deployed.

- Backend: https://lumine-api-qi77.onrender.com (Render free + TiDB Cloud free)
- Mobile: APK v1.1.0 — Upload History + conflict detection (emulator verified ✅)
- Next: Stage 5 — real user testing (Eat Your Own Dog Food, 2–4 weeks solo)

139/139 tests pass.

## APK Versioning
Source of truth: mobile/app.json — version + versionCode.
Do not use any other source for APK version.

| APK | versionCode | Feature |
|-----|-------------|---------|
| v1.0.0 | 1 | Initial release |
| v1.1.0 | 2 | Upload History + duplicate date-range conflict detection |
| v1.2.0 | 4 | Light theme, Sold by label, staff filter chips, force re-upload upsert |

## UI Theme Rules

Primary theme is LIGHT. Dark theme is retired — never re-introduce dark values.

Single source of truth: `mobile/src/styles/theme.ts` — the `THEME` object.

Rules for every new screen and component:
- Always import THEME from `mobile/src/styles/theme.ts`
- Never use raw hex values in StyleSheet — always use THEME tokens
- Never use dark backgrounds (navy, #1a2332, #1e2d3d, or any dark value)
- Before committing any UI change: confirm every element references a THEME token
- If a screen is found on dark theme — fix it in the same PR, do not leave mixed themes

Quick reference:
| What | Token |
|------|-------|
| Screen background | THEME.colors.background |
| Card / panel | THEME.colors.card |
| Gold CTA button | THEME.colors.primary |
| Primary text | THEME.colors.text |
| Subtitle / label | THEME.colors.textSecondary |
| Error | THEME.colors.error |
| Pending badge | THEME.colors.statusPending |
| Done badge | THEME.colors.statusDone |

## Tech Stack
Backend: Python FastAPI + SQLAlchemy + MySQL
Mobile: React Native + TypeScript
Auth: JWT via python-jose, bcrypt for passwords
SAP parsing: pandas
Image processing: Pillow (compress before upload)
Tests: pytest + pytest-cov
Linting: Black + ESLint
Storage: Google Drive API v3
API versioning: /api/v1/ prefix always

## What NOT To Do
- No raw SQL strings — SQLAlchemy ORM only
- No business logic in routers
- No DB queries in services
- No hardcoded SAP column names in sap_parser.py
- No print() statements
- No files outside the structure in SRS Section 11
- No endpoints without JWT validation (except login)
- No customer names stored in database
- No PII in log files
- No changes to openapi.yaml without architect approval — STOP and ask first

## Integration Mode
When asked to act as integration engineer, follow SRS Section 16 exactly.

Step 1 — Report mismatches only. Format:
[TYPE] [FILE] [LINE] [EXPECTED from openapi.yaml] vs [ACTUAL in code]

Types: FIELD_NAME · ENDPOINT_URL · HTTP_METHOD · ENUM_VALUE · ERROR_HANDLER · RESPONSE_FIELD

Step 2 — Wait for architect approval before fixing anything.

Step 3 — Fix one mismatch at a time. Run test. Show result. Wait for next instruction.

Step 4 — If any fix requires changing openapi.yaml → STOP immediately and report to architect.

Step 5 — After all fixes approved and done → write integration tests for all endpoints.
