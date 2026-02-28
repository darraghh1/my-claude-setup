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
| **Skills (preloaded)** | **No** — `skills:` frontmatter NOT preloaded | n/a | ~~Agent-typed subagents get skills preloaded~~ **TESTED 2026-02-27: `skills:` field is advisory only. Agents must explicitly invoke via `Skill()`.** |
| **MCP tools** | **Yes** — available regardless of `tools:` allowlist | n/a | ~~Zero MCP tools available~~ **TESTED 2026-02-27: MCP tools bypass agent `tools:` frontmatter entirely.** |
| **MEMORY.md** | Yes | No — parent cache | Auto memory is injected |
| **SubagentStart hook** | **No** — does NOT fire for team teammates | n/a | ~~Only injection point that runs at spawn time~~ **TESTED 2026-02-27: Hook fires for non-team subagents only. Team teammates (spawned via Task with `team_name`) never receive hook output.** |
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
                            ├── NO preloaded skills (skills: field is advisory only)
                            ├── NO SubagentStart hook (doesn't fire for teammates)
                            ├── MEMORY.md (stale cache)
                            ├── Skill tool (available — can invoke skills explicitly)
                            └── MCP tools (available — bypass tools: allowlist)
```

## Key Insights

### ~~The SubagentStart hook is the only fresh injection point~~ (DISPROVEN)

**TESTED 2026-02-27:** SubagentStart hooks do NOT fire for team teammates. The workaround is self-loading context: workflow skills include a Step 0 that reads critical rule files (`coding-style.md`, `patterns.md`) as the agent's first action.

### Skill invocation works without the registry

The `Skill` tool resolves skill names to disk paths. A teammate can call `Skill({ skill: "postgres-expert" })` successfully even without seeing the registry — but only if it **knows** to invoke that specific skill. Without the registry, the teammate won't discover skills on its own.

**Solution:** The orchestrator extracts the `skill:` field from the phase frontmatter and passes it explicitly in the builder's spawn prompt as `Skill: {skill-name}`. The builder agent's instructions tell it to invoke whatever skill is specified. This removes the discovery problem entirely.

### Agent-typed subagents get more context

Spawning with `subagent_type: "builder"` loads the `team/builder.md` agent definition as system prompt. However, the `skills: [builder-workflow]` field is **advisory only** — the skill is NOT preloaded. The agent body must instruct the builder to invoke it explicitly via `Skill()`. A `general-purpose` subagent gets none of this.

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

1. ~~**Agent-typed subagent context** — verify a `builder` subagent sees its preloaded `builder-workflow` skill~~ **TESTED 2026-02-27: `skills:` NOT preloaded. Agents must invoke explicitly.**
2. ~~**Skill tool resolution** — confirm `Skill({ skill: "postgres-expert" })` works for subagents~~ **TESTED 2026-02-27: Works. Skill tool resolves without registry.**

## ~~Open Questions~~ Resolved Questions (2026-02-27)

- ~~Why were only 3 of 15 rules observed?~~ **Answer:** Only `alwaysApply: true` and no-frontmatter rules auto-load (5 rules). `paths:`-scoped rules do NOT load for teammates.
- ~~Does the Skill tool work for teammates?~~ **Answer:** Yes. `Skill({ skill: "name" })` resolves correctly for teammates even without the skill registry listing.
- ~~Would preloading skills be more reliable?~~ **Answer:** Moot — `skills:` frontmatter doesn't actually preload. The working pattern is: agent body says "invoke X as first action" → agent calls `Skill()` → skill content loads.
- **`tools:` frontmatter** is also advisory only — agents can call any tool regardless of allowlist. The `subagent_type` system definition determines real boundaries.
