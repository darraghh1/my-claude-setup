# My Claude Code setup — hooks, skills, agents, and a structured dev pipeline

I've been lurking here for a while, and I've picked up a ton from people sharing their workflows. Ideas about hooks, skills, agent teams, MCP configs — bits and pieces from dozens of posts that I've adapted and built on over time. So here's my contribution back to the community.

I extracted my Claude Code configuration from a production Next.js/Supabase/TypeScript SaaS project and generalized it for reuse. Everything uses `<!-- CUSTOMIZE -->` markers where you fill in your own project details — or you can run `/customize` and let Claude do it for you.

## What's in the box

| Category | Count |
|----------|-------|
| **Hooks** | 11 Python scripts — quality gates, security blocks, context injection, sound notifications |
| **Skills** | 19 directories (17 slash commands) — planning, building, reviewing, diagrams, MCP wrappers |
| **Agents** | 7 definitions — architect, builder, validator, TDD guide, security reviewer, etc. |
| **Rules** | 13 files — TypeScript, React, Supabase, security, testing, forms, git workflow |
| **MCP Servers** | 4 integrations — Playwright, Context7, Tavily, Sequential Thinking |

## The pipeline

The main thing this setup provides is a structured development pipeline — from feature idea to shipped code, with quality gates at every stage.

![Implementation pipeline](https://raw.githubusercontent.com/darraghh1/my-claude-setup/main/docs/pipeline.svg)

`/implement` acts as a thin orchestrator that spawns ephemeral builder and validator agents — each phase gets a fresh agent pair with clean 200K context. Builders never review their own code; an independent validator runs `/code-review` against codebase reference files, auto-fixes issues, then reports PASS/FAIL. Every phase gets TDD first, then implementation, then verification.

## Things that might be useful even if you don't adopt the whole setup

- **TypeScript PostToolUse hook** — catches `any` types, missing `'use server'`, `console.log`, and hardcoded secrets at write-time (regex-only, no subprocess calls, instant)
- **Blocked commands hook** — configurable JSON file that blocks `git push --force`, `DROP DATABASE`, etc. with safe-pattern exceptions
- **Status line script** — shows model, context %, 5h/7d usage with color thresholds, active tasks/agents, current git branch
- **Per-plan sidecar files** — multiple `/implement` sessions can run on different plans without overwriting each other's status
- **Codebase-grounded reviews** — both `/review-plan` and `/code-review` read actual files from your project before flagging issues, so findings are specific to your codebase rather than generic advice

## Link

**GitHub:** [github.com/darraghh1/my-claude-setup](https://github.com/darraghh1/my-claude-setup)

The README has the full breakdown — directory structure, how every hook/skill/agent works, setup instructions, troubleshooting, and links to the Anthropic research docs that informed the design.

Happy to answer questions or hear suggestions. This has been evolving for a while and I'm sure there's room to improve.
