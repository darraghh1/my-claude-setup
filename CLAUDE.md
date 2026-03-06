Reusable Claude Code configuration layer — hooks, skills, agents, rules, MCP servers for Next.js/Supabase/TypeScript projects. This is tooling infrastructure, not an application.

## Critical Rules

These rules address recurring mistakes that cause real issues. Each one prevents debugging time, security vulnerabilities, or broken builds:

- Using `any` defeats TypeScript's safety net — bugs and security issues reach production undetected. Use proper types or `unknown`.
- `console.log`/`console.error` in production breaks structured logging, making production debugging impossible. Use a proper logger (e.g., Pino, Winston, or your framework's logging utility).
- Missing `import 'server-only'` allows server code to bundle into the client, leaking API keys and database credentials to the browser.
- Server actions must validate inputs with Zod schemas and verify authentication before processing. Unauthenticated or unvalidated data must never reach the database.
- Tables without RLS expose all rows to any authenticated user — one missing policy means customer data leaks across accounts.
- Forgetting to `await params` in async server components causes runtime errors in Next.js that are hard to trace.
- `useEffect` often masks logic that belongs in a server component, event handler, or derived state. Each use should be justified with a comment.
- Multiple separate `useState` calls that change together cause re-renders and state sync bugs. Prefer a single state object.
- Custom form handling bypasses the shared validation pipeline. Use `react-hook-form` + Zod to keep validation consistent.
- Building custom UI when your component library already has the component creates visual inconsistency and double maintenance. Check your component library first.

## Commands

This is a configuration repo — no app build or runtime commands. Hooks are Python scripts run via `uv`.

| Command | Purpose |
|---------|---------|
| `uv run .claude/hooks/<hook>.py` | Run a hook script directly (for testing) |
| `pytest tests/hooks/` | Run hook test suite |

## Architecture

### Pipeline Flow

```
/create-plan → /audit-plan → /review-plan → /implement
```

- **Thin dispatchers** — orchestrators stay lean, all heavy lifting in ephemeral workers
- **Ephemeral agents** — fresh 200K context per phase, no contamination
- **Builder worktree isolation** — parallel builders on separate git branches
- **Group-based auditing** — cross-phase regression detection with deviation chaining
- **5-layer quality gates** — PostToolUse hook → builder verification → validator /code-review → validator verification → group audit

### Component Inventory

| Component | Count | Location |
|-----------|-------|----------|
| Hooks | 12 events, 13 scripts | `.claude/hooks/` |
| Skills | 27 | `.claude/skills/` |
| Agents | 9 | `.claude/agents/` |
| Rules | 16 | `rules/` (symlinked to `~/.claude/rules/`) |
| MCP Servers | 5 | `~/.claude.json` |

### Deployment

Skills and agents are directory-symlinked from `.claude/` to `~/.claude/`. Rules live in `rules/` at repo root with per-file symlinks to `~/.claude/rules/` (avoids double-loading in this project). Hooks and `settings.json` are copied per-project (project-specific validators). MCP servers are configured at user level in `~/.claude.json`.

### Hook Architecture

All hooks are Python 3.11+ with zero external dependencies (stdlib only), run via `uv run --script`, with 10-second timeouts.

Config files in `.claude/hooks/config/`:
- `blocked-commands.json` — security gating patterns
- `project-checks.json` — project-specific TypeScript validation rules
- `quality-check-excludes.json` — path exclusions

## Code Style

- Interfaces over types for object shapes; export all types
- Use type guards, not type assertions
- Service pattern: private class + exported factory function
- Use destructuring: `const { name } = user` not `const name = user.name`
- Use millisecond constants (e.g., `const TIMEOUT = 30_000`) instead of magic numbers
- See `.claude/rules/coding-style.md` for full style guide

## Delegate to Agents

Use the Task tool to delegate tasks to specialized sub-agents. Agents are defined in `.claude/agents/` — check agent descriptions to find the right one for your task.

## Verification

```bash
pytest tests/hooks/    # Hook unit tests
```
