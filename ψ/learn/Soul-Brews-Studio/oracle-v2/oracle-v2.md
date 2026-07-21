# oracle-v2 (Arra Oracle v3) — Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/Soul-Brews-Studio/oracle-v2

## Explorations

### 2026-06-05 1140 (default — 3 agents)
- [Architecture](2026-06-05/1140_ARCHITECTURE.md)
- [Code Snippets](2026-06-05/1140_CODE-SNIPPETS.md)
- [Quick Reference](2026-06-05/1140_QUICK-REFERENCE.md)

**Key insights**:
1. oracle-v2 is the MCP memory layer — an Oracle assistant is stateless; this is its persistent brain
2. 23 MCP tools cover search, learn, handoff, forum, trace — installed via `claude mcp add`
3. Hybrid FTS5 + vector search scores better than either alone; embeddings are async (non-blocking)
