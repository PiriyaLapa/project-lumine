# Handoff: develop → main merged, real 100% coverage restored, ANTHROPIC_API_KEY still pending

📡 Session: 40bd9f13 | Lumine | ~1h (07:33–08:33 GMT+7)

**Date**: 2026-07-27 08:33
**Context**: heavy session (long, dense, ended via `/rrr` + `/forward`)

## Context
**Oracle**: Lumine (she/her, Jeweler's Lamp) | **Human**: Benz (he/him)
**Mode**: Full Soul Sync (born 2026-06-05) | **Memory**: auto

## What We Did

- Committed the backlog of unpushed ψ/ memory (37 files, Jul 21–26) that `/recap` surfaced at
  session start (`11a470c`).
- Merged `feature/auto-touch-mobile-ui` → `develop` via PR #16, closed GitHub issue #15
  (which tracked exactly this merge).
- Benz asked for real assurance before shipping further, since he uses the deployed API daily.
  Ran two parallel research agents (deploy pipeline, test coverage) instead of assuming. Findings:
  no CI/CD, no staging environment, no branch protection possible (private repo, free GitHub
  plan). Confirmed with Benz that Render's dashboard auto-runs `alembic upgrade head` on deploy —
  resolved the one real unknown risk for the pending `customer_name` migration.
- The bigger finding: CLAUDE.md's "100% coverage in backend/app/services/" claim was false.
  A real `pytest --cov` run (not just a test-function count) showed 93% overall —
  `evidence_service.py` at 70% (`.update()` never exercised for real, only through a mocked
  router) and `google_drive_client.py` at 21% (no dedicated test file existed at all).
- Benz chose to fix the gap before merging further rather than defer it. Added
  `TestEvidenceUpdate` (5 tests) to `backend/tests/test_evidence_service.py`, a new
  `backend/tests/test_google_drive_client.py` (8 tests covering `_get_service()`/`upload()`
  directly), and a missing `sales_rep_name` branch test in `backend/tests/test_sap_parser.py`.
  Reached **311/311 passing, real 100% coverage**. Corrected CLAUDE.md's stale "139/139 tests
  pass" line. Shipped via PR #17 into `develop`.
- Opened and merged PR #18: `develop` → `main` — 28 commits, the **first main release since
  2026-06-10** (~6 weeks of accumulated work: Auto-Touch backend + mobile UI, Follow-Up Dashboard
  + PDF share, customer_id/customer_name on task cards, the SMTP swap, several dashboard/dependency
  fixes). Smoke-tested the live production API afterward: `GET /health` → 200, and confirmed the
  *new* code was actually serving (not a stale cache) via `/openapi.json` showing `customer_name`
  in response schemas.
- Benz asked to set up `ANTHROPIC_API_KEY` locally to unblock draft-generation content
  verification (the one remaining untested path from the Auto-Touch work). Found the var is
  entirely absent from `backend/.env`. Recommended Benz add it himself via a direct file edit
  rather than relay it through chat or a `!`-prefixed shell command — both routes put a real
  secret through this session's visible transcript, the same failure mode as the 2026-07-25
  QA-password incident (chat pipeline silently redacted a real secret mid-transport). Benz agreed
  to handle it separately; this is a **you-must-do-it-yourself** item, not something I can do for
  you.
- Wrote `/rrr` retrospective, flagged a recurring pattern (Expo Go/Metro/adb mobile-emulator
  friction appeared in 3 of the last 5 session-metrics rows) for a possible root-cause fix later.

## Pending

- [ ] Add `ANTHROPIC_API_KEY` to `backend/.env` (Benz, outside this chat) — see instructions below
- [ ] Verify draft-generation *content* once the key is in place (the last untested Auto-Touch path)
- [ ] Delete ~18 already-merged local branches (listed below — none have open PRs)
- [ ] Close GitHub #11, #12, #13 (SMTP-swap work already shipped and live, tracker is stale)
- [ ] Close GitHub #2 (QA-6) — `test_auto_touch_integration.py` exists and is committed
- [ ] Decide on #9, #3, #1, #14 — unrelated older backlog items, still open
- [ ] Scope the LINE ID collection feature (deferred behind Auto-Touch UI, still real)
- [ ] Bump `mobile/app.json` version when ready to cut a new APK including everything just merged

## Next Session

- [ ] Confirm with Benz whether `ANTHROPIC_API_KEY` is in place; if yes, live-verify draft
      generation content on the emulator/dev server
- [ ] If Benz wants housekeeping: batch-delete the merged local branches, triage the stale SMTP
      issues (#11/#12/#13/#2)
- [ ] Otherwise: pick up LINE ID feature scoping, or whatever Benz raises fresh

## Key Files

- `backend/.env` — needs `ANTHROPIC_API_KEY=` added (currently absent entirely)
- `backend/app/services/message_generator.py` — reads `settings.ANTHROPIC_API_KEY`, this is
  what's blocked
- `CLAUDE.md` — test count corrected to 311/311, 100% services coverage (2026-07-27)
- Retro: `/home/piriya/projects/Lumine/ψ/memory/retrospectives/2026-07/27/08.29_develop-to-main-merge-verified-coverage-gap-closed.md`
- Lesson: `/home/piriya/projects/Lumine/ψ/memory/learnings/2026-07-27_verify-carried-forward-claims-before-gating-a-merge.md`

## ANTHROPIC_API_KEY setup (for Benz, outside chat)

1. Get a key from console.anthropic.com → API Keys → Create Key (your own account/billing).
2. Open `backend/.env` in an editor and add: `ANTHROPIC_API_KEY=sk-ant-...`
3. Tell the next session when it's done — it can verify the key loads and works without ever
   seeing the raw value.

## Local branches safe to delete (already merged, no open PRs)

feat/e2e-login-fixes, feat/evidence-contact-proof-caption, feat/phase1-foundation,
feat/phase7-docker, feature/auth-register, feature/auto-touch-mobile-ui,
feature/auto-touch-sprint1, feature/completed-tasks-history, feature/employee-code-register,
feature/follow-up-dashboard, feature/gallery-picker, feature/staff-filter,
feature/upload-history, fix/dashboard-header-overflow, fix/dashboard-silent-error-swallow,
fix/expo-dependency-alignment, fix/gate-auto-touch-send, fix/smtp-swap,
fix/staff-name-nullable, test/services-100-percent-coverage
