---
pattern: When a user names a specific external tool by brand (Draw.io, Lucidchart, etc.), check tool availability via ToolSearch before describing any plan — not after starting to plan
date: 2026-08-17
source: rrr: Lumine
concepts: [tool-capability-verification, external-tool-integration, ask-before-assuming]
---

# Check tool availability before planning around a named external tool

## What happened

User asked to "draw all diagrams by access into my github and project directory by using tool for drawing such Draw.io (diagrams.net) and Lucidchart." I only ran `ToolSearch` for a Draw.io/Lucidchart connector *after* the ask landed — found neither exists as an MCP connector — and then had to explain the constraint and negotiate a fallback path (`.drawio` XML files the user imports manually) instead of opening with the constraint already known.

## Why this matters

Finding out a named tool isn't available *after* already engaging with the request forces a mid-task course-correction the user has to sit through. It's a small tax each time, but it's avoidable: tool availability is checkable in one call, before any plan is described.

## The generalizable rule

The moment a request names a specific external tool, product, or service by brand — before sketching any approach, before promising an outcome — run `ToolSearch` (or equivalent capability check) for that tool. Let the result shape the plan from the very first sentence, rather than discovering the gap mid-explanation and backfilling.

This is different from generic capability uncertainty ("can I do X at all") — it's specifically about named third-party tools, where the user has a concrete expectation of what integration should look like, and a wrong assumption either way (assuming it works, or assuming it doesn't) costs a correction cycle either way.

## How to apply

- Named tool in a request → `ToolSearch` first, plan second.
- If no connector exists, don't silently substitute an adjacent tool (e.g. swapping in Miro because it's available) — surface the gap and the real options (manual credential setup, file-based workaround, different tool entirely) and let the user pick, especially when the substitution changes what the user actually gets.
- This generalizes past diagramming tools — same applies to any named SaaS/API a user references assuming I have access (Jira, Slack, a specific analytics platform, etc.).

See also: [[project_lumine_status]] for the diagrams delivered under this constraint.
