---
pattern: after a context compaction or session gap, verify a carried-forward summary against live repo state before continuing any plan it describes as still active
date: 2026-08-03
source: "rrr: Lumine"
concepts: [context-compaction, verification, plan-mode, git-reflog, stale-state]
---

# A stale summary can be fluent and wrong — verify after any gap

## What happened

A session's `.jsonl` file physically spanned 2026-07-20 to 2026-08-03, but five real days of work (a full feature shipped, a production bug diagnosed and fixed twice, a version release) happened in *other* session files in between. The `/compact` summary carried forward from the pre-gap conversation described an approved plan (a full backend sprint) as still "staged, uncommitted, on a feature branch" — stated with no hedge, because from that summary's own vantage point nothing had happened since. A Plan Mode plan file for that same work was still marked active.

Running `/recap` first (habit, not a deliberate check) surfaced a mismatch: the actual `develop` branch HEAD was unrelated work from days later. Verifying directly via `git branch -a`, `git reflog --all`, and `git log --all --diff-filter=A` showed the entire planned feature had already been committed, extended across three more branches, and merged weeks earlier. Continuing the stale plan would have meant re-implementing already-shipped work from a fictional starting state.

## Why this generalizes

- A summary's fluency and internal confidence have no relationship to its currency. A compacted summary describes the world *as of the last thing it saw* — it cannot know about work done in parallel sessions, by other tools, or by the human directly, and it will still state its (now-stale) picture as fact because that's genuinely all it has.
- Plan files and other "active" markers (a Plan Mode plan, a TODO list, a tracked feature branch name) are especially dangerous carriers of staleness: they look like live state but are just as frozen as the summary that reference them.
- The cost of not checking is not a small one — it's re-doing (or attempting to re-do) real, already-integrated work, potentially creating duplicate/conflicting branches or contradicting decisions made in the interim.

## How to apply

1. After any `/compact`, long gap, or session resumption where the carried-forward context describes ongoing/uncommitted work, run a cheap live check before continuing: `git branch -a`, `git log --oneline -5` on the relevant branches, `git reflog --all | grep <feature-name>`.
2. Treat "the plan file still exists and is marked active" as no stronger evidence of currency than the summary itself — a leftover artifact from before the gap is exactly what you'd expect to see whether or not the work is done.
3. If verification reveals the described state is stale, say so explicitly to the user and ask what to actually work on — don't silently patch the plan to fit reality, and don't silently continue as if nothing changed.
4. This generalizes beyond git: any external-state claim inherited from before a context gap (a deployed service's version, a ticket's status, a file's contents) deserves the same one-command verification before being treated as the basis for further work.

## Related

[[2026-07-29_dont-elevate-a-subagents-historical-read-to-settled-fact]] — same family (verify before trusting a historical read), applied here to an entire carried-forward session summary rather than a sub-agent's document research.
