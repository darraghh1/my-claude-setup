# Claude Code Setup for Next.js / Supabase / TypeScript

A production-ready Claude Code configuration for Next.js/Supabase/TypeScript projects. Includes hooks for automated quality gates, skills for guided workflows, agents for specialized tasks, MCP server integrations, and comprehensive coding rules.

Extracted from a production SaaS codebase and generalized for reuse. All files use `<!-- CUSTOMIZE -->` markers where you need to fill in project-specific details.

---

## Table of Contents

- [What This Provides](#what-this-provides)
- [Development Workflow](#development-workflow)
  - [The Pipeline](#the-pipeline)
  - [Atomic Phases](#atomic-phases)
  - [Team Orchestration](#team-orchestration)
  - [Quality Gates](#quality-gates)
  - [Ad-Hoc Development](#ad-hoc-development)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Directory Structure](#directory-structure)
- [Hooks](#hooks)
  - [Hook Summary](#hook-summary)
  - [TypeScript Validator](#typescript-validator)
  - [Blocked Commands](#blocked-commands)
  - [Additional Validators](#additional-validators)
- [Skills](#skills)
  - [Planning](#planning)
  - [Code Quality](#code-quality)
  - [Builders](#builders)
  - [Technical](#technical)
  - [MCP Wrappers](#mcp-wrappers)
- [Agents](#agents)
- [Rules](#rules)
- [MCP Servers](#mcp-servers)
  - [Playwright](#playwright)
  - [Context7](#context7)
  - [Tavily](#tavily)
  - [Sequential Thinking](#sequential-thinking)
- [Status Line](#status-line)
- [Customization Guide](#customization-guide)
- [Troubleshooting](#troubleshooting)
- [Plugins](#plugins)
- [Research](#research)
- [Acknowledgments](#acknowledgments)
- [License](#license)

---

## What This Provides

| Category | Count | Purpose |
|----------|-------|---------|
| **Hooks** | 11 Python scripts | Automated quality gates, logging, security blocks, context injection |
| **Skills** | 16 slash commands | Guided workflows for planning, building, reviewing, and using MCP tools |
| **Agents** | 7 agent definitions | Specialized sub-agents for architecture, review, testing, building |
| **MCP Servers** | 4 integrations | Browser automation, documentation lookup, web search, structured reasoning |
| **Rules** | 13 markdown files | Coding standards for TypeScript, React, Supabase, security, testing, and more |

---

## Development Workflow

This setup's primary value is a **structured development pipeline** — from feature idea to shipped code, with quality gates at every stage. Every guardrail exists because skipping it caused hours of rework in real usage.

### The Pipeline

<picture>
  <img alt="Development pipeline diagram showing the flow from /create-plan through /review-plan, /audit-plan, and /implement with its builder-validator loop" src="docs/pipeline.svg" width="950">
</picture>

### Atomic Phases

Traditional development plans have 3-5 large phases. This doesn't work with AI-assisted development because each phase must fit within a single context window (~200K tokens). Large phases cause Claude to lose earlier context mid-implementation, producing incomplete or inconsistent code.

**The rule: 30 small phases > 5 large phases.**

| Wrong | Right |
|-------|-------|
| "Phase 01: Database + API + UI" | Split into 3 separate phases |
| "Phase 02: Full Feature Implementation" | Break into atomic steps |
| "Phase 03: Testing and Polish" | TDD is Step 0 in *every* phase |

Each phase file includes a `skill:` field in its frontmatter that tells the builder which domain skill to invoke — `postgres-expert` for database work, `server-action-builder` for API mutations, `react-form-builder` for forms, and so on. The builder reads a real reference file from the codebase before writing any code, so patterns are grounded in what actually exists rather than guessed from training data.

### Team Orchestration

The `/implement` skill acts as a **thin dispatcher** that coordinates a team of specialized agents:

| Role | Lifetime | Responsibility |
|------|----------|---------------|
| **Orchestrator** | Entire plan | Finds phases, runs gate checks, spawns/shuts down teammates, routes PASS/FAIL verdicts |
| **Builder** | One phase (ephemeral) | Full phase implementation — reads phase file, finds references, invokes domain skills, writes code with TDD, runs `/code-review` |
| **Validator** | Entire plan (persistent) | Independent verification after each phase — checks files exist, patterns match codebase, tests pass, typecheck clean |

**Why builders are ephemeral:** Each phase gets a fresh builder with a clean 200K context window. After completion, the builder is shut down and a new one is spawned for the next phase. This prevents context contamination between phases (bad patterns from phase 2 don't bleed into phase 3), ensures the `builder-workflow` skill instructions are never compacted away, and means each builder reads fresh references for its specific phase type.

**Why the validator is persistent:** Cross-phase context helps it catch consistency issues — if phase 3's types don't match phase 2's interfaces, a persistent validator notices.

For independent phases (no dependencies between them), multiple builders can be spawned in parallel — each with its own clean context.

### Quality Gates

Quality is enforced at four layers during each phase, in order:

| Layer | When | What Runs | Catches |
|-------|------|-----------|---------|
| **PostToolUse hook** | Every Write/Edit on TS files | `typescript_validator.py` | `any` types, missing `'use server'` directives, `console.log` in production code |
| **Builder verification** | After implementation | `pnpm test` + `pnpm run typecheck` | Test failures, type errors |
| **`/code-review`** | After verification passes | 451-line checklist, codebase-grounded, auto-fix | Pattern deviations, security issues, missing auth checks |
| **Validator teammate** | After builder reports done | Independent file/pattern/test verification | Anything the builder's self-review missed |

Both `/review-plan` (planning phase) and `/code-review` (implementation phase) are **codebase-grounded** — they read actual files from your project before flagging issues, so findings are specific to your codebase rather than generic advice.

Implementation is blocked if:
- Plan review verdict is "No"
- Flow audit says "Major Restructuring Needed"
- Phase contains placeholder content (`[To be detailed]`, `TBD`)
- Phase review has unresolved Critical/High issues
- Validator returns FAIL 3+ times on the same phase (escalates to user)

### Ad-Hoc Development

Not everything needs a plan. For smaller tasks — bug fixes, single-feature additions, quick refactors — use **`/dev`** instead:

```
/dev add a loading spinner to the projects list
```

`/dev` follows the same principles (find a reference first, invoke the right domain skill, TDD, verify) but skips the planning overhead. It auto-routes to the appropriate domain skill based on what you're building:

| Work Type | Skill Invoked |
|-----------|--------------|
| Database changes | `/postgres-expert` |
| Server actions | `/server-action-builder` |
| Service layer | `/service-builder` |
| React forms | `/react-form-builder` |
| Components/pages | `/vercel-react-best-practices` |
| E2E tests | `/playwright-e2e` |

If a `/dev` task turns out to be too large (10+ files, multiple domains), it recommends switching to `/create-plan` instead.

> For a deep dive into how each skill works internally, see [docs/workflow.md](docs/workflow.md).

---

## Quick Start

1. **Copy the configuration files into your project root:**

```bash
cp -r .claude/ your-project/.claude/
cp .mcp.json your-project/.mcp.json
cp CLAUDE.md your-project/CLAUDE.md
```

2. **Add API keys to `.mcp.json`:**

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "YOUR_CONTEXT7_API_KEY"]
    },
    "tavily": {
      "command": "npx",
      "args": ["-y", "tavily-mcp@latest"],
      "env": {
        "TAVILY_API_KEY": "YOUR_TAVILY_API_KEY"
      }
    }
  }
}
```

3. **Run `/customize` to fill in project-specific details.** This onboarding wizard collects your project info (name, commands, architecture, component library, etc.) and fills all `<!-- CUSTOMIZE -->` markers across CLAUDE.md and rule files automatically. Or search for markers manually with `grep -rn "CUSTOMIZE" CLAUDE.md .claude/rules/`.

4. **Start Claude Code** in your project directory. The hooks, skills, and rules load automatically.

---

## Prerequisites

| Dependency | Version | Purpose |
|------------|---------|---------|
| [Node.js](https://nodejs.org/) | 18+ | Running MCP servers via `npx` |
| [Python](https://www.python.org/) | 3.11+ | Running hook scripts |
| [uv](https://docs.astral.sh/uv/) | Latest | Python script runner (used by all hooks) |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Latest | CLI that reads this configuration |

Optional:
- [Playwright browsers](https://playwright.dev/) for the Playwright MCP server
- [curl](https://curl.se/) for sound notifications (used by the notification utility)

---

## Directory Structure

```text
.claude/
├── agents/                         # 7 agent definitions
│   ├── architect.md                # Architecture design and trade-off analysis
│   ├── code-quality-reviewer.md    # Code quality and pattern compliance
│   ├── doc-updater.md              # Documentation maintenance
│   ├── security-reviewer.md        # Security vulnerability detection
│   ├── tdd-guide.md                # Test-Driven Development specialist
│   └── team/
│       ├── builder.md              # Focused implementation agent
│       └── validator.md            # Task verification and auto-fix agent
├── hooks/                          # 11 Python hook scripts
│   ├── config/
│   │   └── blocked-commands.json   # Dangerous command patterns to block
│   ├── notification.py             # Sound alerts for user-action-needed events
│   ├── post_tool_use.py            # Quality checks after Write/Edit on TS files
│   ├── post_tool_use_failure.py    # Actionable guidance after tool failures
│   ├── pre_compact.py              # Transcript backup before context compaction
│   ├── pre_tool_use.py             # Blocks dangerous commands, logs tool calls
│   ├── session_end.py              # Logs session end, plays completion sound
│   ├── session_start.py            # Injects git branch/status into context
│   ├── stop.py                     # Transcript export + completion sound
│   ├── subagent_start.py           # Injects project rules into sub-agents
│   ├── subagent_stop.py            # Logs sub-agent completion
│   ├── user_prompt_submit.py       # Logs prompts, stores for status display
│   ├── utils/
│   │   ├── constants.py            # Shared paths and log directory helpers
│   │   └── notify.py               # Sound notification via HTTP (optional)
│   └── validators/
│       ├── typescript_validator.py  # Regex-based TS/React quality checks
│       ├── validate_file_contains.py    # Checks files contain required sections
│       ├── validate_new_file.py         # Checks a new file was created
│       ├── validate_no_placeholders.py  # Detects placeholder/skeleton content
│       └── validate_tdd_tasks.py        # Enforces TDD task ordering in plans
├── rules/                          # 13 rule files
│   ├── admin.md                    # Admin operations guidelines
│   ├── coding-style.md             # TypeScript/React coding standards
│   ├── database.md                 # Supabase/Postgres patterns and RLS
│   ├── forms.md                    # Form handling with react-hook-form + Zod
│   ├── git-workflow.md             # Branch strategy and commit conventions
│   ├── i18n.md                     # Internationalization patterns
│   ├── mcp-tools.md                # MCP server usage guide
│   ├── pages-and-layouts.md        # Next.js page and layout conventions
│   ├── patterns.md                 # Data fetching, mutations, service patterns
│   ├── route-handlers.md           # API route handler conventions
│   ├── security.md                 # RLS, secrets, auth, multi-tenant isolation
│   ├── testing.md                  # Vitest, mocking, TDD workflow
│   └── ui-components.md            # Component library usage guidelines
├── skills/                         # 18 skill directories (each with SKILL.md)
│   ├── audit-plan/
│   ├── code-review/
│   ├── context7-mcp/
│   ├── customize/
│   ├── create-plan/
│   ├── implement/
│   ├── improve-prompt/
│   ├── playwright-e2e/
│   ├── playwright-mcp/
│   ├── postgres-expert/
│   ├── react-form-builder/
│   ├── review-plan/
│   ├── sequential-thinking-mcp/
│   ├── server-action-builder/
│   ├── service-builder/
│   └── tavily-mcp/
├── settings.json                   # Hook configuration and environment
├── settings.local.json             # Local overrides (output style, spinner)
└── statusline-command.py           # Status bar: model, context, usage, tasks, agents, git

docs/
└── research/                       # 9 Anthropic reference documents (see Research section)

.mcp.json                           # MCP server definitions
CLAUDE.md                           # Main project instructions
```

---

## Hooks

All hooks are Python scripts executed via `uv run`. They are configured in `.claude/settings.json` and run automatically at the appropriate lifecycle points.

### Hook Summary

| Hook | Script | Trigger | What It Does |
|------|--------|---------|--------------|
| **PreToolUse** | `pre_tool_use.py` | Before any tool call | Blocks dangerous Bash commands (configurable). Logs a structured summary of every tool call. |
| **PostToolUse** | `post_tool_use.py` | After any tool call | Runs 7 quality checks on TypeScript files after Write/Edit (see table below). Injects warnings into Claude's context. |
| **PostToolUseFailure** | `post_tool_use_failure.py` | After a tool call fails | Pattern-matches error messages and injects actionable guidance (e.g., "Read file before Edit", "Don't retry denied commands"). |
| **Notification** | `notification.py` | When Claude needs input | Plays a sound for permission prompts and elicitation dialogs. Ignores idle/auth events. |
| **Stop** | `stop.py` | When Claude stops | Exports JSONL transcript to `chat.json`. Plays completion sound. |
| **SubagentStart** | `subagent_start.py` | When a sub-agent launches | Injects project coding rules into the sub-agent's context (sub-agents do not inherit `CLAUDE.md`). |
| **SubagentStop** | `subagent_stop.py` | When a sub-agent finishes | Logs sub-agent completion with agent type and transcript path. |
| **PreCompact** | `pre_compact.py` | Before context compaction | Logs compaction events. Optionally backs up the transcript before compression. |
| **UserPromptSubmit** | `user_prompt_submit.py` | When user submits a prompt | Logs prompt metadata. Stores prompt text in session file for status display. |
| **SessionStart** | `session_start.py` | When a session begins | Injects current git branch and uncommitted file count into Claude's context. Logs session start. |
| **SessionEnd** | `session_end.py` | When a session ends | Logs session end reason. Plays completion sound. |

### TypeScript Quality Checks

The `post_tool_use.py` hook runs 7 regex-based quality checks on `.ts`/`.tsx` files after every Write/Edit. No subprocess calls to `tsc` or `eslint` — these are fast pattern matches that catch violations immediately at write-time.

**Checks performed:**

| # | Category | Check | Applies To |
|---|----------|-------|------------|
| 1 | TypeScript Safety | `console.log`/`console.error` usage | All non-test `.ts`/`.tsx` files |
| 2 | Server/Client Boundary | Missing `import 'server-only'` in server files | Files in `server-actions`, `service`, `loader`, `_lib/server/`, `api` paths |
| 3 | TypeScript Safety | `any` type usage (`: any`, `as any`, `<any>`) | All non-test `.ts`/`.tsx` files |
| 4 | Server/Client Boundary | React hooks without `'use client'` directive | `.tsx` files using hooks (not server files) |
| 5 | Code Style | Default exports on non-page/layout components | `_components/` and `components/` `.tsx` files |
| 6 | Security | Hardcoded secrets (API keys, JWT tokens, Stripe keys, GitHub PATs) | All `.ts`/`.tsx` files |
| 7 | Security | Service-role/admin Supabase client without justification comment | All `.ts`/`.tsx` files |

Test files (`__tests__/`, `.test.ts`, `.test.tsx`) and generated files (`database.types`, `.gen.`) are skipped entirely.

<!-- CUSTOMIZE: To add project-specific checks (e.g., framework wrapper enforcement, naming conventions),
add them to the check_typescript_quality() function in post_tool_use.py. Keep checks lightweight
(regex only, no subprocess calls) and use break-after-first-match to limit noise. -->

### Blocked Commands

The `pre_tool_use.py` hook reads patterns from `.claude/hooks/config/blocked-commands.json`. Each rule has:
- `pattern` -- regex to match against the Bash command
- `safe_patterns` -- regexes that whitelist specific usages (e.g., `rm -rf .next` is allowed)
- `action` -- `"deny"` (hard block) or `"ask"` (prompt user for permission)
- `reason` -- explanation shown to Claude

**Default blocked commands:**

| Command Pattern | Action | Reason |
|----------------|--------|--------|
| `rm -rf` on unrecognized paths | Ask | Could destroy source code or data |
| `git push --force` (without `--force-with-lease`) | Deny | Overwrites remote history |
| `DROP TABLE` | Ask | Permanently destroys table and data |
| `DROP DATABASE` | Deny | Destroys entire database |
| `TRUNCATE` | Ask | Removes all rows with no rollback |

You can add your own rules by editing `blocked-commands.json`.

### Additional Validators

The `validators/` directory contains reusable validators that skills and agents can invoke:

| Validator | Purpose |
|-----------|---------|
| `validate_file_contains.py` | Checks that a file contains required sections (e.g., plan documents must have specific headings) |
| `validate_new_file.py` | Checks that at least one file with a given extension exists in a directory |
| `validate_no_placeholders.py` | Detects placeholder content like `[To be detailed]`, `TBD`, `TODO: flesh out` |
| `validate_tdd_tasks.py` | Enforces that TDD/testing tasks appear before implementation tasks in plan documents |

---

## Skills

Skills are invoked via slash commands (e.g., `/create-plan`) or the `Skill` tool. Each skill has a `SKILL.md` file that provides structured guidance, checklists, and examples.

### Setup

| Skill | Slash Command | Purpose |
|-------|--------------|---------|
| **customize** | `/customize` | Onboarding wizard — collects project details and fills all `<!-- CUSTOMIZE -->` markers across CLAUDE.md and rule files |

### Planning

| Skill | Slash Command | Purpose |
|-------|--------------|---------|
| **create-plan** | `/create-plan` | Generates phased implementation plans with task breakdowns, TDD ordering, and acceptance criteria |
| **review-plan** | `/review-plan` | Reviews and validates implementation plans against project patterns and conventions |
| **audit-plan** | `/audit-plan` | Audits existing plans for completeness, risk, and alignment with architecture |
| **implement** | `/implement` | Executes implementation phases from a plan (handles TDD, coding, review loop) |

### Code Quality

| Skill | Slash Command | Purpose |
|-------|--------------|---------|
| **code-review** | `/code-review` | Structured code review with severity-rated findings, file:line references, and fix suggestions |
| **improve-prompt** | `/improve-prompt` | Refines and improves user prompts for better Claude Code results |

### Builders

| Skill | Slash Command | Purpose |
|-------|--------------|---------|
| **dev** | `/dev` | General-purpose ad-hoc development — routes to domain skills, enforces task tracking, and follows a build-test-verify loop |
| **server-action-builder** | `/server-action-builder` | Generates Server Actions with Zod validation, auth checks, and service integration |
| **service-builder** | `/service-builder` | Generates services following the private class + factory function pattern |
| **react-form-builder** | `/react-form-builder` | Generates client forms with `react-hook-form`, Zod schemas, and component library integration |

### Technical

| Skill | Slash Command | Purpose |
|-------|--------------|---------|
| **postgres-expert** | `/postgres-expert` | Guides database migrations, RLS policies, functions, triggers, and type generation |
| **playwright-e2e** | `/playwright-e2e` | Generates Playwright end-to-end test code for critical user flows |

### MCP Wrappers

These skills provide structured guidance for using the MCP server tools effectively:

| Skill | Slash Command | Purpose |
|-------|--------------|---------|
| **context7-mcp** | `/context7-mcp` | Guides use of Context7 for up-to-date library documentation lookup |
| **tavily-mcp** | `/tavily-mcp` | Guides use of Tavily for web search, extraction, and research |
| **sequential-thinking-mcp** | `/sequential-thinking-mcp` | Guides use of sequential thinking for structured multi-step reasoning |
| **playwright-mcp** | `/playwright-mcp` | Guides use of Playwright MCP for live browser interaction |

---

## Agents

Agents are specialized sub-agents that can be delegated tasks via the `Task` tool. They are defined in `.claude/agents/` and have specific tool access and model configurations.

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **architect** | Sonnet | Read, Grep, Glob | Software architecture design, trade-off analysis, database schema planning, route/component design. Read-only -- does not implement. |
| **code-quality-reviewer** | Sonnet | Read, Grep, Glob, Bash | Code quality review against TypeScript/React/Next.js patterns. Outputs severity-rated findings with fix suggestions. |
| **security-reviewer** | Sonnet | Read, Write, Edit, Bash, Grep, Glob | Security vulnerability detection: RLS validation, secrets scanning, admin client misuse, OWASP Top 10 checks. |
| **tdd-guide** | Sonnet | Read, Write, Edit, Bash, Grep | Test-Driven Development specialist using Vitest with happy-dom. Guides RED-GREEN-REFACTOR workflow. |
| **doc-updater** | Sonnet | Read, Write, Edit, Bash, Grep, Glob | Documentation maintenance. Updates CLAUDE.md, architecture maps, and feature documentation. |
| **builder** | Opus | Full tool access | Focused implementation agent. Executes one task at a time, supports skill invocation, follows project patterns. |
| **validator** | Opus | Full tool access (except NotebookEdit) | Verifies task completion against acceptance criteria. Auto-fixes Critical/High issues, creates fix tasks for the rest. |

The `builder` and `validator` agents are designed for team workflows where a lead agent coordinates multiple builders and validators working on different tasks.

---

## Rules

Rule files in `.claude/rules/` are automatically loaded by Claude Code and provide domain-specific coding standards.

| Rule File | What It Covers |
|-----------|---------------|
| `admin.md` | Admin operations, privileged access patterns, admin client usage guidelines |
| `coding-style.md` | Immutability, error handling with structured logging, Server Action conventions, import ordering, React best practices |
| `database.md` | Supabase/Postgres patterns: migrations, type inference, SQL style, RLS helpers, views with `security_invoker`, common patterns |
| `forms.md` | Form handling with `react-hook-form` + Zod, schema sharing between client and server, validation patterns |
| `git-workflow.md` | Branch strategy (`development`/`main`), commit message format, pre-push verification, PR workflow |
| `i18n.md` | Internationalization patterns, translation key conventions, locale handling |
| `mcp-tools.md` | MCP server usage guide: when to use each server, quick references, common library IDs, rules for each tool |
| `pages-and-layouts.md` | Next.js App Router page/layout conventions, async params handling, loading states, error boundaries |
| `patterns.md` | Data fetching with loaders, mutation flow with Server Actions, service pattern, route structure, React Query usage |
| `route-handlers.md` | API route handler conventions, request/response patterns, middleware |
| `security.md` | RLS enforcement, secret management, authentication, multi-tenant data isolation, OAuth callbacks, security checklist |
| `testing.md` | Vitest configuration, mock patterns, TDD workflow, component testing, E2E testing approach |
| `ui-components.md` | Component library usage, when to use shared components vs custom UI, styling conventions |

---

## MCP Servers

Four MCP (Model Context Protocol) servers are configured in `.mcp.json`. They provide Claude Code with additional capabilities via direct tool calls.

### Playwright

**Purpose:** Live browser interaction -- navigating pages, clicking buttons, filling forms, taking screenshots.

**Setup:** No API key required. Requires a browser to be installed.

```bash
# If you get a "browser not installed" error:
npx playwright install chromium
```

**Key tools:**

| Tool | Usage |
|------|-------|
| `mcp__playwright__browser_navigate` | Open a URL |
| `mcp__playwright__browser_snapshot` | Get page structure (accessibility tree) -- always do this before interacting |
| `mcp__playwright__browser_click` | Click an element (needs `ref` from snapshot) |
| `mcp__playwright__browser_type` | Type text into a field |
| `mcp__playwright__browser_take_screenshot` | Capture a visual screenshot |

**Important:** Always call `browser_snapshot` before interacting with elements -- it provides the `ref` values needed for click/type/hover. Prefer snapshot over screenshot for structured data.

### Context7

**Purpose:** Query up-to-date library and framework documentation.

**Setup:** Requires a Context7 API key from [Upstash](https://upstash.com/).

```json
{
  "context7": {
    "command": "npx",
    "args": ["-y", "@upstash/context7-mcp", "--api-key", "YOUR_API_KEY"]
  }
}
```

**Key tools:**

| Tool | Usage |
|------|-------|
| `mcp__context7__resolve-library-id` | Resolve a library name to a Context7 ID (call first) |
| `mcp__context7__query-docs` | Query documentation for a specific library |

**Common library IDs** (skip resolve for these):

| Library | ID |
|---------|-----|
| Next.js | `/vercel/next.js` |
| React | `/facebook/react` |
| Supabase JS | `/supabase/supabase-js` |
| Zod | `/colinhacks/zod` |
| TanStack Query | `/tanstack/query` |

### Tavily

**Purpose:** Web search, content extraction, site crawling, and multi-source research.

**Setup:** Requires a Tavily API key from [tavily.com](https://tavily.com/).

```json
{
  "tavily": {
    "command": "npx",
    "args": ["-y", "tavily-mcp@latest"],
    "env": {
      "TAVILY_API_KEY": "YOUR_API_KEY"
    }
  }
}
```

**Key tools:**

| Tool | Usage |
|------|-------|
| `mcp__tavily__tavily_search` | Quick web search (start here -- fast and cheap) |
| `mcp__tavily__tavily_extract` | Extract content from a specific URL |
| `mcp__tavily__tavily_map` | Map a website's structure before crawling |
| `mcp__tavily__tavily_crawl` | Crawl multiple pages from a website |
| `mcp__tavily__tavily_research` | Comprehensive multi-source research (expensive -- use sparingly) |

### Sequential Thinking

**Purpose:** Structured multi-step reasoning for complex problems.

**Setup:** No API key required.

**Tool:** `mcp__sequential-thinking__sequentialthinking`

**When to use:**
- Bug with 3+ possible causes needing elimination
- Architectural decision with competing trade-offs
- Root cause analysis requiring hypothesis testing

**When not to use:**
- Simple errors with clear stack traces
- Straightforward implementation decisions

---

## Status Line

The `statusline-command.py` script renders a rich status bar at the bottom of Claude Code showing real-time session info:

```text
Opus | ██████░░░░ 58% | 5h: 23% (3h12m) | 7d: 8% (5d2h) | Tasks: 2/5 | Agents: 1 team + 2 bg | notes P3 | development
```

**Segments displayed:**

| Segment | Source | Example |
|---------|--------|---------|
| Model | Claude's stdin | `Opus`, `Sonnet`, `Haiku` |
| Context | Token usage / window size | `██████░░░░ 58%` |
| 5h Usage | Anthropic OAuth API | `5h: 23% (3h12m)` — resets every 5 hours |
| 7d Usage | Anthropic OAuth API | `7d: 8% (5d2h)` — resets every 7 days |
| Tasks | Open/completed task counts | `Tasks: 2/5` (hidden when no tasks) |
| Agents | Active teammates + background tasks | `Agents: 1 team + 2 bg` (hidden when none) |
| Plan | Per-plan sidecar files from `/implement` | `notes P3` or `notes P3 | billing P1` (hidden when no plan active) |
| Git Branch | `git branch --show-current` | `development` |

The **Plan** segment uses per-plan sidecar files in `~/.cache/claude-statusline/plans/` — each `/implement` session writes its own file keyed by plan name (e.g., `notes.json`, `billing.json`). This means multiple agents working on different plans each get their own sidecar with no overwrites. The statusline scans all sidecar files and displays every active plan. Stale sidecars from crashed sessions auto-expire after 2 hours.

Colors change from green to yellow to red as usage increases (50% / 80% thresholds).

### Status Line Setup

1. **Copy the script** to your global Claude config:

```bash
cp .claude/statusline-command.py ~/.claude/statusline-command.py
chmod +x ~/.claude/statusline-command.py
```

2. **Add to your global settings** at `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline-command.py"
  }
}
```

The status line is a **global** setting (not per-project) because it uses your OAuth credentials from `~/.claude/.credentials.json` to fetch usage data. Place it in `~/.claude/settings.json`, not the project-level settings.

### How It Works

The script receives JSON on stdin from Claude Code containing model info, context window state, active tasks/agents, and workspace path. It fetches subscription utilization from the Anthropic OAuth usage API (`api.anthropic.com/api/oauth/usage`) with a 60-second cache to avoid excessive API calls, then renders all segments with ANSI 256-color codes.

### Requirements

- **Claude Code Max or Pro subscription** — the OAuth usage endpoint requires an active subscription
- **Authenticated session** — you must be logged in (the script reads `~/.claude/.credentials.json`)
- No additional dependencies — uses only Python standard library (`urllib`, `json`, `subprocess`)

---

## Customization Guide

### 1. Fill in CLAUDE.md

Search for `<!-- CUSTOMIZE -->` markers in `CLAUDE.md`. Each marker includes instructions and examples:

```bash
grep -n "CUSTOMIZE" CLAUDE.md
```

Key sections to customize:
- **Project description** -- Replace the placeholder with your app's name and tech stack
- **Monorepo** -- List your apps/packages or remove the section for single-app projects
- **Commands** -- Add your dev, build, test, and verification commands
- **Architecture** -- Describe your data flow, auth, and multi-tenant patterns
- **Verification** -- Add your project's typecheck/lint/test commands

### 2. Fill in Rule Files

Several rule files also have `<!-- CUSTOMIZE -->` markers:

```bash
grep -rn "CUSTOMIZE" .claude/rules/
```

Common customizations:
- `git-workflow.md` -- Your remote URLs, branch names, CI pipeline
- `database.md` -- Your migration commands, RLS helper functions
- `security.md` -- Your auth wrapper, specific security requirements
- `patterns.md` -- Your Server Action wrapper, specific architectural patterns
- `coding-style.md` -- Your logging utility, framework-specific conventions

### 3. Add Custom Rules

Create new `.md` files in `.claude/rules/`. Claude Code automatically loads all rule files in this directory.

```bash
# Example: add a rule for your API integration
touch .claude/rules/my-api-integration.md
```

### 4. Add Custom Skills

Create a new directory in `.claude/skills/` with a `SKILL.md` file:

```text
.claude/skills/my-skill/
└── SKILL.md
```

The `SKILL.md` file should contain the guidance, checklists, and examples that Claude loads when the skill is invoked.

### 5. Add Custom Agents

Create a new `.md` file in `.claude/agents/` with YAML frontmatter:

```markdown
---
name: my-agent
description: "What this agent does and when to use it."
tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
model: sonnet
---

# My Agent

Instructions for the agent...
```

### 6. Modify Blocked Commands

Edit `.claude/hooks/config/blocked-commands.json` to add or remove blocked command patterns:

```json
[
  {
    "pattern": "your-regex-pattern",
    "safe_patterns": ["exceptions"],
    "action": "deny",
    "reason": "Why this is blocked"
  }
]
```

### 7. Sound Notifications (Optional)

The `notify.py` utility sends HTTP requests to `localhost:9999` for sound alerts. If you do not have a sound server running, notifications fail silently and hooks continue normally. To disable the sound calls entirely, edit `utils/notify.py` to make the `notify()` function a no-op.

---

## Troubleshooting

### Hooks not running

**Symptom:** Quality checks, blocked commands, or context injection not working.

**Check:**
1. Verify `uv` is installed: `uv --version`
2. Verify Python 3.11+: `python3 --version`
3. Check `.claude/settings.json` exists and has valid JSON
4. Run a hook manually to test:
   ```bash
   echo '{"tool_name":"Bash","tool_input":{"command":"echo test"}}' | uv run .claude/hooks/pre_tool_use.py
   ```

### MCP servers not loading

**Symptom:** MCP tool calls fail or are not available.

**Check:**
1. Verify `.mcp.json` exists in the project root
2. Verify API keys are set (not placeholder values)
3. Check that `npx` is available: `npx --version`
4. Try running the MCP server manually:
   ```bash
   npx @playwright/mcp@latest
   ```
5. For Playwright, ensure browsers are installed:
   ```bash
   npx playwright install chromium
   ```

### Skills not found

**Symptom:** Slash command or `Skill` tool call returns "skill not found".

**Check:**
1. Verify the skill directory exists: `ls .claude/skills/`
2. Verify each skill has a `SKILL.md` file
3. Skill names match the directory name (e.g., `/create-plan` maps to `.claude/skills/create-plan/`)

### TypeScript validator warnings not appearing

**Symptom:** Code quality issues not flagged after Write/Edit.

**Check:**
1. The validator only runs on `.ts` and `.tsx` files
2. Test files are only checked for hardcoded secrets
3. Files in `node_modules`, `.next`, `dist`, `__tests__`, and `__mocks__` are skipped
4. Run the validator manually:
   ```bash
   echo '{"tool_name":"Write","tool_input":{"file_path":"test.ts"}}' | uv run .claude/hooks/validators/typescript_validator.py
   ```

### Agent teams not working

**Symptom:** Team-based workflows fail or agents cannot communicate.

**Check:**
1. Verify `settings.json` has the experimental teams flag:
   ```json
   {
     "env": {
       "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
     },
     "teammateMode": "in-process"
   }
   ```

---

## Plugins

Optional Claude Code plugins can enhance the development experience. See [plugins.md](plugins.md) for details on available plugins and installation instructions.

---

## Research

The `docs/research/` directory contains reference material from Anthropic's official documentation that informed the design of this setup. Useful if you want to understand the "why" behind the hooks, skills, and agent patterns.

| Document | What It Covers |
|----------|---------------|
| [anthropic-best-practices.md](docs/research/anthropic-best-practices.md) | Consolidated Anthropic best practices for Claude Code configuration and workflows |
| [anthropic-hooks-reference.md](docs/research/anthropic-hooks-reference.md) | Complete lifecycle event hook reference -- events, schemas, input/output contracts |
| [anthropic-skills-guide.md](docs/research/anthropic-skills-guide.md) | Building, testing, and distributing Agent Skills using the MCP architecture |
| [anthropic-skills-info.md](docs/research/anthropic-skills-info.md) | Extending Claude with custom slash commands and the Agent Skills standard |
| [anthropic-agents-info.md](docs/research/anthropic-agents-info.md) | Creating custom subagents with specialized tools and model configurations |
| [anthropic-claude-code-agents.md](docs/research/anthropic-claude-code-agents.md) | Claude Code-specific skill extensions, subagents, and agent teams |
| [anthropic-teams.md](docs/research/anthropic-teams.md) | Orchestrating teams of Claude Code sessions with shared tasks and messaging |
| [anthropic-memory-and-prompting.md](docs/research/anthropic-memory-and-prompting.md) | CLAUDE.md memory hierarchy, directive compliance, and documentation architecture |
| [anthropic-takeaways.md](docs/research/anthropic-takeaways.md) | Quick-reference action table summarizing insights across all topics |

---

## Acknowledgments

The hook architecture in this project was inspired by [disler/claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability). The hooks have since been extensively rewritten but the original project provided valuable patterns for Claude Code hook design.

---

## License

MIT -- see [LICENSE](LICENSE) for details.
