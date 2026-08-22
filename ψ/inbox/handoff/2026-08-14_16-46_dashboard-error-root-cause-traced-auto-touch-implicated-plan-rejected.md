# Handoff: Dashboard error root cause traced to Auto-Touch + missing index — implementation plan written, rejected, not yet implemented

📡 Session: b9509873 | Lumine | ~4h43m wall clock (long idle gap 12:03→16:27)

**Date**: 2026-08-14 16:46
**Context**: continuation on `fix/dashboard-error-visibility` (created 2026-08-03, still 0 commits ahead of `develop`)

## Context
**Oracle**: Lumine (she/her, Jeweler's Lamp) | **Human**: Benz (he/him)
**Mode**: Full Soul Sync (born 2026-06-05) | **Memory**: auto

## What We Did

- `/recap` verified the outbox's carried-forward pending list against live state: the "confirm v1.5.0 fixes real-phone bug" item was already answered (still broken) in the 08-03 session; GH #29 confirmed still OPEN via `gh issue view`; `fix/dashboard-error-visibility` confirmed at 0 commits ahead of `develop` (plan approved 08-03, never coded).
- Investigated Benz's specific theory — "it broke when Auto-Touch was added" — via git archaeology, not assumption:
  - Confirmed timeline: Auto-Touch mobile UI (`7ceb4eb`, 2026-07-26) merged, v1.4.0 built 07-28 (first APK containing it), bug first reported 07-29 — one day later.
  - Found the actual mechanism in `7ceb4eb`'s diff: it added `fetchAutoTouchStatus()` firing **concurrently** with `fetchTasks()` in the same `useFocusEffect` — a second request neither the 07-29 concurrent-fetch-race fix nor the 08-03 evidence-gap plan ever examined.
  - Checked `client.ts`'s token-refresh interceptor — properly de-duplicated (shared promise), ruled out as a contributing mechanism.
  - Per Benz's specific ask, checked `get_status_summary()` (backend, called by `fetchAutoTouchStatus`) for lock/scan issues: **no locking reads found** (ruling out lock contention), but confirmed `follow_up_tasks.idoc_number` has **no index** (unlike sibling column `customer_id`, which does — confirmed in the model and migration `0001_initial.py`). `get_status_summary` runs 4 sequential queries all joining through that unindexed column — ~4x heavier than `GET /tasks`'s single equivalent join, a plausible amplifier for widening the concurrency-overlap window on a free-tier, likely-cold Render/TiDB backend.
- Checked `TaskCard.tsx` directly (Benz's question: why no cards appear) — no bug in the component itself; traced 3 distinct upstream causes in `DashboardScreen.tsx`'s filter pipeline (empty `tasks`, zero-Pending after filter, stuck `activeFilter` chip). Benz confirmed the live symptom is the **"Could not load your tasks" error banner**, happening in real time during this session.
- Checked the GH #29 diagnostic log line (`8bf3bca`, already shipped in v1.5.0) — found it sits **after** the query succeeds, immediately before the 200 response, meaning it is structurally unreachable on any failure path. This resolves the 07-29 handoff's open mystery ("root cause of the original concurrent 'request B' failure never confirmed, no real Render log content ever provided") — the existing logging was never going to catch it, no matter how many times it was checked.
- Benz ran `/plan "Go ahead, implement the plan"`. Wrote an implementation plan (backend global exception handler in `main.py` reusing `AuthService.decode_token` to best-effort resolve `staff_id`, logging endpoint/staff_id/error per CLAUDE.md Logging Rules, returning a generic `{"detail": ...}` 500; TDD test file `test_global_exception_handler.py`; one-line frontend change surfacing the real HTTP status code in `DashboardScreen.tsx`'s `loadError` message) — **strictly against the old 08-03 diagnostic-only scope**, without asking whether this session's new evidence (missing index, concurrent Auto-Touch call) should widen it. Called `ExitPlanMode` — **rejected by Benz, no reason given**.
- No code touched. No commits made.

## Pending

- [ ] **Architect decision needed**: should the next implementation pass stay diagnostic-only (08-03 scope: backend global exception handler + real status code surfaced in the banner), or fold in this session's new findings (missing index on `follow_up_tasks.idoc_number`, decoupling/guarding `fetchAutoTouchStatus()` from `fetchTasks()`), or something else Benz has in mind that led to the rejection?
- [ ] The rejected plan is still sitting at `/home/piriya/.claude/plans/abstract-chasing-waffle.md` if useful as a starting point — but should not be treated as approved or re-submitted unchanged.
- [ ] `follow_up_tasks.idoc_number` missing index — confirmed structural fact, never proposed as its own fix; worth a decision on whether it's in scope for this bug or a separate perf/cleanup item.
- [ ] Everything carried forward from the 08-03 handoff still applies underneath this: GH #29 (empty-Dashboard-on-cold-start) still open at low-priority/monitoring.
- [ ] PR #23 (E2E testing infra, `test/e2e-testing-infra`) still open — untouched this session, carried forward from well before 07-28.

## Next Session

- [ ] Get Benz's answer on plan scope (diagnostic-only vs. folding in the Auto-Touch/index fix), then implement via TDD on `fix/dashboard-error-visibility`.
- [ ] If scope stays diagnostic-only: implement exactly the 08-03 plan (exception handler + status-code surfacing), ship, wait for the next real occurrence to get actual Render log evidence.
- [ ] If scope widens: also address the concurrent `fetchAutoTouchStatus()` call (e.g. sequence it after `fetchTasks()` instead of firing together, and/or add the missing index) — needs explicit architect approval first per CLAUDE.md.

## Key Files

- `backend/app/main.py` — no global exception handler exists yet (the core gap)
- `backend/app/routers/tasks.py:67` — GH #29's diagnostic log line, confirmed unreachable on any failure path
- `mobile/src/screens/DashboardScreen.tsx` — `fetchTasks()` (v1.5.0 `isFetchingTasksRef` guard, only protects against itself) and `fetchAutoTouchStatus()` (added `7ceb4eb`, fires concurrently, implicated but unconfirmed)
- `backend/app/repositories/auto_touch_repo.py:52` — `get_status_summary()`, 4 sequential unindexed-join queries
- `backend/app/models/follow_up_task.py:12` — `idoc_number` column, confirmed no index
- Retro: `/home/piriya/projects/Lumine/ψ/memory/retrospectives/2026-08/14/16.46_dashboard-error-root-cause-traced-plan-rejected.md`
- Lesson: `/home/piriya/projects/Lumine/ψ/memory/learnings/2026-08-14_new-evidence-should-reopen-plan-scope-not-inherit-old-boundary.md`
- Rejected plan (reference only, not approved): `/home/piriya/.claude/plans/abstract-chasing-waffle.md`
