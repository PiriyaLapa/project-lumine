# oracle-v2 (Arra Oracle v3) — Architecture
*Learned: 2026-06-05*

---

## What Is This?

Arra Oracle v3 is the **MCP memory layer** that powers Oracle AI assistants — a semantic search + learning system built on SQLite FTS5 + LanceDB vectors. An Oracle assistant is stateless; oracle-v3 is its persistent memory.

---

## System Layers

```
Claude Code (via MCP tools)          HTTP API consumers
         ↓                                   ↓
         oracle-v3 (this repo) ← The brain
                   ↓
         SQLite + FTS5 + LanceDB ← Persistent knowledge
```

---

## Directory Structure

```
src/
├── index.ts          # MCP server entry (23 tools)
├── server.ts         # HTTP API — Elysia, port 47778
├── tools/            # MCP tool handlers
├── routes/           # HTTP route handlers (25 groups, 55+ endpoints)
├── db/               # Drizzle ORM schema + migrations
│   └── schema.ts     # All tables
├── indexer/          # Knowledge indexing pipeline
├── vector/           # Pluggable vector store adapters
├── vault/            # Central knowledge repo management
├── forum/            # Thread-based Q&A system
├── trace/            # Discovery session logging
└── server/plugin/    # Route plugin system

cli/                  # arra-cli shell client
bin/                  # HTTP server binary
```

---

## Core Services

### 1. MCP Server — 23 Tools
Search, learn, forum, trace, handoff, inbox, supersede, reflect, schedule, verify, concepts, stats.

### 2. HTTP API — 55+ Endpoints
14 route groups: search, threads, traces, knowledge, files, health, dashboard, auth, schedule, oraclenet, plugins, settings, supersede, vector.

### 3. Indexer — Knowledge Pipeline
```
ψ/memory/ markdown files
  → OracleIndexer
  → SQLite FTS5 (sync, immediate)
  → LanceDB vector jobs (async daemon)
```

### 4. Vault CLI — Central Brain
```
oracle-vault init  → Clone central GitHub repo
oracle-vault sync  → Commit learnings to GitHub
oracle-vault pull  → Pull vault changes to local ψ/
```

---

## Hybrid Search Algorithm

```
Query → sanitize → FTS5 search (50 results, exponential decay score)
                → Vector search (50 results, cosine distance score)
      → Normalize both scores to [0,1]
      → Merge: score = 0.5*fts + 0.5*vector + 10% boost if in both
      → Deduplicate → return top 20
```

---

## Key Database Tables

| Table | Purpose |
|-------|---------|
| `oracle_documents` | Doc metadata, supersede chain |
| `oracle_fts` | FTS5 virtual table for keyword search |
| `indexing_jobs` | Per-doc per-model vector job queue |
| `forum_threads/messages` | Q&A with GitHub issue mirroring |
| `trace_log` | Discovery traces with dig points |
| `search_log/learn_log` | Audit trails |
| `schedule` | Calendar/appointments |

---

## Tech Stack

- **Runtime**: Bun 1.2+
- **Web**: Elysia (bun-native)
- **ORM**: Drizzle + SQLite FTS5
- **Vectors**: LanceDB (primary), ChromaDB (legacy)
- **Embeddings**: BGE-M3 default (multilingual Thai↔EN, 384-dim)
- **MCP**: Model Context Protocol SDK

---

## Philosophy Encoded in Design

| Principle | Implementation |
|-----------|----------------|
| Nothing is Deleted | `superseded_by` field, never hard delete |
| Patterns Over Intentions | Audit logs for all access and changes |
| External Brain, Not Command | Read tools 4:1 over write tools |
