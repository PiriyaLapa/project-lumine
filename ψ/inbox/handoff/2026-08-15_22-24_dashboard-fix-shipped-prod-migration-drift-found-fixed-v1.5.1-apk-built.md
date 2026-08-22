# Handoff: Dashboard fix shipped, real production root cause found + fixed, v1.5.1 APK built

📡 Session: e6e413dc | Lumine | ~60m (21:24–22:24)

**Date**: 2026-08-15 22:24
**Context**: continuation from 08-14 handoff (`fix/dashboard-error-visibility`, plan rejected)

## Context
**Oracle**: Lumine (she/her, Jeweler's Lamp) | **Human**: Benz (he/him)
**Mode**: Full Soul Sync (born 2026-06-05) | **Memory**: auto

## What We Did

- Implemented and shipped the fix proposed at the end of the 08-14 session: migration 0011 (index on `follow_up_tasks.idoc_number`) + decoupled `fetchAutoTouchStatus()` from `fetchTasks()` in `DashboardScreen.tsx`'s `useFocusEffect`. 331/331 backend tests pass unchanged. PR #33 opened, verified live end-to-end on a real Android emulator (fought through WSL2 `adb reverse` silently dropping relayed data — worked around via direct LAN IP — and a few Expo Go native crashes before a clean load), merged to `develop` (`b5f8b98`).
- **Found the real production root cause almost by accident**, while applying the new migration to production: `alembic current` against the live production TiDB showed `0009`, not `0010` — migration 0010 (`transactions.customer_name`, merged 2026-07-26) had **never been deployed to production**. Directly running the exact `GET /api/v1/tasks` query function against production confirmed a deterministic `OperationalError: Unknown column 'transactions.customer_name'` — this endpoint had been failing on **every single call** in production, not intermittently as every prior session (07-29, 08-03, 08-14, and this session's own PR) had assumed.
- Reported this to Benz before touching anything further; got explicit go-ahead. Applied migrations 0010+0011 directly to production TiDB (after catching that an unscoped `alembic upgrade head --sql` misleadingly regenerates the full chain from base — re-ran scoped as `0009:head --sql` for an honest preview first). Verified the previously-failing query now succeeds live against production.
- Updated `CLAUDE.md` (APK table + Current Phase narrative) with the accurate finding, bumped `mobile/app.json` to v1.5.1/versionCode 8, committed+pushed directly to `develop` (`55b7b0c`, matching the existing precedent for version-bump commits).
- Ran a real EAS `preview` build — **finished successfully**. APK: https://expo.dev/artifacts/eas/jetrYcQ882QBj5yNrtISb4sYcP9lWVKCM2CZYmPj17M.apk
- Wrote a lesson learned on the core mistake this session surfaced: root-cause theories built entirely from git history + local dev behavior can be confidently wrong when dev/prod schema drift is the actual bug — always check the production database's live state directly, early, not as an afterthought during deploy.

## Pending

- [ ] Install v1.5.1 APK on Benz's real phone and confirm the Dashboard loads correctly in production now (this closes the loop Benz has been chasing since 2026-07-29 — high confidence given the deterministic missing-column cause is now fixed, but not yet confirmed on a real device)
- [ ] Consider commenting on / closing GH #29 ("Dashboard: first-load cold-start race can show empty task list after fresh login") — today's finding (missing migration → deterministic `GET /tasks` failure) is a much stronger explanation for the reported symptom than the cold-start race theory #29 was filed under. Not touched this session — Benz's call.
- [ ] A recurring pattern was flagged in this session's retro: "asserted an unverified/inferred theory as fact without doing the one live check that would confirm it" appeared in the error column of 3 of the last 7 sessions (07-29 09:00, 07-29 09:18, this session). Worth a standup conversation about a standing habit fix, not another one-off catch.
- [ ] Local dev environment still running in a modified state from this session's emulator verification: `lumine-backend-1` Docker container is running with the dev-override hot-reload mount (not its original 3-week-old baked image), and a backgrounded `expo start --android` / Metro process may still be alive. Neither is harmful, but worth a clean restart next session if it causes confusion.

## Next Session

- [ ] Confirm real-phone install of v1.5.1 and report back
- [ ] Decide on GH #29 (close with reference to this session's finding, or leave open pending real-phone confirmation)
- [ ] Optionally address the recurring "unverified theory as fact" pattern as a standing habit

## Key Files

- `mobile/src/screens/DashboardScreen.tsx` — the sequencing fix
- `backend/alembic/versions/0011_index_followuptask_idoc_number.py` — the index migration
- `backend/app/models/follow_up_task.py` — `index=True` added
- `CLAUDE.md` — APK table + Current Phase, now accurate on the real root cause
- `ψ/memory/retrospectives/2026-08/15/22.21_dashboard-fix-shipped-prod-migration-drift-was-real-cause-v1.5.1-building.md` — full retro with AI Diary + recurring-pattern detection
- `ψ/memory/learnings/2026-08-15_verify-production-schema-state-before-trusting-a-root-cause-theory.md` — the generalizable lesson
