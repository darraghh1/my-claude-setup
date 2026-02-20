# Team Agent Context Research

> Tested 2026-02-20 on Claude Code with Opus 4.6. Findings may change as Claude Code evolves.

## Background

Team agents (teammates spawned via the `Task` tool) operate in a different context than the parent session. This document records what context teammates actually receive and how we compensate for gaps.

## Test Method

1. Added a unique marker (`purple-elephant-42`) to CLAUDE.md mid-session
2. Spawned a `general-purpose` teammate with instructions to report all available context
3. Compared the teammate's report against the parent session's context

## Findings

### What teammates receive

| Context Source | Received? | Fresh from disk? | Notes |
|---|---|---|---|
| **CLAUDE.md** | Yes | **No** — parent's cached version | Changes made mid-session are invisible to teammates |
| **Rules** (`.claude/rules/`) | Partial — 3 of 15 observed | No — parent cache | Only `git-workflow.md`, `mcp-tools.md`, `security.md` were reported. May be selective injection or summarisation artifact |
| **Skills registry** | **No** | n/a | Teammates see zero registered skills. The `Skill` tool exists but the registry listing available skills is absent |
| **Skills (preloaded)** | Yes, if `skills:` in agent frontmatter | n/a | Agent-typed subagents (e.g., `builder`) get their `skills:` field preloaded into system prompt |
| **MCP tools** | **No** | n/a | Zero MCP tools available. Teammates cannot use Playwright, Tavily, Context7, etc. |
| **MEMORY.md** | Yes | No — parent cache | Auto memory is injected |
| **SubagentStart hook** | Yes | **Yes — fresh** | Only injection point that runs at spawn time. Reads from disk, not cache |
| **Working directory** | Yes | Yes | Correct working directory inherited from parent |
| **Git status** | Yes | No — snapshot from session start | Stale by the time teammates are spawned |
| **Environment info** | Yes | Yes | Platform, shell, model identification |

### What teammates DON'T receive

| Missing | Impact | Mitigation |
|---------|--------|------------|
| **Skill registry** | Teammates don't know what skills are available to invoke | Pass `Skill: {name}` explicitly in spawn prompt; inject skill list via SubagentStart hook for builder agents |
| **MCP tools** | No Tavily, Playwright, Context7, etc. | Teammates use `WebSearch`/`WebFetch` instead, or parent handles MCP-dependent work |
| **Fresh CLAUDE.md** | Mid-session edits invisible | SubagentStart hook injects critical rules (runs fresh at spawn time) |
| **Most rule files** | Only ~3 of 15 rules observed | SubagentStart hook injects condensed rule summary; enhance to inject full rule content for builder/validator agents |

## Architecture

```
Parent session (full context)
  │
  ├── CLAUDE.md (loaded at session start, cached)
  ├── 15 rule files (loaded at session start, cached)
  ├── 23 skills (registry available)
  ├── 5 MCP servers (tools available)
  ├── MEMORY.md (loaded at session start)
  │
  └── Spawns teammate ──→ Teammate context:
                            ├── CLAUDE.md (parent's stale cache)
                            ├── ~3 rule files (partial, stale)
                            ├── Agent definition (if agent-typed)
                            ├── Preloaded skills (from agent's skills: field)
                            ├── SubagentStart hook injection (FRESH)
                            ├── MEMORY.md (stale cache)
                            ├── Skill tool (available, but no registry)
                            └── NO MCP tools
```

## Key Insights

### The SubagentStart hook is the only fresh injection point

Everything else comes from the parent's cached context. The hook runs at spawn time and reads from disk, making it the only way to inject up-to-date information.

### Skill invocation works without the registry

The `Skill` tool resolves skill names to disk paths. A teammate can call `Skill({ skill: "postgres-expert" })` successfully even without seeing the registry — but only if it **knows** to invoke that specific skill. Without the registry, the teammate won't discover skills on its own.

**Solution:** The orchestrator extracts the `skill:` field from the phase frontmatter and passes it explicitly in the builder's spawn prompt as `Skill: {skill-name}`. The builder agent's instructions tell it to invoke whatever skill is specified. This removes the discovery problem entirely.

### Agent-typed subagents get more context

Spawning with `subagent_type: "builder"` loads the `team/builder.md` agent definition as system prompt, including its `skills: [builder-workflow]` preloaded skill. A `general-purpose` subagent gets none of this.

### Rules are the biggest gap

The condensed bullet list in the SubagentStart hook covers ~11 patterns, but the full rule files contain detailed guidance on database patterns, form handling, testing, security, and more. Builders working on database migrations without `database.md` rules will miss conventions like `security_invoker` views, migration naming, and RLS helper functions.

**Solution:** Enhance the SubagentStart hook to inject rule file content for builder and validator agents.

## Recommendations

### Implemented

1. **Orchestrator passes `Skill: {name}` in spawn prompt** — builder no longer needs to discover the skill from phase frontmatter
2. **Builder agent defers to builder-workflow** — removed competing 7-step workflow from agent definition
3. **Builder-workflow acknowledges spawn prompt skill** — uses `Skill:` field if present, falls back to frontmatter

4. **Enhanced SubagentStart hook** — tiered context injection based on agent type:

| Agent Type | Injection Tier | Content | Token Cost |
|---|---|---|---|
| `builder`, `validator` | **Full** | Compact rules + skill registry + 13 rule files (read fresh from disk) | ~9.5K tokens (~4.7% of 200K) |
| All others | **Compact** | Condensed 11-bullet rule summary | ~180 tokens |

The hook reads rule files from `~/.claude/rules/` at spawn time, skipping `git-workflow.md` (builders don't commit) and `mcp-tools.md` (builders don't have MCP tools). This is the only injection point that provides fresh content — everything else comes from the parent's stale cache.

5. **Phase template updated** — added `service-builder` and `none` to the `skill:` options list in PHASE-TEMPLATE.md

### Still to test

1. **Agent-typed subagent context** — verify a `builder` subagent sees its preloaded `builder-workflow` skill and can invoke domain skills via the `Skill` tool
2. **Skill tool resolution** — confirm `Skill({ skill: "postgres-expert" })` works for subagents even without the skill registry in their system prompt

## Open Questions

- Why were only 3 of 15 rules observed in the initial test? Likely the general-purpose teammate was summarising selectively — the full CLAUDE.md + rules blob is injected but lengthy. The enhanced hook now injects rules independently of the parent cache.
- Does the `Skill` tool work for teammates in practice? The tool exists in their tool list, but the registry might be needed for resolution. Needs testing with an agent-typed subagent.
- Would preloading more skills via the `skills:` field be more reliable than on-demand invocation? Preloading guarantees availability but costs tokens (each preloaded skill's full SKILL.md is in the system prompt). On-demand invocation is cheaper but depends on the `Skill` tool resolving correctly.
