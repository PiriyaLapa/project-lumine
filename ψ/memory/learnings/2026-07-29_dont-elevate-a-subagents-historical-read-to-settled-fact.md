---
pattern: a sub-agent's read of historical documents is evidence, not confirmation — treat it as "likely" until live state agrees, and say so explicitly when the plan depends on it
date: 2026-07-29
source: "rrr: Lumine"
concepts: [verification, sub-agent-trust, deploy-config, plan-mode, honesty-over-confidence]
---

# Don't elevate a sub-agent's historical read to settled fact

## What happened

Planning a verification test, an Explore agent read three `ψ/` incident write-ups and reported "Render auto-deploys from `develop`, not `main`" — correcting the planner's own working assumption. The plan then proceeded on that basis: skipped a `develop`→`main` merge, declared the fix "very likely already live," and had the user install an APK and test against production. It turned out to be correct — the user later confirmed the deploy succeeded via Render's own dashboard — but the confidence expressed in the plan document at the time it was written wasn't actually earned by anything live; it was earned only by the user's confirmation that came several steps later.

## The pattern

Sub-agent research often surfaces documented history (past incidents, prior configuration notes, old lessons) as if it settles a live-system question. Historical documents can go stale — configuration changes, someone reconfigures a dashboard, a fact that was true in July may not be true in a later session. The sub-agent did its job correctly (accurately reporting what the documents said); the risk is in how the *coordinating* agent uses that report — treating "three past write-ups agree" as equivalent to "I checked the live system right now."

## Why this matters

When a plan's key premise rests on inference from historical documents rather than a live check, saying "very likely" in the plan file is honest — but that hedge needs to survive into execution and into how results get reported to the user, not evaporate once the plan is approved and things start moving. If the premise turns out wrong, the cost compounds: the user is told a fix is "live" and it isn't, and the actual verification step downstream (installing an APK, running a real test) ends up testing stale code without anyone noticing until something doesn't match.

## How to apply

- When a plan's central premise comes from a sub-agent reading documentation/history rather than live system state, name that source explicitly ("per three past incident write-ups," not just "Render deploys from develop") so the reader can weight it correctly.
- Look for a cheap live check to upgrade "likely" to "confirmed" before committing significant follow-on effort (installing builds, running tests) — if no live check is available, say so and flag the residual uncertainty rather than dropping the hedge silently.
- The actual verification event (a real log line, a user's own dashboard check) is what earns confidence — not the quality or count of historical documents that predicted it. Don't retroactively credit the inference once the real check succeeds; name the gap that existed at plan time regardless of the outcome.

## Related

[[2026-07-29_verify-inferred-diagnoses-before-filing-not-only-when-asked-to-plan-a-fix]] — same family of lesson (verify before stating as fact), applied here specifically to trusting a sub-agent's historical-document research as if it were a live check.
