# Lumine Auto-Touch — Sprint 1 Backlog
**Version**: 1.0 | **Date**: 2026-05-30 | **Duration**: 2 weeks (10 days)

**Sprint goal**: Associate opens app → sees today's list → taps customer → reads AI draft → taps Send. 30 seconds. Zero writing.

Full plan: `wiki/queries/lumine-autotouch-sprint1-plan.md` in SecondBrain.

---

## Pre-Sprint Gate — BLOCKING

Nothing starts until all 5 are done.

| # | Action | Owner | Done? |
|---|--------|-------|-------|
| 1 | CRM Excel export from CRM team (Sales Rep ID 50847) | Benz | ⬜ |
| 2 | LINE OA Channel Access Token confirmed accessible | Benz | ⬜ |
| 3 | SendGrid account created (free tier) | Benz | ⬜ |
| 4 | Stage 5 gate confirmed closed | Benz | ✅ 2026-05-31 |
| 5 | `openapi.yaml` updated with all 8 new endpoints (`/api/v1/` prefix) | Architect | ✅ 2026-05-31 |

---

## Backlog by Agent

### 🏛 Architect (Days 1–2)

- [x] **ARCH-1** Fix endpoint versioning — all 8 confirmed `/api/v1/` ✅
- [x] **ARCH-2** Design unified customer table schema — Migration 0006 schema defined ✅
- [x] **ARCH-3** Add all 8 endpoints to `openapi.yaml` ✅
- [x] **ARCH-4** Design messages/delivery log table — Migration 0007 schema defined ✅
- [x] **ARCH-5** SAP product parser approved as standalone service `sap_product_parser.py` ✅

### 🔬 QA (Days 1–3, RED tests before Developer writes code)

- [ ] **QA-1** `test_sap_product_parser.py` — 7 cases including returned item exclusion
- [ ] **QA-2** `test_crm_import.py` — valid, missing column, duplicate, new, conflict
- [ ] **QA-3** `test_customer_register.py` — valid, missing field, language detection (5 name types)
- [ ] **QA-4** `test_auto_touch.py` — today list, generate, send, skip, do_not_contact excluded
- [ ] **QA-5** `test_language_detection.py` — 10 name cases
- [ ] **QA-6** `test_auto_touch_integration.py` — full E2E flow

### 🎨 UX/UI (Days 1–3)

- [ ] **UI-1** `agents/specs/auto-touch-tab.md`
- [ ] **UI-2** `agents/specs/today-list-screen.md`
- [ ] **UI-3** `agents/specs/customer-message-screen.md`
- [ ] **UI-4** `agents/specs/new-customer-screen.md`

### 🔒 Security (Days 2–3 review + Day 9 gate)

- [ ] **SEC-1** JWT required on all 8 new endpoints — verify
- [ ] **SEC-2** Phone + email never in logs, URLs, or JWT
- [ ] **SEC-3** `do_not_contact` enforced in repository WHERE clause
- [ ] **SEC-4** API key storage: ANTHROPIC_API_KEY, SENDGRID_API_KEY, LINE_CHANNEL_ACCESS_TOKEN
- [ ] **SEC-5** PDPA opt-out in system prompt (not user prompt — non-bypassable)
- [ ] **SEC-6** Final checklist Day 9

### ⚙️ DevOps (Days 3–4 + Day 8)

- [~] **OPS-1** Add 3 new env vars to Render + `.env.example` — `.env.example` + `config.py` updated ✅ · Render dashboard: waiting for credentials from Benz
- [ ] **OPS-2** Apply Migration 0006 to TiDB Cloud
- [ ] **OPS-3** Apply Migration 0007 to TiDB Cloud
- [ ] **OPS-4** Verify `alembic current` = head
- [ ] **OPS-5** Deploy merged develop to Render
- [ ] **OPS-6** Smoke test all 8 endpoints on production URL
- [ ] **OPS-7** Update EAS secrets if new mobile env vars needed

### 💻 Developer (Days 3–10, STRICT ORDER)

**Backend — Week 1:**

