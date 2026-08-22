---
pattern: Check the production database's actual live migration/schema state directly before trusting any root-cause theory for a production bug — dev/prod drift can itself be the bug
date: 2026-08-15
source: rrr: Lumine
concepts: [root-cause-analysis, migration-drift, production-verification, overconfidence, alembic]
---

# Verify production schema state before trusting a root-cause theory

## What happened

Across three sessions (2026-07-29, 2026-08-03, 2026-08-14), a production bug ("Could not load your tasks" on the mobile Dashboard) was investigated purely through git archaeology and local dev environment behavior. A plausible, well-evidenced theory built up: `fetchAutoTouchStatus()` firing concurrently with `fetchTasks()` (added in a specific commit, timed to match the bug's first report), amplified by a missing database index. This session (2026-08-15) implemented and shipped a fix for exactly that theory — new migration, code change, full TDD, live emulator verification, PR merged.

Then, while doing the routine next step of applying the new migration to production, `alembic current` against the real production database showed it was **two migrations behind** — not one. A migration from 2026-07-26 (`transactions.customer_name`) had never been deployed to production at all. Directly querying production with the exact function behind `GET /api/v1/tasks` confirmed a deterministic `OperationalError: Unknown column 'transactions.customer_name'` — the endpoint had been failing on **every single call**, not intermittently. This was the real, dominant cause of the bug — found almost by accident during a deploy step, not by the diagnosis process itself.

## The pattern

A root-cause theory built entirely from code inspection, git history, and local/dev environment reproduction can be internally consistent, well-evidenced, and still be answering the wrong question — because dev and production schema state can silently diverge, and that divergence can itself be the actual bug. The more sessions spent building a theory this way, the more confident it feels, but confidence built on local evidence never checks the one fact that mattered: does production even have the schema the code assumes?

## Why this generalizes

Any bug investigation for a deployed system should include, early — not as an afterthought during deployment — a direct, live check of production's actual state relevant to the theory being built:
- For migration-based schema systems (Alembic, Django migrations, Rails, etc.): run the "current revision" check against the real production database connection string, not just `git log` on migration files or the dev database's state.
- For config/environment-dependent bugs: check the actual production environment variables/config, not just what's in `.env.example` or what the dev environment has.
- For deployment-pipeline assumptions ("X auto-deploys from branch Y," "migrations run automatically on deploy"): verify this is actually happening, don't assume it from documentation or past sessions' notes — this project's own Render deployment does *not* appear to auto-run `alembic upgrade head`, which was itself an unverified assumption carried across multiple sessions.

The cost of skipping this check scales with how much work gets built on top of the wrong theory — in this case, a full implementation, test suite, live emulator verification, and merged PR, all of which remained valid and worth keeping (the concurrency fix is real and harmless), but none of which addressed the actual dominant failure mode until the schema check happened to surface it.

## Related

[[2026-08-03_a-stale-summary-can-be-fluent-and-wrong-verify-after-any-gap]] — same family of "fluent and confident but unverified" failure, applied here to root-cause theories specifically rather than carried-forward summaries.
[[2026-07-29_verify-inferred-diagnoses-before-filing-not-only-when-asked-to-plan-a-fix]] — this session is a longer, more elaborate recurrence of the same underlying pattern: an inferred diagnosis treated as settled before a direct live check.
