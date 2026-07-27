---
pattern: Before merging into any branch that might be connected to auto-deploy, check what's actually configured to deploy from it — don't infer from documented convention alone, and if there's no direct way to check, use a zero-credential signal (an unauthenticated route that only exists in the newer code) to determine what's actually live.
date: 2026-07-23
source: rrr: Lumine
concepts: [deployment, production-incident, ci-cd, verification-without-impersonation]
---

# Check deploy consequences before merging, not after a bug report

## What happened

Merged PR #4 and PR #5 into `develop` on explicit user instruction. `CLAUDE.md`
documented the flow as "feat → develop → main," which reads as if `develop` is
a pre-production integration branch — nothing in it said `develop` triggers a
live deploy. It turned out Render was configured to auto-deploy from
`develop`, and the merge shipped code expecting a database migration
(`skipped_until` column, migration `0008`) that had never been applied to the
production database (TiDB Cloud, still at revision `0005`).

The result: every call to `GET /api/v1/tasks` in production started 500ing
immediately after the merge. This wasn't caught until almost a full day later,
when the user reported the mobile app showing a misleading "No pending tasks.
Well done!" empty state (itself a separate bug — the mobile client silently
swallowed the HTTP error instead of surfacing it).

## The generalizable rule

Before merging into a branch, ask (or check) whether that branch is wired to
an auto-deploy pipeline — don't assume based on a documented naming
convention like "develop is for integration, main is for production." If
there's no direct way to check (no dashboard access, no deploy config file in
the repo), a cheap empirical test works: hit an unauthenticated route that
only exists in the newer code version. A `403` (route exists, needs auth)
means the new code is live; a `404` means it isn't. This determined, with zero
credentials, that Render was running `develop`'s code — a fact that reframed
the entire incident investigation.

## Secondary pattern: verifying production without impersonating a real user

Twice in this session, authenticated production behavior needed proving
without the real user's password. Two safe patterns, both preferable to
forging a JWT for someone else's identity even when explicitly asked to "test
the live endpoint":

1. **In-process verification** — call the actual router/service function
   directly in Python against the real database, using a manually-constructed
   `TokenPayload` (or equivalent) that never leaves the process or touches the
   network. Proves the real query + real serialization/validation logic works,
   without any network-level auth involved at all.
2. **A freshly-registered, clearly-labeled throwaway account** via the real
   `/auth/register` endpoint — proves the real HTTP + auth path end to end
   when that's specifically what needs testing, without ever touching or
   pretending to be the real account.

## Also worth remembering

A safety mechanism that's been *coded* is not the same fact as a safety
mechanism that's *deployed and live*. Treat those as two separately-verifiable
claims, and re-check the live state explicitly before reporting a protection
as active — even (especially) in the same session where you personally wrote
the code, since "I built it" quietly substitutes for "it's live" if you don't
watch for that.
