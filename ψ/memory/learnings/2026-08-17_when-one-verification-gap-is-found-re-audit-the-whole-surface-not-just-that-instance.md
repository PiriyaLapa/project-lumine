---
pattern: When a user catches one instance of narrow-scope verification (e.g. one missing feature in a diagram/doc set), re-scan the entire surface you're already looking at for the same failure mode — don't just fix the reported instance.
date: 2026-08-17
source: rrr: Lumine
concepts: [verification-scope, diagramming, self-audit, recurring-gap]
---

# Re-audit the whole surface when one verification gap is found, not just the reported instance

## What happened

Built 6 interview-prep diagrams for Lumine, verified them against the live codebase (models, routers) for field/entity accuracy. The user later asked "why couldn't I see the Auto-Touch feature" — a real, fully-built subsystem (5 endpoints, AI drafting, LINE/SMTP dispatch, a send gate) that had been verified narrowly (schema field accuracy) but never audited for entirely missing *features*.

Fixed it: read the real Auto-Touch code paths, added coverage across Use Case/Architecture/BPMN/Sequence, split the DFD into proper levels. Two commits landed. Only while writing the session retrospective — after both commits — did a second gap surface: `routers/reports.py` (KPI/dashboard reports) was sitting in the *same* Architecture-tab router list (`auth, upload, tasks, evidence, customers, auto_touch, reports`) that had just been re-verified for Auto-Touch, and it was never diagrammed either. It was one line away from the exact box being edited, and it wasn't checked.

## Why this matters

The first gap (Auto-Touch) was itself already a "verified narrowly, not the whole surface" failure. When the user reports one instance of that failure mode, the instinctive move is to fix the one reported thing and treat it as resolved. But if verification was narrow once, it was probably narrow elsewhere too — the same router list, the same file, the same session. Fixing only the reported instance leaves the sibling gaps for the user to find one at a time, each requiring a new "why isn't X in here" question, when a single re-scan of the surface already open in the editor would have caught them together.

## How to apply

When a user points out "you missed X" in something you verified/audited: before fixing X, re-scan the *entire list or surface X came from* for other members with the same property. If X was "a router not represented in the diagram," check every other router in the same router list, not just X. Do this in the same pass, before committing — not as a follow-up once the retro or a later session surfaces it. Cheap to do while the context is loaded; expensive to have the user find each one separately. Related: [[2026-08-17_check-tool-availability-before-planning-around-a-named-external-tool]] (same session-family, verify-before-committing theme).
