---
pattern: after any session resume, compaction failure, or unexplained gap, verify current git/deployment/issue-tracker state before writing a retrospective, handoff, or taking any action that assumes continuity
date: 2026-08-22
source: "rrr: Lumine"
concepts: [session-continuity, verification, compaction, handoff, stale-context]
---

# Verify current state after any session gap before writing a retro or handoff

## What happened

A session's last real action was an `ExitPlanMode` call that the user interrupted. Immediately after, a `/compact` attempt failed ("You've hit your session limit"), and the same `/rrr and /forward` invocation followed. The session ID was unchanged, and the prior conversation was still fully present in context — every surface signal suggested this was a normal continuation.

It wasn't. Checking `git log`/`git status`/`gh issue list` before writing anything revealed that real time had moved forward by over three weeks, and `develop` now contained an entirely different, much longer commit history: a shipped release, a real production bug fix that superseded the diagnosis from the "current" session, new issues, unrelated documentation work — none of it visible in the conversation itself, only inferable from an ambient "this file changed on disk" notification and a direct state check.

## Why this generalizes

- A stable session ID and full conversational context are not proof that no time has passed or that no other work has happened. In any environment where other sessions, agents, or people can act on the same shared repository/system between your turns, "the conversation looks continuous" and "the world is unchanged" are independent facts.
- The failure mode is silent and confident: without an explicit check, you would produce a well-formed, internally-consistent retro or handoff that is simply wrong about present reality — and worse, a handoff is specifically the artifact meant to orient the *next* session, so a stale one actively misdirects future work rather than just being locally wrong.
- This is a scaled-up version of the "verify vs. inferred" pattern already familiar at the level of a single fact (a test count, a root-cause theory) — but applied to an entire session's worth of assumed context at once, which is much more expensive to get wrong.

## How to apply

- Before writing any retrospective, handoff, or status summary — especially after a `/compact`, a session resume, or any turn boundary where you can't be certain nothing happened in between — run cheap, direct checks: `git log`/`git status` for repo state, an issue/PR tracker query for current backlog, any deploy-status check available. This costs a handful of read-only commands.
- If those checks reveal a gap, don't paper over it or silently write around it — say so explicitly, scope the retro/handoff honestly to only what you actually know firsthand, and point whoever reads it toward the real current-state tooling (e.g., a `/recap`-style command) rather than trying to reconstruct the missing period from inference.
- Don't let a superseded diagnosis or fix quietly stand as if it were still the final word — if evidence shows your earlier conclusion was incomplete or wrong, name the supersession directly in the retro, even if the earlier work wasn't wasted (it may still have been correct and useful — the point is not to imply it was the whole story when it wasn't).

## Related

[[2026-07-29_verify-inferred-diagnoses-before-filing-not-only-when-asked-to-plan-a-fix]], [[2026-07-29_dont-elevate-a-subagents-historical-read-to-settled-fact]], [[2026-07-29_a-committed-fix-is-not-a-shipped-fix]] — the same family of "verify before asserting" lessons from the same underlying session, this one scaled up to whole-session context rather than a single claim.
