---
date: 2026-06-10
source: rrr: Lumine
tags: oracle, pm-agent, memory, conflict, hotcache, project-status
---

# Dual Memory Sources Can Disagree on Project Status

## Pattern

A project can have two memory layers that drift independently:
1. **In-repo memory** (CLAUDE.md "Current Phase", `.claude` auto-memory) — tends to reflect the last in-repo session's understanding.
2. **External SecondBrain wiki** (hotcache + entity pages) — tends to reflect the latest *strategic* decision, which may have been made in a different project's session.

In Lumine's case, in-repo memory said "no open blockers, Stage 5 in progress." The wiki said Stage 5 gate closed 2026-05-31 *and* a 2026-06-04 note paused the entire project in favor of a different project (Sales Report Automation). Both can be technically true at different layers — but only one should drive "what's next."

## When a PM-style persona is invoked

`agents/pm_agent.md` (and similar role files) specify "Read First — Every Session" lists that include external wiki paths. These protocols exist precisely to catch this kind of drift. Skipping straight to in-repo memory for a "what's next" question can produce an answer that's locally correct but globally stale.

## Conflict reporting, not resolution

Per CLAUDE.md: "If you find a conflict or gap... STOP and tell me. Do not invent solutions. Do not fill gaps silently." When in-repo and external memory disagree on something as fundamental as "is this project active," the right move is to present the conflict with dates and let the architect decide — not to pick the more recent timestamp, the more exciting option, or the one that lets the session "produce something."

## Suspicious timing is a flag, not a verdict

A pause note dated one day before a multi-hour Oracle awakening ritual *in the paused project* is worth surfacing as-is. Resist the urge to narrate a theory (e.g., "the awakening doesn't count as feature work so it's fine") — that's the architect's interpretation to make, not the AI's to assume.
