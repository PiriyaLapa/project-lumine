# Handoff: Production Gallery screenshots (2 projects) + adb-tap helper tool shipped

📡 Session: 6f067685 | project-lumine + PawsAndPace + portfolio-website + dotfiles-bin | ~3h

**Date**: 2026-08-21 21:37
**Context**: fresh session, three sequential deliverables

## What We Did

**1. Lumine screenshots → portfolio Production Gallery**
- Recapped portfolio-website's actual latest commit (`60d7125`, Benz's own
  `ProductionGallery` build) before touching anything, per his request.
- Ran `/plan`, researched Lumine's mobile screens/nav/auth, captured 7 real screens
  (Login, Dashboard, Task Detail, Evidence, Customer Profile, Auto-Touch, Follow-Up
  Report) via adb/uiautomator automation against a freshly-seeded local dev backend.
- Along the way: traced a misleading "Invalid credentials" error to a stale
  standalone APK with no attached Metro server (fixed by starting `expo start`), and
  found+filed a real backend bug — `GET /api/v1/customers/{id}` 500s when a
  SAP-imported customer has no `customers` table row (**Lumine issue #38**, fix
  suggested, not applied).
- Committed `dc0319a` (Lumine) + `eaf661c` (portfolio-website), pushed both, verified
  the Vercel deploy built from the right commit via `vercel inspect --logs`.

**2. PawsAndPace screenshots → portfolio Production Gallery**
- Repeated the process for PawsAndPace (GPS-driven fitness app, different Expo SDK).
- Fixed a real docker-compose port conflict (host 3307) via a local untracked
  `docker-compose.override.yml`. Registered a fresh account, diagnosed a genuine AVD
  environment gap via `dumpsys location` (Google Play Services' fused-location layer
  wasn't forwarding GPS updates to the app, despite the raw GPS provider updating
  correctly) — pivoted to the app's own Simulation Panel per the pre-written plan
  fallback rather than force a blocked pipeline.
- Found+filed a second real bug: Simulation Panel fake runs show `NaN:NaN`/`NaN kcal`
  on RunComplete/Evolution (**PawsAndPace issue #4**, exact two-line fix identified).
- Captured 6 screens (Register, Login, active Run, Run Complete, Evolution,
  Dashboard) — RunMapScreen/CountdownScreen intentionally omitted, no real route data
  ever existed to show.
- Committed `e07b41b` (PawsAndPace) + `7469dc9` (portfolio-website), pushed both,
  verified the Vercel deploy the same way.

**3. Built and shipped `adb-tap`**
- In direct response to a recurring-pattern flag (coordinate/tap-targeting mistakes,
  3 of last 7 session-metrics rows), built `~/bin/adb-tap` — a Python CLI that
  re-dumps the UI hierarchy before every tap/type instead of reusing stale
  coordinates, with a verified `--clear`+type-and-verify flow.
- Live-validated against the emulator (XML-escape safety, content-desc targeting,
  clear-vs-append correctness) — not just read back for plausibility.
- Discovered `~/bin` wasn't a git repo; asked where it should live rather than
  assuming, created a new private GitHub repo (`PiriyaLapa/dotfiles-bin`), committed
  `adb-tap` (`b1c386d`) + the pre-existing `adb` wrapper (`e7fd3d4`), pushed both.

## Pending

- [ ] Benz to visually confirm both Production Galleries render correctly on
      `piriyalapa.dev` — this sandbox has no browser and no network path to that
      domain, and `*.vercel.app` preview URLs are SSO-protected, so only commit-level
      deploy verification was possible, not visual confirmation.
- [ ] Lumine issue #38 (customer-profile 500 on missing `customers` row) needs an
      architect decision on the suggested fix.
- [ ] PawsAndPace issue #4 (SimulationPanel NaN:NaN/NaN-kcal bug) needs an architect
      decision on the suggested two-line fix.
- [ ] RunMapScreen/CountdownScreen remain unpopulated in the Paws & Pace gallery —
      worth a future session on a different AVD/host if full coverage is wanted,
      since the fused-location gap looked specific to this emulator instance.
- [ ] `docker-compose.override.yml` in PawsAndPace is untracked/undocumented outside
      this session's retro — worth a `.gitignore` entry + README mention so it
      doesn't look like a stray file to a future session.
- [ ] `logicVsLive` field on both portfolio projects is still unpopulated — a natural
      follow-up now that real screenshots exist, if Benz wants a diagram-vs-real-screen
      comparison feature.

## Next Session

- [ ] Get Benz's visual confirmation on both galleries, close the loop on this
      deliverable.
- [ ] Revisit Lumine #38 and PawsAndPace #4 once Benz has made a call on each.
- [ ] Use `adb-tap` (not hand-typed `adb shell input tap`) in any future
      Android-automation session, and note in that session's own metrics row whether
      it was used — this will make visible whether the tool actually closed the
      recurring coordinate-mistake pattern.
- [ ] Unrelated pre-existing item: PR #23 (`test/e2e-testing-infra`) is still open on
      project-lumine — not touched this session, flagging since it showed up in the
      cleanup scan.

## Key Files
- `project-lumine`: `docs/screenshots/*.png` (7 files, committed `dc0319a`)
- `PawsAndPace`: `docs/screenshots/*.png` (6 files, committed `e07b41b`),
  `docker-compose.override.yml` (untracked, local port-conflict fix)
- `portfolio-website`: `src/content/site.ts` (both projects' `uiScreenshots` now
  populated), `public/content/screenshots/*.png` (13 files total)
- `~/bin/adb-tap` (new, in `PiriyaLapa/dotfiles-bin`) — tap-by-dump helper for any
  future Android UI automation
