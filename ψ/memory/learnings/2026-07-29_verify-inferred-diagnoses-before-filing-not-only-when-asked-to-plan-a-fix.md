---
pattern: verify an inferred (not confirmed) diagnosis against actual code before filing the issue, not only when later asked to plan a fix for it
date: 2026-07-29
source: "rrr: Lumine"
concepts: [diagnosis, root-cause-investigation, plan-mode, bug-triage, honesty-over-momentum]
---

# Verify inferred diagnoses before filing, not only when asked to plan a fix

## What happened

A prior session diagnosed an empty-Dashboard symptom as a "cold-start JWT race" — but that session's own handoff explicitly flagged the conclusion as *inferred, not confirmed* (no log access to the actual failed request). The next session filed a GitHub issue (#29) stating that theory as the "suspected cause" in concrete technical terms, without re-checking it against the code first.

Only when the user asked `/plan Show me the plan how do you fix it?` did an Explore agent actually verify the theory — and it didn't hold up: the token write was fully `await`ed before navigation, and the axios client had no in-memory cache to race against. A second investigation into a backup backend theory also came up empty. Two rounds of "the theory doesn't hold" later, the honest move was to add diagnostic logging and wait for recurrence, not to invent a third guess.

## The pattern

An inferred diagnosis carried in memory/handoff notes can silently harden into "fact" the next time it's referenced — especially when writing something as consequential as a public issue tracker entry. The caveat ("I don't have logs, this is inferred") needs to travel with the claim into every place the claim gets restated, not just live in the original diagnostic note.

## Why this matters

Filing a bug with a stated root-cause theory that turns out to be false costs real friction later: someone (a future session, a teammate, future-you) reads the issue, trusts the stated mechanism, and either builds a fix for a non-existent bug or has to spend a round-trip discovering the theory was never confirmed. The fix — asking "do I actually know this, or did I infer it?" before writing it down as fact — costs nothing and prevents that.

## How to apply

- Before filing an issue, a status note, or any other durable artifact based on a previous session's conclusion, check whether that conclusion was marked "confirmed" or "inferred/hypothesized" in its source. If inferred, either verify it fresh or state the uncertainty explicitly in the new artifact ("suspected, unconfirmed — see below for what would confirm/deny it").
- When a stated premise turns out false during planning, don't quietly swap in a different plausible theory to keep momentum — surface the finding and ask how to proceed. Two ruled-out theories and an honest "we don't know, here's how we'll find out" is a better outcome than a third guess dressed up as a fix.
- When no root cause is confirmed, instrumentation (logging that captures the exact signal needed to test the next theory) is a legitimate and often the only defensible deliverable — it's not a consolation prize for failing to find the bug.

## Related

[[2026-07-29_diff-first-then-ask-when-diagnosing-a-possible-regression]] — the immediately preceding session's lesson about diffing code before trusting a regression theory; this lesson extends that principle to the moment of *filing* the theory, not just diagnosing it.
