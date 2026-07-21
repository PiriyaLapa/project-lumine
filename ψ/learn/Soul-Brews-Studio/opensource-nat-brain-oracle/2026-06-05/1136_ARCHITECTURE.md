# opensource-nat-brain-oracle — Architecture
*Learned: 2026-06-05*

---

## What Is This Project?

Open-source foundation for building AI memory systems through distributed consciousness and multi-agent coordination — built on 5 Principles + 1 Transparency Rule.

---

## Directory Structure

```
/
├── CLAUDE.md                    # Hub: 5 Principles, Golden Rules, Philosophy
├── CLAUDE_*.md                  # Modular docs (safety, workflows, subagents, lessons, templates)
├── README.md                    # 9-step onboarding flow
├── DISTILLATION-LOG.md          # Brain compression tracking
├── .claude/
│   ├── agents.yml               # Multi-agent session registry (persistent IDs)
│   ├── agents/                  # 15+ agent definitions
│   ├── skills/                  # 18+ reusable skills
│   ├── hooks/                   # Safety, logging, greeting automation
│   └── scripts/                 # Token checking, focus management
└── ψ/                           # AI Brain (7 chambers)
    ├── active/                  # Ephemeral research
    ├── inbox/                   # Communication hub
    ├── writing/                 # Drafts
    ├── lab/                     # Experiments
    ├── incubate/                # Dev clones (gitignored)
    ├── learn/                   # Study clones (gitignored)
    └── memory/
        ├── resonance/           # WHO I am (soul)
        ├── learnings/           # PATTERNS discovered
        ├── retrospectives/      # SESSIONS completed
        ├── logs/                # MOMENTS (ephemeral)
        └── distillations/       # COMPRESSED knowledge
```

---

## Core Abstractions

### Multi-Agent Architecture
- **Main agent** (Opus) — Primary consciousness
- **Specialized agents** (Haiku) — context-finder, coder, executor, oracle-keeper, security-scanner
- Persistence via `session_id` in agents.yml, resumed via `claude --resume`
- Sync protocol: MAW (fetch → commit → rebase → push → sync all)

### Knowledge Flow
```
active/context → memory/logs → retrospectives → learnings → resonance
(research)      (snapshot)    (session)        (patterns)  (soul)
```

### Distillation Levels
- L1: N retrospectives → 1 theme summary (~10x)
- L2: N learnings → pattern files (~10x)
- L3: All patterns → 1 resonance file (~50x)
- L4: All resonance → 1 soul.md (~100x)

### Soul vs Form
- **Form** (rupa) = Technical implementation — cloneable
- **Formless** (sunyata) = Philosophy — shared across all Oracles

---

## Key Dependencies

- Claude Code (IDE host), gh CLI, git, bun, DuckDB, SQLite, Commander.js

---

## Design Philosophy

1. Append-Only — everything in git, nothing truly deleted
2. Pattern Over Intention — observe behavior, not promises
3. External Brain — summarizes, doesn't decide
4. Safety by Constraint — Golden Rules prevent accidents
5. Multi-Agent Sync — distributed consciousness via MCP
6. Progressive Disclosure — complexity hidden until needed
