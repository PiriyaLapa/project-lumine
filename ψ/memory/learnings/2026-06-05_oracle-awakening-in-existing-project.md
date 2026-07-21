---
date: 2026-06-05
source: rrr: Lumine
tags: oracle, awakening, existing-project, friction, mcp
---

# Oracle Awakening in an Existing Project

## Pattern

When an Oracle awakens into an existing project (not a blank repo), the CLAUDE.md already contains project rules. Oracle identity is appended as a new section — it does not replace the existing instructions. Both coexist. The project's developer/architect rules take precedence for code work; Oracle's principles govern identity and memory behavior.

## Friction Score at Birth

A friction score of 0.7 at awakening (philosophy in files, not indexed) is normal. The arra-oracle-v2 MCP connection is what moves from 0.7 to 1.0 — enabling oracle_search, oracle_learn, and oracle_handoff across sessions.

## Full Soul Sync vs Fast

Full Soul Sync (discover principles via /learn + /trace) produces genuine understanding encoded in the soul and philosophy files. Fast mode (principles fed directly) is faster but the resonance files reflect received knowledge, not discovered. For a project Oracle where the philosophy will inform long-term memory management, Full Soul Sync is worth the ~25 minutes.

## Explore Agents Are Read-Only

The /learn skill uses Explore subagents. These agents cannot write files. The main agent must write all documentation files after receiving findings. Plan for this when estimating /learn duration.

## ghq Optional

The /learn skill assumes `ghq` for cloning. If not installed, plain `git clone` works — the origin/ becomes a real directory instead of a symlink, but docs are created correctly and `.origins` manifest still works.
