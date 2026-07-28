---
pattern: A number inherited from a prior session's handoff (test count, coverage %, "verified") is a claim, not a fact — run it yourself before using it to justify a merge/deploy gate
date: 2026-07-27
source: rrr: Lumine
concepts: [verification, test-coverage, merge-gate, plan-mode, credential-handling]
---

# Verify carried-forward claims before gating a merge — a count is not a verification

## What happened

Merging `feature/auto-touch-mobile-ui` → `develop`, the plan file stated "backend suite is
295/295 green" as a satisfied precondition. That claim came from the prior session's handoff,
not from actually running the suite this session. It happened to be numerically correct — 295
test functions existed and passed — but the deeper claim CLAUDE.md makes ("100% coverage in
backend/app/services/") was false: real coverage was 93%, with `google_drive_client.py` at 21%
(no dedicated test file at all) and `evidence_service.py` at 70% (`.update()` only ever exercised
through a mocked router, never for real). This only surfaced because the user pushed for a
stricter pre-`main`-merge gate and a real `pytest --cov` run was finally executed.

A related wrinkle: the research subagent tasked with checking coverage correctly refused to run
`pytest` under an active plan-mode restriction, and fell back to static analysis (`grep -c "def
test_"`). That produced an accurate test *count* but told us nothing about coverage — the one
number that actually mattered turned out to be unavailable until the execution phase, one full
round-trip later.

## Why this generalizes

- Test-function count and coverage percentage are independent signals. A suite can be "295/295
  passing" and still leave entire files essentially untested, if those files just happen not to be
  exercised by the passing tests.
- Claims that travel across sessions (handoffs, retros, CLAUDE.md assertions) decay silently —
  nothing forces them to be re-verified, so they get cited as fact indefinitely unless someone
  explicitly re-runs the check.
- Plan-mode's read-only restriction is correct to enforce, but it means a research phase under
  that restriction can only produce proxy metrics (counts, static greps) for anything that requires
  actual execution (real pass/fail, real coverage). That gap needs to be named explicitly in the
  findings, not silently backfilled with the proxy metric as if it were equivalent.

## How to apply

1. Before writing "tests pass" or "N/N passing" into a plan file as justification for a
   merge/deploy gate, actually run the suite this session — don't cite a number from a prior
   session's handoff or from a static grep of test function names.
2. When a project's own rules state a coverage threshold (e.g., "100% required"), treat that as
   something to verify with a real coverage report before a production-adjacent merge, not
   something to assume is already true because the docs say so.
3. If a research subagent is blocked from running the real check (plan-mode, sandboxing, missing
   deps), have it say so explicitly in its report — "test count is N, but coverage is unverified
   because execution was blocked" — rather than letting the available proxy metric stand in
   silently for the one that was actually asked for.
4. Separately: for secrets an agent cannot self-generate (a third-party API key tied to the
   user's own account/billing, as opposed to a throwaway credential the agent can mint itself —
   see [[2026-07-25_self-generate-credentials-never-relay-via-chat]]), the safe pattern is having
   the user edit the secret file directly, outside the chat pipeline — not relaying it through
   chat, and not routing it through a `!`-prefixed shell command either, since both still put the
   raw value through the session's visible transcript.
