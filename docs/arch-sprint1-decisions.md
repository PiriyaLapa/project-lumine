# Architecture Decisions — Auto-Touch Sprint 1
**Date**: 2026-05-31  
**Architect**: Lumine Architect Agent  
**Status**: APPROVED — Developer may proceed

---

## ARCH-1: Endpoint Versioning ✅

All 8 new endpoints use `/api/v1/` prefix. Consistent with all existing endpoints.

```
/api/v1/customers/import-crm
/api/v1/customers/register
/api/v1/auto-touch/today
/api/v1/auto-touch/generate-message
/api/v1/auto-touch/send/{customer_id}
/api/v1/auto-touch/skip/{customer_id}
/api/v1/auto-touch/status
/api/v1/utils/parse-sap-product
```

All 8 require Bearer JWT. No new public endpoints.

---

## ARCH-2: Unified Customer Record — Migration 0006 ✅

### Decision: New `customers` table (not columns on existing tables)

**Rationale**: Customer contact data is orthogonal to transactions and tasks. Adding phone/email to the `transactions` table would repeat data per line item (SAP exports one row per item). A dedicated `customers` table with `customer_id` as the primary key is the correct join pattern.

**Join key**: `customer_id` (string, VARCHAR 50) — matches the `customer_id` field already stored in the `transactions` table. This is the SAP customer identifier. The join is:
```sql
transactions.customer_id = customers.customer_id
```

### Migration 0006 — `customers` table

```sql
CREATE TABLE customers (
    customer_id     VARCHAR(50)     NOT NULL PRIMARY KEY,
    name            VARCHAR(255)    NOT NULL,
    phone           VARCHAR(20)     NULL,
    email           VARCHAR(255)    NULL,
    line_id         VARCHAR(100)    NULL,
    language        VARCHAR(5)      NOT NULL DEFAULT 'th',
    language_source VARCHAR(20)     NOT NULL DEFAULT 'auto_detected',
    do_not_contact  BOOLEAN         NOT NULL DEFAULT FALSE,
    source          VARCHAR(30)     NOT NULL DEFAULT 'crm_import',
    staff_id        INT             NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                             ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_staff_id (staff_id),
    INDEX idx_do_not_contact (do_not_contact)
);
```

**Field rules (LOCKED):**
- `customer_id` — VARCHAR(50), matches SAP format. Float strings (e.g. "67913358.0") normalized to "67913358" at import time by the existing `_normalize_numeric_str` utility.
- `phone` and `email` — nullable. PII. Must never appear in any log line.
- `line_id` — nullable. NULL until Sprint 2 auto-matching.
- `language` — enum('th', 'en'). Default 'th'. Auto-detected at record creation.
- `language_source` — enum('auto_detected', 'manual_override'). Tracks how language was set.
- `do_not_contact` — enforced in `customer_repo.py` WHERE clause. NEVER filtered in router or service. Any query that reads customers for Auto-Touch must include `WHERE do_not_contact = FALSE`.
- `staff_id` — which associate registered/imported this customer. FK to `staff.id` (nullable — SAP-only customers have no registering staff).
- `source` — enum('crm_import', 'manual_registration', 'sap_only'). `sap_only` = customer_id seen in SAP but no contact info yet.

### Auto-join on SAP upload (existing upload flow, no code change needed)

When `POST /api/v1/upload` runs and a `customer_id` from SAP is not in the `customers` table, the upload service does NOT need to create a customer record. The `transactions` table already stores `customer_id` as a string. The Auto-Touch today-list query joins `transactions → follow_up_tasks → customers` at query time. If no `customers` row exists, the customer appears in the today list with `channels_available: {email: false, line: false}` and a "contact info missing" warning.

---

## ARCH-4: Messages/Delivery Log — Migration 0007 ✅

### Decision: New `messages` table

Tracks every Auto-Touch send attempt with delivery status per channel.

### Migration 0007 — `messages` table

```sql
CREATE TABLE messages (
    id              INT             NOT NULL AUTO_INCREMENT PRIMARY KEY,
    customer_id     VARCHAR(50)     NOT NULL,
    staff_id        INT             NOT NULL,
    task_id         INT             NULL,
    touchpoint_type VARCHAR(5)      NULL,
    message_text    TEXT            NOT NULL,
    channel_line    BOOLEAN         NOT NULL DEFAULT FALSE,
    channel_email   BOOLEAN         NOT NULL DEFAULT FALSE,
    status_line     VARCHAR(20)     NULL,
    status_email    VARCHAR(20)     NULL,
    sent_at         DATETIME        NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customer_id (customer_id),
    INDEX idx_staff_id (staff_id),
    INDEX idx_task_id (task_id)
);
```

