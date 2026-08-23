---
pattern: when new evidence surfaces mid-session that could widen an already-approved plan's scope, explicitly re-confirm scope with the architect before writing the new plan — don't silently inherit the old boundary
date: 2026-08-14
source: "rrr: Lumine"
concepts: [plan-scope, evidence-gap-logging, race-condition, missing-index, verification]
---

# New evidence should reopen plan scope, not inherit the old boundary

## What happened

On 2026-08-03, a plan was approved for the Dashboard "Could not load your tasks" bug: add a backend global exception handler and surface the real HTTP status code in the on-screen error — diagnostic only, scoped narrowly because no confirmed root cause existed yet.

On 2026-08-14, asked to investigate root cause with a specific theory in hand ("it broke when Auto-Touch was added"), git archaeology found real, load-bearing evidence: a concurrent request (`fetchAutoTouchStatus()`) added the day before the bug was first reported, plus a confirmed missing index (`follow_up_tasks.idoc_number`) making that concurrent request ~4x heavier than its neighbor — a plausible direct mechanism, not just a diagnostic gap. Separately, the existing GH #29 diagnostic logging was found to be structurally unreachable on any failure path (placed right before the success-path return), which explained why two prior attempts to pull real log evidence had come up empty.

When the user then said "go ahead, implement the plan," the plan was written strictly against the old 08-03 diagnostic-only boundary — without asking whether the new evidence (missing index, concurrent call) should now be folded into the fix itself. The plan was rejected via `ExitPlanMode` with no reason given.

## Why this generalizes

- An approved plan's scope reflects what was known *at approval time*. If new evidence emerges afterward that changes the causal picture, the old scope is no longer necessarily the right scope — but it's also the path of least resistance, since it's already "approved" and requires no new confirmation.
- Silently inheriting the old boundary optimizes for not re-litigating a decision, at the cost of possibly building the wrong thing when the premise has changed. This is a narrower, more specific case of the general "verify before continuing a carried-forward plan" pattern (see [[2026-08-03_a-stale-summary-can-be-fluent-and-wrong-verify-after-any-gap]]) — but here the plan itself wasn't stale, the *evidence behind it* was incomplete when it was written.
- A bare "go ahead, implement the plan" from the user is ambiguous between "implement exactly what we already approved" and "implement whatever the right plan now is, given everything we've learned." Defaulting to the narrower reading without checking is itself a silent assumption.

## How to apply

1. Before writing an implementation plan that references or extends a previously-approved plan, check whether anything material has changed since approval (new evidence, new findings, new constraints).
2. If something material has changed, use AskUserQuestion to explicitly ask whether scope should expand, before writing the plan file — don't just silently keep the old boundary because it's already blessed.
3. This is cheap insurance: one clarifying question costs far less than a rejected plan and a lost round-trip, especially when the session already did the work to surface the new evidence.
4. Note the inverse failure mode too: don't scope-creep into fixing everything found during investigation without confirmation either — the fix is to *ask*, not to unilaterally pick either the narrow or the wide scope.

## Related

[[2026-08-03_a-stale-summary-can-be-fluent-and-wrong-verify-after-any-gap]] — same family (verify before trusting a carried-forward artifact), applied here to a plan's scope rather than a session summary.