- [ ] **DEV-1** `0006_unified_customer.py` migration
- [ ] **DEV-2** `0007_messages.py` migration
- [ ] **DEV-3** `services/sap_product_parser.py` — strip rules + category map + returned flag
- [ ] **DEV-4** Router `POST /api/v1/utils/parse-sap-product`
- [ ] **DEV-5** `repositories/customer_repo.py` — CRUD for new columns
- [ ] **DEV-6** `services/language_detection.py` — Thai Unicode + romanization + English default
- [ ] **DEV-7** `services/crm_import_service.py` — parse, match, update/create, flag conflicts
- [ ] **DEV-8** Router `POST /api/v1/customers/import-crm`
- [ ] **DEV-9** `services/customer_register_service.py`
- [ ] **DEV-10** Router `POST /api/v1/customers/register`
- [ ] **DEV-11** `repositories/auto_touch_repo.py` — today list, status update, skip
- [ ] **DEV-12** `services/message_generator.py` — Claude API, bilingual system prompt, PDPA hardcoded
- [ ] **DEV-13** `services/line_client.py` — LINE Messaging API push message
- [ ] **DEV-14** `services/sendgrid_client.py` — SendGrid send
- [ ] **DEV-15** `services/auto_touch_service.py` — orchestrates 11–14
- [ ] **DEV-16** `routers/auto_touch.py` — all 6 auto-touch routes

**Mobile — Week 2:**

- [ ] **DEV-17** `AppNavigator.tsx` — add Auto-Touch tab with pending badge
- [ ] **DEV-18** `screens/TodayListScreen.tsx`
- [ ] **DEV-19** `screens/CustomerMessageScreen.tsx` — AI draft + edit + send + skip
- [ ] **DEV-20** `screens/NewCustomerScreen.tsx` — 4-field form, 30s target
- [ ] **DEV-21** `api/client.ts` — add auto-touch + customer endpoints
- [ ] **DEV-22** Language flag toggle in CustomerMessageScreen

---

## New Files Summary

### Backend
```
backend/app/
├── services/
│   ├── sap_product_parser.py      ← NEW
│   ├── language_detection.py      ← NEW
│   ├── crm_import_service.py      ← NEW
│   ├── customer_register_service.py ← NEW
│   ├── message_generator.py       ← NEW (Claude API)
│   ├── line_client.py             ← NEW
│   └── sendgrid_client.py         ← NEW
│   └── auto_touch_service.py      ← NEW
├── repositories/
│   ├── customer_repo.py           ← EXTEND (new columns)
│   └── auto_touch_repo.py         ← NEW
├── routers/
│   ├── customers.py               ← NEW
│   ├── auto_touch.py              ← NEW
│   └── utils.py                   ← NEW
alembic/versions/
├── 0006_unified_customer.py       ← NEW
└── 0007_messages.py               ← NEW
tests/
├── test_sap_product_parser.py     ← NEW
├── test_crm_import.py             ← NEW
├── test_customer_register.py      ← NEW
├── test_auto_touch.py             ← NEW
├── test_language_detection.py     ← NEW
└── test_auto_touch_integration.py ← NEW
```

### Mobile
```
mobile/src/screens/
├── TodayListScreen.tsx            ← NEW
├── CustomerMessageScreen.tsx      ← NEW
└── NewCustomerScreen.tsx          ← NEW
navigation/AppNavigator.tsx        ← EXTEND (new tab)
api/client.ts                      ← EXTEND (new endpoints)
```

---

## New Endpoints (all require JWT)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/customers/import-crm` | Bulk CRM Excel import |
| POST | `/api/v1/customers/register` | Quick customer registration |
| GET | `/api/v1/auto-touch/today` | Today's contact list |
| POST | `/api/v1/auto-touch/generate-message` | Claude API draft |
| POST | `/api/v1/auto-touch/send/{customer_id}` | Send LINE + Email |
| POST | `/api/v1/auto-touch/skip/{customer_id}` | Defer to tomorrow |
| GET | `/api/v1/auto-touch/status` | Sent/pending/skipped counts |
| POST | `/api/v1/utils/parse-sap-product` | SAP code → readable name |

---

## Definition of Done (19 items)

See `wiki/queries/lumine-autotouch-sprint1-plan.md` for full checklist.
Summary: CRM import ✓ · registration ✓ · parser ✓ · join works ✓ · today list ✓ · draft never blank ✓ · edit ✓ · send ✓ · status ✓ · skip ✓ · Thai/English ✓ · manual override ✓ · PDPA opt-out ✓ · 5 customers in <3 min ✓

---

## PM Rules (non-negotiable)

1. No confirmation dialogs on Send
2. Draft always pre-populated — never blank on screen
3. Auto-send without approval is **permanently excluded**