**Field rules:**
- `task_id` — nullable FK to `follow_up_tasks.id`. NULL is reserved for future non-task-triggered messages (Phase 3). Sprint 1: always set.
- `touchpoint_type` — denormalized copy of `task_type` for query convenience without join.
- `status_line` / `status_email` — enum: 'sent' | 'failed' | 'not_available' | NULL. NULL = channel not attempted.
- `message_text` — the final message as actually sent (not the AI draft — the associate's possibly-edited version).

---

## ARCH-5: SAP Product Parser Architecture ✅

### Decision: Standalone service file, also exposed as utility endpoint

**File**: `backend/app/services/sap_product_parser.py`

**Rationale**: Separating it from `sap_parser.py` is correct. The existing `sap_parser.py` handles column mapping and data extraction from SAP files. The new parser handles product *name cleanup* — a display concern, not a data-ingestion concern. They serve different layers.

**Call pattern**:
- Internal: `auto_touch_service.py` calls `parse_product_name(product_raw)` directly (no HTTP round-trip)
- External: `POST /api/v1/utils/parse-sap-product` for testing and debugging

**Parsing function signature**:
```python
def parse_product_name(product_raw: str) -> dict:
    """
    Returns: {
        "product_raw": str,
        "product_clean": str,
        "category": str | None,
        "size": str | None
    }
    """
```

**Returned items rule**: items where `returned = True` in SAP are excluded from message context by `auto_touch_service.py` before calling the parser. The parser itself is stateless and does not know about return status.

---

## Key Architectural Decision: Send = Mark Task Done

### Decision: `POST /api/v1/auto-touch/send/{customer_id}` marks the linked FollowUpTask as Done automatically.

**Rationale**: Sending the message IS the customer contact. In the manual flow, the associate contacts the customer then marks Done. In Auto-Touch, the send is the contact — there is no separate "mark done" step. Requiring the associate to tap Send and then separately tap Done creates friction that violates the product's simplicity principle.

**Implementation**:
- `auto_touch_service.send_message()` calls `task_repo.update_status(task_id, "Done")` on successful delivery (at least one channel sends)
- If ALL channels fail, the task is NOT marked Done — it remains Pending in both the tasks list and the Auto-Touch list
- Partial delivery (one of two channels sends) → task IS marked Done (message was delivered)

**Impact on `GET /api/v1/tasks`**: tasks marked Done via Auto-Touch will appear as Done in the regular tasks view. This is correct behaviour — no inconsistency.

---

## Repository Pattern for New Code (LOCKED)

All new code must follow the existing call chain:

```
Router → Service → Repository → MySQL
```

New files:
```
repositories/
  customer_repo.py        ← all customers table queries
  auto_touch_repo.py      ← today list, skip, status queries; messages table writes

services/
  language_detection.py   ← pure function, no DB dependency
  sap_product_parser.py   ← pure function, no DB dependency
  crm_import_service.py   ← calls customer_repo
  customer_register_service.py ← calls customer_repo + language_detection
  message_generator.py    ← calls Claude API (external); no DB dependency
  line_client.py          ← calls LINE Messaging API (external); no DB dependency
  sendgrid_client.py      ← calls SendGrid API (external); no DB dependency
  auto_touch_service.py   ← orchestrator; calls auto_touch_repo + message_generator
                             + line_client + sendgrid_client + task_repo (for Done update)

routers/
  customers.py            ← import-crm + register
  auto_touch.py           ← today + generate-message + send + skip + status
  utils.py                ← parse-sap-product
```

**Rule**: `message_generator.py`, `line_client.py`, and `sendgrid_client.py` must never import `Session`. They are pure service clients. All DB interaction goes through repositories.

---

## PII Handling Rules (New Fields)

`phone` and `email` on the `customers` table are PII under Thailand PDPA.

**Enforced by Architect:**
- Never log phone or email at any level (DEBUG, INFO, WARNING, ERROR)
- Never include phone or email in JWT claims
- Never include phone or email in URL path parameters
- Error messages must not echo phone or email back in responses
- `customer_id` (opaque SAP ID) is safe to log — it is not personally identifiable

---

## Environment Variables Required (New)

DevOps must add before any backend deployment:

```
ANTHROPIC_API_KEY=sk-ant-...
SENDGRID_API_KEY=SG....
LINE_CHANNEL_ACCESS_TOKEN=...
```

All three are required at startup. If any is missing when `auto_touch_service` is imported, raise `RuntimeError` — same pattern as existing `SECRET_KEY` guard.

---

## What Requires Architect Re-Approval Before Build

- Any change to the `customers` table schema beyond what is defined in Migration 0006
- Any change to field names in `Customer`, `AutoTouchCustomer`, `SendMessageRequest`, or `SendMessageResponse` schemas
- Any new endpoint not listed in the 8 above
- Any decision to store phone, email, or line_id in a table other than `customers`
- Any proposal to auto-send without associate approval
