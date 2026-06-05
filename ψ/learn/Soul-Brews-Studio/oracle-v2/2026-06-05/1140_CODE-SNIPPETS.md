# oracle-v2 (Arra Oracle v3) — Code Snippets & Patterns
*Learned: 2026-06-05*

---

## Dual Entry Points

```typescript
// src/index.ts — MCP Server (stdio transport)
// Either proxies to HTTP server or runs embedded SQLite + vector store

// src/server.ts — HTTP API (Elysia, port 47778)
```

---

## Supersede Pattern (Nothing is Deleted)

```typescript
// oracle_documents table
supersededBy: text("superseded_by"),
supersededAt: integer("superseded_at"),
supersededReason: text("superseded_reason"),
// Old documents preserved — never deleted, just marked superseded
```

---

## Tool Aliasing (3 generations supported)

```typescript
// All map transparently to oracle_*:
arra_search   → oracle_search
muninn_search → oracle_search
oracle_search → oracle_search (current)
```

---

## Tool Context Injection Pattern

```typescript
// All handlers receive unified context:
{ db, vectorStore, repoRoot }
```

---

## FTS5 Query Sanitization

```typescript
// Removes 25+ special chars to prevent parse errors before FTS5 query
```

---

## Pluggable Vector Store Adapters

```typescript
// Supported backends:
// ChromaDB, LanceDB, sqlite-vec, Qdrant, Cloudflare Vectorize

// Default embedding model: bge-m3 (1024-dim, multilingual Thai↔EN)
// Other models: qwen3 (4096-dim), nomic (768-dim, fast)
```

---

## Per-Model Job Queue Pattern

```typescript
// indexingJobs table: per-doc per-model queue
// Allows adding/removing embedding models without schema changes
// FTS indexes first, vector embedding queued async
```

---

## Hot-Reload Tool Config

```typescript
// Watches ψ/config.json
// Mutations happen in-place via Set.clear/add
// Tools checked at request time — no restart needed
```

---

## HTTP Security Headers

```typescript
"X-Frame-Options": "DENY"
"Content-Security-Policy": "..."
"X-Content-Type-Options": "nosniff"
// Private Network Access: Chrome 117+ PNA header support
```

---

## Key Database Tables

| Table | Purpose |
|-------|---------|
| `oracle_documents` | Document index with supersede chain |
| `indexingJobs` | Per-doc per-model embedding queue |
| `forumThreads/Messages` | Q&A with GitHub issue mirroring |
| `searchLog/learnLog` | Audit trails |
| `documentAccess` | Access tracking |

---

## CLI Commands

```bash
arra-cli plugin   # manage plugins
arra-cli session  # inspect sessions
arra-cli reindex  # trigger FTS/SQLite reindex
arra-cli config   # manage API targets
```

---

## Run Locally

```bash
bun run dev      # MCP server (stdio)
bun run server   # HTTP API (port 47778)
bun run index    # Knowledge indexer

bun test         # All tests
bun db:push      # Apply schema
bun db:studio    # Drizzle Studio GUI
```
