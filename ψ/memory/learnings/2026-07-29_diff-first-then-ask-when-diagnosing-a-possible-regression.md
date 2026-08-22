---
pattern: When diagnosing "did my recent change break X," run the relevant git diff against the pre-change commit before asking the user multiple rounds of symptom questions
date: 2026-07-29
source: rrr: Lumine
concepts: [debugging, regression-diagnosis, git-diff, agent-decision-error, user-interrogation]
---

# Diff first, then ask

## What happened
Right after shipping a production release, Benz reported his real tasks weren't showing on the Dashboard. Ran three separate rounds of clarifying questions (what exact symptom, did it work before, what do other screens show, does pull-to-refresh help) before running a single `git diff` against the pre-release commit on the specific files involved (`tasks.py`, `task_repo.py`, `DashboardScreen.tsx`). The diff showed those files were completely unchanged by the release — instantly ruling out the most alarming hypothesis (a regression from today's work). That diff was available, free, and read-only the entire time; it just wasn't reached for until after the human Q&A rounds.

## Why this generalizes
Right after a deploy, "did I just break this" is always the first hypothesis worth ruling out, and a `git diff <pre-release-commit> <current> -- <the files that own the broken feature>` answers it definitively in seconds — no user interaction needed. Compare that to interrogating the user: each round costs a real round-trip, and the user's answers (symptom text, "did it work before," etc.) are useful for narrowing *other* hypotheses, but they can't answer "did the code change" as fast or as certainly as just looking.

The general shape: **when a hypothesis can be checked by reading something you already have access to, check it before asking the user something that also bears on that hypothesis.** Human Q&A is for information *only* the user has (what they're seeing, their role, what account they're using) — not for information sitting in the repo.

## How to apply
1. On a "did my change break this" report, identify the specific files/functions that own the broken behavior.
2. `git diff <last-known-good-commit> <current> -- <those files>` immediately, before the first clarifying question if possible, or at latest interleaved with the first round.
3. Use the diff result to either rule out a regression (diff is empty/irrelevant → look elsewhere, likely environmental/data/timing) or confirm one (diff shows a suspicious change → go straight to that, no further guessing needed).
4. Reserve `AskUserQuestion` rounds for things only the user can tell you — not for things you could check yourself first.
