# Handoff: Dashboard concurrent-fetch race — diagnosed, fixed, shipped as v1.5.0

📡 Session: 11f65fd7 | Lumine | long session, 08:12–18:24 GMT+7

**Date**: 2026-07-29 18:24
**Context**: continuation of the day's big session (recap → GH #29 diagnostic logging → GH #27 self-registration fix → GH #20 branch cleanup → this Dashboard race-condition investigation)

## What We Did

- Fixed **GH #27** (self-registration could pick `store_manager`) — PR #31 merged, mobile role picker removed.
- Fixed **GH #20** (delete merged branches) — 22 branches deleted locally and on origin, verified merged first.
- Investigated a real production incident: Store Dashboard showing **"Could not load your tasks. Pull down to try again."** Ruled out DB connectivity, a stale-migration false alarm (traced to a 9-day-stale local `backend/.env`, not a real production issue), a bad deploy, and a refresh-token-expiry theory (falsified when a fresh re-login still failed).
- Found the real root cause by tracing code, not logs: `DashboardScreen.tsx`'s `fetchTasks` had **no in-flight guard**, and both `useFocusEffect` and `RefreshControl`'s `onRefresh` called it — pulling to refresh while a fetch was already running fired a second, concurrent, racing request that could silently overwrite a genuinely successful state with an error.
- Fixed it with a `useRef`-based guard — but **committed it and moved on without shipping it**. Hours later the bug recurred; verified branch/PR/merge state directly (not assumed) and confirmed the fix had been sitting local-only the whole time. Pushed, opened **PR #32**, merged on explicit confirmation.
- Manual-reproduction tested the fix via Metro (temporary debug log, removed after) — passed on the emulator. But the **real phone still showed the bug**, because it's still running the old binary — this app has **no OTA update path** (confirmed: no `expo-updates` package, no `updates` config) — every fix requires a full EAS build + manual install.
- Bumped to **v1.5.0 (versionCode 7)**, added the changelog row, triggered `eas build --profile preview --platform android`, watched it via a backgrounded polling loop, build finished in ~12.5 min. Benz installed it and is **still testing** as of this handoff.

## Pending

- [ ] **Confirm whether v1.5.0 actually fixes the Dashboard bug on Benz's real phone** — he was mid-test when this session wrapped.
- [x] ~~Push commit `045bec1` to `origin/develop`~~ — done during this handoff (pushed `e244261..045bec1`), specifically to avoid repeating the exact mistake this session's own lesson names. `develop` and `origin/develop` are in sync as of end of session.
- [ ] Root cause of the original concurrent "request B" failure (from the very first incident, before the guard fix) was never confirmed — no real Render log content was ever provided despite two requests. Independent of the fix (which addresses the mechanism regardless); revisit only if useful.
- [ ] GH #29 (empty-Dashboard-on-cold-start) remains open at low-priority/monitoring — diagnostic logging shipped and verified live, but root cause still unconfirmed.

## Next Session

- [ ] Check in on the v1.5.0 real-phone test result if Benz hasn't already reported it.
- [x] ~~Clean up 3 more locally-merged branches~~ — done during this handoff (`fix/dashboard-concurrent-fetch-race`, `fix/registration-force-sales-associate-role`, `fix/tasks-diagnostic-logging`, verified merged first, deleted locally + on origin).
- [ ] Consider whether GH #29's still-unconfirmed root cause and the original "request B" mystery are worth closing out, or should just stay in monitoring mode.

## Key Files
- `mobile/src/screens/DashboardScreen.tsx` — the race-condition guard (`isFetchingTasksRef`)
- `mobile/app.json`, `CLAUDE.md` — v1.5.0/versionCode 7 bump (uncommitted push pending)
- `ψ/memory/learnings/2026-07-29_a-committed-fix-is-not-a-shipped-fix.md` — this session's main lesson
