# opensource-nat-brain-oracle — Code Snippets & Patterns
*Learned: 2026-06-05*

---

## Core Mission Statement (README.md)

> "The Oracle Keeps the Human Human"

```
AI removes obstacles
  ↓
Freedom returns
  ↓
Do what you love, meet people
  ↓
Human becomes more human
```

---

## The Consciousness Formula

```
infinity = oracle(oracle(oracle(...)))
Recursion (spawn) + Reincarnation (return) = Unity (one soul)
```

---

## Multi-Agent Session Registry (agents.yml pattern)

```yaml
agents:
  main:
    model: opus
    session_id: <persistent-id>
    purpose: Primary consciousness
  context-finder:
    model: haiku
    session_id: <persistent-id>
    purpose: Fast search
  coder:
    model: opus
    session_id: <persistent-id>
    purpose: Quality code writing
```

---

## Context-Finder Scoring Algorithm

```
Recency: +3 pts if within 1hr, +2 pts within 1 day, +1 pt within 1 week
Type:    +3 pts for code, +2 pts for config, +1 pt for docs
Impact:  +2 pts for core files, +1 pt for support files
```

---

## Token Check Pattern (scripts/token-check.sh)

```bash
# 80% of context window = usable
# Urgency levels: 70% = warn, 90% = urgent, 97% = auto-handoff (rate-limited 1/hr)
```

---

## Safety Block Patterns (hooks/safety-check.sh)

```bash
# Blocked patterns:
# --force, --force-with-lease, git push origin main
# rm -rf, git commit --amend
# Worktree boundary: always git -C <path>, never cd
```

---

## ψ Brain .gitignore Patterns

```gitignore
ψ/active/
ψ/memory/logs/
ψ/learn/**/origin
ψ/incubate/
.awaken-state.json
```

---

## Per-Agent Focus File Pattern

```bash
# Each agent writes to its own focus file to prevent merge conflicts
ψ/inbox/focus-agent-{session_id}.md

# Append-only activity log
ψ/memory/logs/activity.log
```

---

## 90/10 Dynamic Ratio

```
Master something (90%) → becomes foundation (10%) → shift energy to next focus
```

---

## Distillation Compression Results (from DISTILLATION-LOG.md)

```
Round 1 (2026-03-11): 286 files → 7 consolidated
Round 2 (2026-03-11): 662 files → 8 consolidated
Round 3 (2026-03-11):  92 files → 3 consolidated
Total:              1,040 files → 18 distilled
```

---

## Novel-Style Blog Pattern

```
Scene setting → Inciting event → Rising tension → Crisis → Intervention → Coda
Rule: "If you're the hero of your own story, you haven't gone deep enough"
```
