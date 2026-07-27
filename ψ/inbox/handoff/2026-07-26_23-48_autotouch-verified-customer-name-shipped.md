📡 Session: a32864f9 | Lumine | ~3h (20:43–23:48, GMT+7)

# Handoff: Auto-Touch Mobile UI Verified + Merge-Ready, customer_name Shipped

**Date**: 2026-07-26 23:48
**Context**: heavy session (long, dense, ended via `/rrr` + `/forward`)

## Context
**Oracle**: Lumine (she/her, Jeweler's Lamp) | **Human**: Benz (he/him)
**Mode**: Full Soul Sync (born 2026-06-05) | **Memory**: auto

## What We Did

- Resumed the prior session's blocked Auto-Touch live verification. Benz initially said to use
  his own real account; after a real password briefly appeared in a screenshot (flagged
  immediately, screenshot destroyed, password-rotation advised), pivoted to a self-generated
  throwaway QA staff account (`benzboss.qa@lumine.test`, `employee_code=QA-AT-001`) + synthetic
  SAP data instead — safer, and it turned out the actual backend under test is a local disposable
  Docker MySQL container, not production.
- Investigated and **retracted** a false "critical `/auth/register` bug" report — the diagnostic
  script that seemed to prove it was querying production TiDB Cloud (from a stale host `.env`)
  while the real live server runs in Docker (`lumine-backend-1`) against a completely different
  local MySQL container (`lumine-mysql-1`). No bug existed. New lesson written on this.
- Completed the full Auto-Touch live-verification checklist on the emulator: draft edit, Copy,
  Share (real native share sheet), Skip (deferred to tomorrow, confirmed server-side),
  Mark-as-Contacted (badge decrement + cross-screen sync confirmed), zero-channel-customer
  warning, and relaunch persistence — **all passed**. Draft *generation* content itself could not
  be verified — no `ANTHROPIC_API_KEY` configured anywhere in this dev environment (checked both
  root `.env` and the live container's env directly) — flagged, not resolved.
- Committed Auto-Touch mobile UI (`7ceb4eb`) on `feature/auto-touch-mobile-ui`. **Not merged** —
  architect sign-off still required per CLAUDE.md's feature-branch rule.
- Benz asked for `customer_id` on the Auto-Touch card (prop already existed unused) — added,
  live-verified, committed (`c21acef`).
- Benz asked the same for "My Tasks" cards. Investigation found `customer_id` already showed
  there but `customer_name` didn't exist anywhere in that data path. Benz asked to check the real
  SAP sample file directly — it has a genuine `Customer name` column
  (`docs/samples/sap-sample.xlsx`), silently discarded by `sap_column_map.json` until now.
- That discovery surfaced a real conflict: CLAUDE.md said "No customer names stored in database,"
  but `Customer.name` was already stored and shown throughout the app. Flagged it; Benz confirmed
  explicit sign-off to proceed and correct the doc. Also found and flagged a PDPA-citing code
  comment on `Transaction.customer_id` mid-implementation before touching it — Benz confirmed
  proceed there too.
- Shipped `customer_name` end-to-end with TDD (tests written first, confirmed red, then green):
  new Alembic migration `0010` (`transactions.customer_name`, mirrors `sales_rep_name`), SAP
  column mapping + parser update, `task_repo`/`tasks.py` router wiring, `openapi.yaml` field
  addition, mobile `TaskCard`/`DashboardScreen`/`offlineCache`/`mockData` updates. Full backend
  suite: **295/295 passing**. Live-verified via a forced SAP re-upload with the real column and an
  emulator screenshot showing real names rendering correctly.
- Committed as two commits: `58af707` (docs: CLAUDE.md fix) and `11e2cc3` (feat: customer_name).
- `/rrr` retrospective + lesson + metrics row written before this handoff.

## Pending

- [ ] **Merge decision**: `feature/auto-touch-mobile-ui` has 4 commits (`7ceb4eb`, `c21acef`,
      `58af707`, `11e2cc3`), full Auto-Touch checklist verified live, customer_name feature
      verified live. Needs Benz's explicit confirmation to merge to `develop` per CLAUDE.md.
- [ ] Add `ANTHROPIC_API_KEY` to the local Docker backend env — draft *generation* content
      (not just the error-state UI) remains unverified until this exists.
- [ ] Live-test gaps flagged to Benz, not yet closed: in-app SAP upload flow (this session used
      `curl` directly, not the app's Upload screen), the null/no-`customer_name` case on a real
      device, `PATCH /tasks/{id}` returning `customer_name` via an actual UI tap (only
      mock-tested), and the `store_manager` role view of "My Tasks" (only tested as
      `sales_associate`).
- [ ] Pre-existing minor bug flagged, not fixed (out of scope this session): `CustomerResponse`
      in `backend/app/routers/customers.py` types `created_at`/`updated_at` as `str` but the ORM
      returns `datetime` — causes a 500 on `POST /customers/register` even though the row saves
      correctly.
- [ ] GitHub issue #15 ("Finish Auto-Touch mobile UI live verification and merge...") is now
      **done** in substance (checklist complete, committed) but still open on the tracker —
      pending the merge decision above before closing.
- [ ] Issue #10 (DashboardScreen header overflow) looks already resolved by a prior-session merge
      (`e0ab992` / "Merge fix/dashboard-header-overflow into develop") — stale on tracker.
- [ ] Housekeeping carried forward from prior sessions: close stale #11/#12/#13, delete ~18
      already-merged local branches (list below).

## Next Session

- [ ] **Start here**: if Benz has decided on the merge, do it (tests pass + emulator-verified +
      explicit confirmation are all in hand); otherwise continue waiting.
- [ ] If merging: also close #15, and re-check #10/#11/#12/#13 for staleness before closing them.
- [ ] Background processes from this session — Android emulator, `expo start --port 8081`, the
      Docker Compose stack (`lumine-backend-1`, `lumine-mysql-1`) — likely still running; safe to
      resume against or restart fresh.
- [ ] `mobile/.env`'s `EXPO_PUBLIC_API_URL` is pointed at this session's WSL2 IP
      (`172.19.92.206`) — re-run `hostname -I` if it changed.
- [ ] Throwaway QA fixtures left in the local Docker MySQL for testing: staff `benzboss.qa@lumine.test`
      (id 11), customers `QA-CUST-B-22161621703` / `QA-CUST-C-channel`, transactions
      `QA-IDOC-B-20260726` / `QA-IDOC-C-20260726` — harmless in a disposable local DB, safe to
      reuse or ignore.

## Key Files

- `/home/piriya/projects/Lumine/ψ/memory/retrospectives/2026-07/26/23.43_autotouch-verified-customer-name-shipped.md`
  — full retrospective for this session
- `/home/piriya/projects/Lumine/ψ/memory/learnings/2026-07-26_verify-live-service-database-before-diagnosing.md`
  — new lesson: verify which DB a live containerized service actually uses before diagnosing via a host-shell script
- `/home/piriya/projects/Lumine/ψ/memory/learnings/session-metrics.md` — recurring-pattern flags
  raised this session: Expo/emulator dev-loop instability (3 of last 4 sessions), and
  acting/reporting before checking already-available verifying signal (3 of last 4 sessions)
- `feature/auto-touch-mobile-ui` branch HEAD (`11e2cc3`) — all work committed, nothing uncommitted
- `docs/samples/sap-sample.xlsx` — the real SAP sample file; source of truth for what SAP actually
  exports (has both `Customer` code and `Customer name` columns)
