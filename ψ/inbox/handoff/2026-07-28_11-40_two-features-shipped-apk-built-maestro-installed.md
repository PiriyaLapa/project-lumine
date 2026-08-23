# Handoff: Customer Profile + Nav Drawer shipped to production, v1.4.0 APK built, Maestro CLI installed (emulator connection still open)

📡 Session: e174f01a | Lumine | ~3h30m (08:01–11:32 GMT+7)

**Date**: 2026-07-28 11:40
**Context**: very long, dense session (ended via `/rrr` + `/forward`)

## Context
**Oracle**: Lumine (she/her, Jeweler's Lamp) | **Human**: Benz (he/him)
**Mode**: Full Soul Sync (born 2026-06-05) | **Memory**: auto

## What We Did

- Built **Customer Profile** (purchase history + follow-up/2-2-2 history per customer) — 3 new backend endpoints, `customer_profile_service.py`, new `CustomerProfileScreen.tsx`, store-wide-within-store auth exception documented in `CLAUDE.md`. TDD throughout, emulator-verified. Merged via PR #21.
- Built a **slide-out nav drawer** replacing Dashboard's 5-button header — new `GET /api/v1/auth/me`, `AppDrawer.tsx` (custom Modal + core `Animated`, no new native deps). Caught and fixed a real layout bug (`flex`/`width` conflict rendering the drawer full-width) live on the emulator. Merged via PR #22.
- Stood up **real E2E testing infra** as a third branch (PR #23, still open): isolated `docker-compose.e2e.yml` stack, `seed_e2e_data.py`, 11 real HTTP tests in `backend/tests_e2e/` — verified live, dev/QA data confirmed untouched. Mobile Maestro flows written (`mobile/.maestro/*.yaml`) but not yet run against a device (see Pending).
- Ran a full **product backlog + production-readiness audit**, cross-checked against real code state (not just the tracker) — found 2 stale-but-open issues (#11, #2 — already done) and one real untracked security gap (`auth.py` self-registration lets anyone pick `store_manager`).
- Benz set a hard deadline ("must work tomorrow" — follow-ups, history, evidence logging; Auto-Touch explicitly OK to leave broken). Merged the release PR #24 (`develop`→`main`), smoke-tested production, live-verified the evidence-logging flow end to end for the first time this session — **found a real workflow trap: no way to add evidence to a task after marking it Done** (found by walking into it myself). Bumped mobile to **v1.4.0 / versionCode 6** (PR #25).
- Ran the **EAS cloud build myself** (`eas-cli` was already authenticated on this machine) — build `288084da` finished successfully: **https://expo.dev/artifacts/eas/veUbRZJ85CGeZhS29Si3IRyxjH4jMImaOLUKz-iIqZA.apk**
- Installed **Java + Maestro CLI with no root access** (portable Temurin JRE to `~/.local/jre`, Maestro to `~/.maestro` — both added to `~/.bashrc`). Attempted to connect Maestro to the emulator — blocked by a real WSL2/Windows networking split (Maestro's JVM needs its own ADB server; the working `adb` here is a wrapper shelling to Windows' `adb.exe`, and the emulator's ADB port is bound to `127.0.0.1` on the Windows side only, unreachable from WSL2's network namespace).

## Pending

- [ ] **Benz**: install the v1.4.0 APK on your phone (link above), confirm it opens and logs into production correctly — the one check only you can do.
- [ ] Maestro↔emulator connection — needs a Windows-side fix: either enable WSL2 mirrored networking (`.wslconfig` → `networkingMode=mirrored`, then `wsl --shutdown`) or run `adb.exe -a nodaemon server start` to bind all interfaces. Not urgent.
- [ ] Decide on PR #23 (E2E infra): merge as-is (backend fully proven, mobile flows unverified) or wait for Maestro to fully connect.
- [ ] `auth.py` self-registration role gap (`/api/v1/auth/register` lets anyone pick `store_manager`, no auth on the endpoint) — worth fixing before any non-solo use.
- [ ] `ANTHROPIC_API_KEY` still absent from `backend/.env` (issue #19) — you-must-do-it-yourself step.
- [ ] Close GitHub #11, #2 (already done, tracker is stale) — no new issue, just close.
- [ ] Decide on #9, #3, #12, #13, #14 — unrelated older backlog, carried forward unchanged.
- [ ] Local branch cleanup (#20) — now +2 more merged branches (`feature/customer-profile-history`, `feature/nav-drawer`) since last count.
- [ ] SAP Material Description samples (#1) — unblocks `sap_product_parser.py`, which was never built (Auto-Touch messages currently show raw SAP codes).
- [ ] **Remember**: log evidence *before* marking a task Done — there's currently no way to add it after, per the workflow trap found this session.

## Next Session

- [ ] Confirm with Benz whether the APK install/login check passed.
- [ ] If Maestro networking gets fixed: run `mobile/.maestro/login.yaml` (and the other 3 flows) for real, then reconsider merging PR #23.
- [ ] Otherwise: pick up the backlog items above, or whatever Benz raises fresh.

## Key Files

- `backend/app/routers/customers.py`, `customer_profile_service.py` — Customer Profile
- `mobile/src/components/AppDrawer.tsx`, `mobile/src/screens/DashboardScreen.tsx` — nav drawer
- `backend/tests_e2e/`, `docker-compose.e2e.yml`, `mobile/.maestro/*.yaml` — E2E infra (PR #23, open)
- `mobile/app.json` — v1.4.0 / versionCode 6
- `CLAUDE.md` — Auth Rules exception, APK table, E2E Testing section, refreshed test count (326/326)
- Retro: `/home/piriya/projects/Lumine/ψ/memory/retrospectives/2026-07/28/11.32_two-features-shipped-apk-built-maestro-half-unblocked.md`
- Lesson: `/home/piriya/projects/Lumine/ψ/memory/learnings/2026-07-28_try-no-root-alternative-before-blaming-environment-mismatch.md`
