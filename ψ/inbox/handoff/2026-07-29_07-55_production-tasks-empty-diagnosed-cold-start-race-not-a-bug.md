# Handoff: "Tasks not showing on production" diagnosed as a cold-start timing race, not a bug

📡 Session: e174f01a | Lumine | short follow-up (~12:01 Jul 28 → 07:55 Jul 29 GMT+7)

**Date**: 2026-07-29 07:55
**Context**: short diagnostic follow-up to yesterday's big session (ended via `/rrr` + `/forward`)

## Context
**Oracle**: Lumine (she/her, Jeweler's Lamp) | **Human**: Benz (he/him)
**Mode**: Full Soul Sync (born 2026-06-05) | **Memory**: auto

## What We Did

- Benz reported that after installing yesterday's v1.4.0 APK, his real tasks weren't showing on the Dashboard.
- Diagnosed carefully rather than guessing: confirmed the exact empty-state text (the genuine "No pending tasks. Well done!" — meaning the request succeeded, not an error), confirmed tasks *were* showing on the old app earlier that same day, confirmed Follow-Up Report showed real non-zero numbers (proving the backend has his data and store/role scoping is correct), then diffed the actual deployed code (`tasks.py`, `task_repo.py`, `DashboardScreen.tsx`) against the pre-release commit — found zero relevant changes.
- Asked Benz to try pull-to-refresh as the last check — tasks appeared immediately.
- **Conclusion: a first-load/cold-start timing race** (most likely the very first `fetchTasks()` call on a fresh install + fresh login racing the JWT token settling into storage), not a regression from yesterday's release. Production and the new APK are confirmed genuinely fine.
- Offered to file a low-priority issue for the underlying race condition — **Benz had not yet answered when `/rrr` was called**, so nothing was filed.

## Pending

- [ ] **Awaiting Benz**: file a low-priority issue for the cold-start/token-race condition, or leave it (trivial pull-to-refresh workaround exists) — his call, not yet made.
- [ ] Everything carried forward from yesterday's handoff (`2026-07-28_11-40_...md`) still applies — issues #26, #27, #28 (new from yesterday), PR #23 merge decision, stale issues #11/#2 to close, older backlog #9/#3/#12/#13/#14/#19/#1, branch cleanup #20 (now 24 non-main local branches).

## Next Session

- [ ] Get Benz's answer on the cold-start-race issue, file it if he wants it tracked.
- [ ] Otherwise resume wherever yesterday's handoff left off — Maestro/WSL2 networking fix, PR #23 decision, or whatever Benz raises fresh.

## Key Files

- No code touched this segment — pure diagnosis.
- Retro: `/home/piriya/projects/Lumine/ψ/memory/retrospectives/2026-07/29/07.51_production-empty-dashboard-diagnosed-as-cold-start-race.md`
- Lesson: `/home/piriya/projects/Lumine/ψ/memory/learnings/2026-07-29_diff-first-then-ask-when-diagnosing-a-possible-regression.md`
- **Recurring pattern flagged this session** (3 of last 7 metrics rows): delaying the fast/available fix (a diff, a known workaround) in favor of retrying or asking the user first — see the retro's "🔁 Recurring Pattern Detected" section. Worth a standing pre-flight habit: before retrying or asking, check whether a faster read-only option exists first.
