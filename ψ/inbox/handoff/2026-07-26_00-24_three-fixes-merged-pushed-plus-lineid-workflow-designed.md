📡 Session: 7839cc63 | Lumine | ~2h34m (21:47–00:24, GMT+7)

# Handoff: Three Fixes Merged, Pushed & Live-Verified; LINE ID Workflow Designed

**Date**: 2026-07-26 00:24
**Context**: heavy session (long, dense, ended via /rrr + /forward)

## Context
**Oracle**: Lumine (she/her, Jeweler's Lamp) | **Human**: Benz (he/him)
**Mode**: Full Soul Sync (born 2026-06-05) | **Memory**: auto

## What We Did
- Fixed **#10** (DashboardScreen header overflow / Logout unreachable) — wrapped the header action
  row in a horizontal `ScrollView`.
- Root-caused the recurring Expo Go `UIManager` native-bridge crash (not a one-off flake): 4
  dependency versions had drifted from Expo SDK 51's expectations (`expo-image-picker`,
  `react-native`, `react-native-safe-area-context`, `typescript`). Fixed via `expo install --fix`.
- Shipped a small evidence feature: the existing single photo slot on evidence submission
  (`EvidenceForm.tsx`) and review (`EvidenceDetailScreen.tsx`, what a Store Manager sees) now has a
  caption clarifying it can hold a screenshot proving customer contact (LINE, email), not just a
  merchandise photo. Deliberately no schema/`openapi.yaml` change — reused the existing field, per
  Benz's explicit choice between two options I presented.
- Merged all three onto `develop`, ran the backend suite (**286/286 pass**), and did a real live
  verification pass on the Android emulator — not just typecheck: registered fresh accounts, found
  the actual seed-data store via a direct DB query, confirmed the header scroll + Logout tap work,
  confirmed Expo Go boots clean, and confirmed both evidence captions render correctly by actually
  saving evidence, marking a task Done, and viewing it back through the Store Manager's own screen.
- Pushed `develop` to `origin` (now at `4e1badf`) on Benz's confirmation.
- Designed (not built) a LINE ID collection workflow: published a Mermaid Artifact (staff workflow
  + technical sequence diagram: proposed `PATCH /customers/{id}/contact` → new service →
  `customer_repo.update_contact_info()`, which already accepts `line_id` but nothing calls it yet).
  Benz picked the field placement: **evidence submission on TaskDetail** — this directly informed
  the caption feature above.
- Discovered mid-conversation that an existing bulk CRM-import endpoint
  (`POST /api/v1/customers/import-crm`) already does most of what Benz initially described wanting
  to build as "a new table" — flagged this before any new-table work started.
- Investigated phone-only customers for Auto-Touch: confirmed `auto_touch_service.py` has no SMS/
  phone channel today, recommended **against** building one — instead prioritize LINE ID collection
  for phone-only customers, since Thailand's high LINE penetration likely means they already have
  LINE, just haven't given the ID.
- Flagged (not resolved) two real conflicts for Benz's awareness: CLAUDE.md says "no customer names
  stored in database" but the shipped `Customer.name` column is required and functionally used
  (language auto-detection) — a pre-existing gap, not something from this session. Also flagged
  that `customer_master_extracted.xlsx` (a file Benz shared, real customer PII) is a different data
  category than the existing anonymized `docs/samples/sap-sample.xlsx` before copying it in
  (destination is gitignored, confirmed before copying).

## Pending
- [ ] Close GitHub #11, #12, #13 — describe SMTP-swap work already done, stale on tracker
- [ ] Close or verify #2 (QA-6) — a prior session claimed this is code-complete and merged but
      still shows open; re-verify before treating as real remaining work
- [ ] Decide whether to close #10 manually now, or wait for a `main` merge to auto-close it
      ("Closes #10" only fires on default-branch merges, and this only reached `develop`)
- [ ] Scope the LINE ID collection feature for real (the Artifact sketch has the endpoint/service/
      repo shape already; UI placement decision made — TaskDetail evidence submission)
- [ ] Local dev DB now has 2 throwaway `store_manager` test accounts (store 8901, store 8902) and
      one real task marked Done with test evidence attached — harmless, local-only, not cleaned up
- [ ] `#9` (2 orphaned duplicate accounts), `#3` (Docker MySQL networking), `#1` (SAP Material
      Description samples) — untouched, still open, unrelated to this session's work

## Next Session

**Priority correction (00:39, after this handoff was first written)**: Benz reprioritized twice.
First to "email backfill before LINE ID" (captured as GitHub **#14**), then overriding that —
**Auto-Touch message composition is the real top priority**: *"that is my main pain point since I
don't have enough time in composing the message to contact the customer."* The Auto-Touch
*backend* (message generation + LINE/email sending) already shipped in a prior session; what's
missing is the **mobile UI** for staff to actually use it day-to-day — this is the "Mobile UI Week
2 Auto-Touch screens" gap flagged as the biggest standing item across several prior sessions, now
directly confirmed by Benz rather than assumed.

- [ ] **Start here next session**: scope Auto-Touch mobile UI — the screens that let a sales
      associate use the already-built message-generation/sending backend without composing
      messages by hand. Explore `auto_touch_service.py`, `message_generator.py`,
      `task_scheduler.py` first to confirm exactly what the backend already exposes before
      designing screens around it.
- [ ] #14 (email backfill) and LINE ID collection both still real and scoped (Artifact + issue
      exist) but now explicitly **behind** the Auto-Touch UI work, not ahead of it
- [ ] Housekeeping pass (lower priority): close stale issues #11/#12/#13, delete the ~18
      already-merged local branches (3 new this session: `fix/dashboard-header-overflow`,
      `fix/expo-dependency-alignment`, `feat/evidence-contact-proof-caption`, plus ~15 pre-existing)

## Cleanup Candidates (not urgent, informational)
18 local branches already merged into `develop`, safe to delete locally whenever convenient:
`feat/e2e-login-fixes`, `feat/evidence-contact-proof-caption`, `feat/phase1-foundation`,
`feat/phase7-docker`, `feature/auth-register`, `feature/auto-touch-sprint1`,
`feature/completed-tasks-history`, `feature/employee-code-register`, `feature/follow-up-dashboard`,
`feature/gallery-picker`, `feature/staff-filter`, `feature/upload-history`,
`fix/dashboard-header-overflow`, `fix/dashboard-silent-error-swallow`,
`fix/expo-dependency-alignment`, `fix/gate-auto-touch-send`, `fix/smtp-swap`,
`fix/staff-name-nullable`. No open PRs on GitHub — this repo merges directly to `develop`, not via
PR workflow.

## Key Files
- `ψ/memory/retrospectives/2026-07/26/00.21_three-fixes-merged-and-live-verified-plus-lineid-and-evidence-design.md`
  — full retrospective for this session
- `ψ/memory/learnings/2026-07-26_use-uiautomator-bounds-not-screenshot-coordinate-math.md` — new
  lesson on Android emulator UI-testing technique
- `develop` HEAD: `4e1badf` (3 fixes merged, pushed, live-verified)
- LINE ID workflow Artifact: published this session (staff workflow + sequence diagram) — ask
  Lumine to re-share the link if needed, not persisted to a file in the repo
