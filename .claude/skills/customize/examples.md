# Customize Skill — Example Intake

This shows what a completed intake looks like for a hypothetical "Acme HR" SaaS project.
Use this as a reference when running `/customize` for your own project.

---

## Example Project Brief: Acme HR

### Round 1 — Core Identity

**Project name and description:**
Acme HR — employee management platform for small businesses.

**App structure:** Monorepo (Turborepo)

| App | Port | Purpose |
|-----|------|---------|
| `apps/web` | 3000 | Marketing site + auth pages |
| `apps/dashboard` | 3001 | Main HR dashboard |
| `apps/e2e` | — | Playwright E2E tests |
| `packages/ui` | — | Shared component library (shadcn/ui) |
| `packages/db` | — | Shared Supabase client + types |

**Package manager:** pnpm

**Component library:** shadcn/ui
- Import path: `@acme/ui` (from `packages/ui`)

### Round 2 — Architecture

**Auth model:** Multi-tenant with teams
- Each company is an "organization" (org_id FK)
- Users belong to orgs via `memberships` table
- Roles: owner, admin, member

**Framework wrappers:** None — uses manual Zod + auth pattern

**Logging:** Pino
- Import: `import { logger } from '@acme/logger'`

**Supabase client paths:**
- Server: `import { createClient } from '@acme/db/server'`
- Client: `import { createBrowserClient } from '@acme/db/client'`
- Admin: `import { createAdminClient } from '@acme/db/admin'`

### Round 3 — Commands & Git

**Key commands:**
```bash
pnpm dev                    # Start all apps
pnpm build                  # Build all
pnpm test                   # Run Vitest
pnpm test:e2e               # Run Playwright
pnpm lint                   # ESLint
pnpm typecheck              # TypeScript check
pnpm verify                 # typecheck + lint + test
pnpm db:diff                # Create Supabase migration
pnpm db:reset               # Reset database
pnpm db:typegen             # Generate TypeScript types
```

**Git strategy:**
- Branches: `main` (stable) + `develop` (active work)
- Remote: `origin` → `github.com/acme-hr/platform.git`
- No upstream template

**CI/CD:** GitHub Actions
- Jobs: typecheck, lint, unit tests, E2E tests, deploy to Vercel

### Round 4 — Optional Features

**i18n:** Yes, using `next-intl`
- Namespaces: `common`, `auth`, `dashboard`, `employees`, `settings`

**Testing structure:**
```
apps/dashboard/__tests__/{feature}/
```

**Other conventions:**
- All API routes use `withAuth` middleware from `@acme/auth`
- Feature flags via Supabase `app_config` table
- Admin panel at `/admin` uses `isAdmin()` check from `@acme/auth`

---

## What the Customized CLAUDE.md Looks Like

After running `/customize` with the brief above, CLAUDE.md would become:

```markdown
Acme HR — employee management platform. Next.js App Router, Supabase, TypeScript, Turborepo.

## Critical Rules

- Using `any` defeats TypeScript's safety net ...
- `console.log`/`console.error` in production breaks structured logging. Use `logger` from `@acme/logger`.
- Missing `import 'server-only'` allows server code to bundle into the client ...
- Server actions must validate inputs with Zod schemas and verify authentication before processing ...
- Tables without RLS expose all rows to any authenticated user ...
(... standard rules, with logger and any project-specific additions ...)

## Monorepo

| App | Port | Purpose |
|-----|------|---------|
| `apps/web` | 3000 | Marketing site + auth pages |
| `apps/dashboard` | 3001 | Main HR dashboard |
| `apps/e2e` | — | Playwright E2E tests |
| `packages/ui` | — | Shared component library (shadcn/ui) |
| `packages/db` | — | Shared Supabase client + types |

## Commands

\```bash
pnpm dev                    # Start all apps
pnpm build                  # Build all
pnpm test                   # Run Vitest
pnpm test:e2e               # Run Playwright
pnpm lint                   # ESLint
pnpm typecheck              # TypeScript check
pnpm verify                 # typecheck + lint + test
pnpm db:diff                # Create Supabase migration
pnpm db:reset               # Reset database
pnpm db:typegen             # Generate TypeScript types
\```

## Architecture

- **Multi-tenant**: Organizations with team members, all data scoped via `org_id` FK
- **Data fetching**: Server Components with loaders (read) + Server Actions with Zod (mutations)
- **RLS**: Enforces authorization automatically — no manual auth checks with standard Supabase client
- **Feature flags**: `app_config` table in Supabase

## Code Style

(... unchanged from template ...)

## Delegate to Agents

(... unchanged from template ...)

## Verification

After implementation, run `pnpm verify` (typecheck + lint + test) or individually:

1. **Run `pnpm typecheck`** — must pass
2. **Run `pnpm lint`** — auto-fix with `pnpm lint --fix`
3. **Run `pnpm test`** — all tests pass
```

---

## What Customized Rule Files Look Like

### patterns.md — Supabase Client Table

```markdown
| Context | Client | Import |
|---------|--------|--------|
| Server Components, Actions | `createClient()` | `@acme/db/server` |
| Client Components | `createBrowserClient()` | `@acme/db/client` |
| Bypassing RLS (rare) | `createAdminClient()` | `@acme/db/admin` |
```

### testing.md — Test Location

```markdown
Tests go in `apps/dashboard/__tests__/{feature}/`:

\```
apps/dashboard/__tests__/
├── employees/              # Employee feature tests
│   └── employee-service.test.ts
├── settings/               # Settings tests
│   └── settings.test.tsx
└── helpers/                # Shared test utilities
\```
```

### database.md — Commands

```markdown
- Create migrations: `pnpm db:diff`
- Apply migrations: `pnpm db:reset`
- Generate types: `pnpm db:typegen`
```

### git-workflow.md — Branch Strategy

```markdown
| Branch | Purpose | Pushes To |
|--------|---------|-----------|
| `develop` | Active working branch | `origin/develop` |
| `main` | Stable branch — CI + deploy | `origin/main` |
```

---

## Validation Output

After customization, the validation step should produce:

```
Customization complete for Acme HR!

Files modified:
  - CLAUDE.md
  - .claude/rules/git-workflow.md
  - .claude/rules/database.md
  - .claude/rules/patterns.md
  - .claude/rules/coding-style.md
  - .claude/rules/security.md
  - .claude/rules/ui-components.md
  - .claude/rules/forms.md
  - .claude/rules/testing.md
  - .claude/rules/i18n.md
  - .claude/rules/admin.md
  - .claude/rules/pages-and-layouts.md
  - .claude/rules/route-handlers.md

Remaining markers: 0

Next steps:
  1. Review the changes: git diff
  2. Test the setup: start a new Claude Code session and verify context
  3. Optional: Add project-specific validators to post_tool_use.py
```
