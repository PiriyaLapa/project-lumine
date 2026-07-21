# oracle-v2 (Arra Oracle v3) — Quick Reference
*Learned: 2026-06-05*

---

## What Is This?

**Arra Oracle v3** is an **MCP Memory Layer server** that provides Claude AI assistants with semantic knowledge management, learning capture, and consulting capabilities. It's the epistemological backbone of the Oracle ecosystem — a queryable knowledge system.

---

## Add to Claude Code

```bash
claude mcp add arra-oracle-v2 -- bunx --bun arra-oracle-v2@github:Soul-Brews-Studio/arra-oracle-v3#main
```

Or in `~/.claude.json`:
```json
{
  "mcpServers": {
    "arra-oracle-v2": {
      "command": "bunx",
      "args": ["--bun", "arra-oracle-v2@github:Soul-Brews-Studio/arra-oracle-v3#main"]
    }
  }
}
```

---

## Key MCP Tools (23 total)

### Search & Discovery
| Tool | Purpose |
|------|---------|
| `oracle_search` | Hybrid search (FTS5 + vector) across principles, patterns, learnings |
| `oracle_list` | Browse all documents, filter by type/date |
| `oracle_read` | Read full content by path or ID |
| `oracle_reflect` | Get random principle for reflection/alignment |

### Knowledge Capture
| Tool | Purpose |
|------|---------|
| `oracle_learn` | Add new pattern/learning to `ψ/memory/learnings/` |
| `oracle_supersede` | Mark old doc as superseded (Nothing is Deleted — old preserved) |
| `oracle_stats` | DB statistics: doc counts, indexing status |

### Session Continuity
| Tool | Purpose |
|------|---------|
| `oracle_handoff` | Write session context to `ψ/inbox/` for future sessions |
| `oracle_inbox` | List pending handoffs, newest-first with previews |

### Forum/Consultation
| Tool | Purpose |
|------|---------|
| `oracle_thread` | Send message to discussion thread; oracle auto-responds |
| `oracle_threads` | List threads by status (pending/active/closed) |
| `oracle_thread_read` | Read full message history |

### Tracing
| Tool | Purpose |
|------|---------|
| `oracle_trace` | Log a trace session with dig points (files, commits, issues) |
| `oracle_trace_chain` | Get full linked discovery chain |

---

## Tech Stack

- **Runtime**: Bun ≥1.2
- **DB**: SQLite + FTS5, Drizzle ORM
- **Vectors**: LanceDB / Chroma / Qdrant (optional, FTS5 fallback)
- **HTTP**: Elysia on port 47778
- **MCP**: Model Context Protocol SDK

---

## Philosophy Embedded in Design

1. **Nothing is Deleted** — Append-only. `oracle_supersede` preserves old docs with reason
2. **Patterns Over Intentions** — Read tools 4:1 over write tools
3. **External Brain, Not Command** — Mirror reality, don't prescribe

---

## What It Provides to Oracle Agents

1. Search millions of principles/patterns in milliseconds
2. Capture session discoveries to permanent vault
3. Preserve context between agent runs (handoff/inbox)
4. Async Q&A with oracle auto-response
5. Trace exploration sessions for reproducibility
6. Periodic alignment through reflection

---

## Version Policy

CalVer format: `v{yy}.{m}.{d}-alpha.{HMM}` — every merge to main auto-tags an alpha release.
