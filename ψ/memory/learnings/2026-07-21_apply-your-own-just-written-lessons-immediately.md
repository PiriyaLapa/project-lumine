---
pattern: When you've written a lesson about escalating to a stronger fix after a specific failure pattern, apply it explicitly the very next time the same symptom recurs in the same session — don't re-diagnose from scratch and drift back into weaker fixes the lesson exists to skip.
date: 2026-07-21
source: rrr: Lumine
concepts: [self-evaluation, escalation-strategy, expo-go, environment-troubleshooting]
---

# Apply your own just-written lessons immediately, not just in future sessions

## What happened

Earlier in this session, after a long troubleshooting arc, wrote a lesson: "when a
warm fix (relaunch, reinstall) has already proven unreliable, escalate directly to
the coldest available fix (full VM/emulator reboot) rather than trying more warm
variations." That lesson was written specifically because ~10 warm-fix attempts had
been tried before cold boot finally worked.

About an hour later, in the same session, the identical crash symptom
(`ClassCastException`/`NullPointerException` on `UIManager` in Expo Go) came back
while trying to switch test accounts. Instead of going straight to a cold boot
(the fix already known to work, from one hour prior, in this same session), the
first move was `pm clear host.exp.exponent` — a fix that hadn't even been tried
before, but was still fundamentally in the "warm" tier the lesson was about. Only
after that failed did the cold boot get tried.

## The generalizable rule

Lessons written mid-session are not just for "next time" in some future session —
they apply to the very next occurrence of the same symptom *in the current
session*, and are easy to forget under the pressure of a new instance of an old
problem, especially when the new instance has slightly different surface details
(this time it was about switching accounts, not initial app testing) that make it
feel like a "different problem" worth fresh diagnosis. Before re-diagnosing a
familiar failure signature, explicitly check: "did I already write a lesson about
this exact symptom earlier in this conversation?" If yes, apply it directly instead
of re-deriving the escalation ladder from scratch.

## Secondary finding: cold boot is not deterministic

The same cold-boot fix that worked cleanly on the first attempt earlier in the
session did *not* reproduce the fix on its own the second time — it took cold boot
*combined with* a fresh Expo Go uninstall/reinstall to get a clean load. Treat a
single successful fix for a flaky native-bridge crash as having raised the odds,
not as a deterministic solution — be ready to escalate further (e.g. stack cold
boot + reinstall) if the same fix doesn't reproduce cleanly on a later occurrence.
