---
pattern: When a live failure's symptom matches something already documented in memory (from any prior session, not just this one), check memory for the exact fix before the first retry — not after several retries of the already-known-to-be-flaky approach
date: 2026-07-26
source: rrr: Lumine
concepts: [self-evaluation, memory-recall, escalation-strategy, expo-go, environment-troubleshooting]
---

# Recall a matching memory before the first retry, not after several

## What happened

Hit Expo Go's documented `UIManager not properly initialized` native-bridge crash — a failure
signature already described in this vault from two prior sessions, including the specific detail
that a "third distinct launch mechanism via Expo Go's own native 'Enter URL manually' UI" was what
eventually broke the pattern last time. That exact learning file had already been read earlier in
the same session (during recap and again during planning context).

When the crash actually hit live, the first move was still `am start -a android.intent.action.VIEW
-d "exp://..."` — the same deep-link approach already flagged as unreliable — retried six times,
including through a full cold AVD reboot (itself a documented escalation step), before switching to
the technique the memory file had already named: launching Expo Go's own home screen and tapping
"Recently opened" rather than deep-linking in externally. That one attempt succeeded immediately.

Six retries of a known-flaky approach were spent before reaching for a fix that was already sitting
in memory, read earlier in the same session, and directly named for this exact symptom.

## The generalizable rule

Having read a relevant memory earlier in a session is not the same as recalling it under pressure
when its symptom actually appears. When a live failure's error text, stack trace shape, or visible
symptom matches something already documented — from this session *or any prior one* — the first
response should be an explicit check ("have I already written down the fix for exactly this?")
before the first retry, not a default reach for the most obvious variation of the approach that just
failed. This generalizes the existing lesson about applying same-session lessons immediately
([[2026-07-21_apply-your-own-just-written-lessons-immediately]]) to cross-session memory: the gap
between "I read this" and "I retrieved this at the moment it mattered" is exactly where the wasted
retries happen, and it doesn't matter whether the memory is an hour old or a week old.

Practically: when a failure recurs that feels "familiar," pause before the first retry and grep
memory/learnings for the symptom's distinctive terms (exception class name, error string, tool name)
rather than trusting recall from having read it earlier in the same conversation.
