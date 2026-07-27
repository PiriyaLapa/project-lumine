---
pattern: When a handoff or memory file states test counts, coverage percentages, or "ready to commit/merge" claims, re-run the verification yourself before acting — don't cite the stale number as current fact.
date: 2026-07-25
source: rrr: Lumine
concepts: [verification, handoff-trust, memory-staleness, code-review]
---

# Verify handoff claims before acting on them, not just before reporting them

## What happened

A prior session's handoff claimed the SendGrid→SMTP swap was "286/286 tests, 100% coverage,
diff shown, staged" and just needed a go-ahead to commit. It would have been fast to take that at
face value and run `git commit` directly. Instead, before committing, the diff was actually read
(`git diff --cached`), the test suite was actually re-run, coverage was actually re-measured on the
new file, and a grep was run for leftover references to the old provider name.

This surfaced a real, previously-missed issue: `backend/.env.example` had a comment referencing
`SENDGRID_API_KEY`, a variable deleted a few lines above in the very same diff — a stale reference
that "286/286 tests pass" and "100% coverage" cannot catch, because neither metric grades prose in
comments.

## The generalizable rule

A memory file, handoff, or retrospective's stated metrics are a claim about a past point in time,
not a live fact. This is already documented as a general principle (`/recap`'s "Verify Before
Reporting" section), but the scope is broader than reporting: **verify before *acting* on a claim
that leads to a commit, merge, or deploy — not only before repeating the claim back to the user.**
Re-running tests and re-reading a diff costs very little compared to the cost of committing
something with an undiscovered issue, however small.

## Also worth remembering

Diligence tends to drop right after finding the first issue. In this session, after finding the one
stale `SENDGRID_API_KEY` reference, the fix was applied and tests were re-run, but a second full
read-through of the same file (and the adjacent `docs/render-env-setup.md`) to check for a *sibling*
issue nearby didn't happen with the same care as the first pass. Finding one bug doesn't mean
there's only one bug in the same document — the search radius shouldn't shrink just because the
first hit felt like closure.
