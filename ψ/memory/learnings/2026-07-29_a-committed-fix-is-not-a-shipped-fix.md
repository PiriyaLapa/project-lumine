---
pattern: treat "committed but not pushed/merged/deployed" as an explicitly tracked, spoken-aloud state — not an implicit step you'll get back to
date: 2026-07-29
source: "rrr: Lumine"
concepts: [git-workflow, deployment, verification, race-condition, shipping-discipline]
---

# A committed fix is not a shipped fix

## What happened

Diagnosed and fixed a real production bug (a concurrent-request race condition in `DashboardScreen.tsx` — `useFocusEffect` and `RefreshControl`'s `onRefresh` both called an unguarded `fetchTasks`, letting two requests race and corrupt shared state). Implemented a `useRef`-based guard, verified the typecheck, committed it on a feature branch — and then the session moved on to other things without ever pushing the branch, opening a PR, or merging it.

Hours later, the exact same production bug recurred. The user asked me to check whether the fix had actually shipped before treating it as new. It hadn't: the commit had been sitting local-only the entire time. The fix itself was correct on the first try — the failure was entirely in the shipping discipline, not the diagnosis or the code.

The same near-miss happened again in the same session: a version-bump commit (`mobile/app.json` → v1.5.0) was made and, while writing the session retrospective, was caught sitting unpushed as well — the identical pattern about to repeat a second time before it was named explicitly.

## Why this generalizes

- "I fixed it" and "the fix is committed" and "the fix is shipped" are three different claims, and only the last one actually resolves a user-facing bug. It's easy to silently conflate the first two and stop tracking the gap to the third, especially mid-session when attention moves to the next task.
- In any project with a manual or multi-step deploy path (a PR review gate, a build-and-install step, anything short of true instant auto-deploy on commit), a local commit is invisible to everyone but the person who made it — including, apparently, that same person a few hours later.
- The cost of this gap compounds: a real user hits the still-broken system, has to notice and report it again, and the diagnosing agent has to re-verify state from scratch rather than just knowing the fix was already live.

## How to apply

- When a fix is committed, immediately decide out loud (or in whatever tracking mechanism the session uses) whether it ships now or is deliberately deferred — don't let "commit it and move on" become the default unstated end state.
- Before closing out any bug-fix task, explicitly state the fix's full status: committed / pushed / PR opened / merged / deployed. If any of those steps is pending, name it as pending — don't imply completion by simply stopping the conversation about it.
- When a previously-reported bug recurs, check ship status (branch/PR/merge/deploy state) before re-diagnosing the code from scratch — a full recurrence of the exact same symptom is more likely to mean "the fix never shipped" than "the fix didn't work," and that's a much cheaper thing to rule out first.
- If you catch this pattern about to repeat within the same session (e.g., another commit sitting unpushed while writing about the first instance), say so explicitly rather than letting a second silent gap form.

## Related

[[2026-07-29_verify-inferred-diagnoses-before-filing-not-only-when-asked-to-plan-a-fix]] and [[2026-07-29_dont-elevate-a-subagents-historical-read-to-settled-fact]] — same family of "verify, don't assume" lessons from the same day, applied here specifically to deployment/shipping state rather than root-cause claims.
