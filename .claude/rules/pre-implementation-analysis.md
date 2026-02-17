---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# Pre-Implementation Analysis

Rushing into code without considering blast radius, security, and existing patterns has caused regressions, tenant data leaks, and unnecessary rewrites in this codebase. The user depends on a brief analysis step before writing code to catch these issues early — skipping it wastes their debugging time later.

## When to Skip

Skip for trivial changes (typos, one-line fixes, obvious bugs), research/exploration tasks, or when the user says "just do it." Also skip when implementing from `/implement` phase docs — they already contain this analysis.

## Before Writing Code

For non-trivial tasks (new features, multi-file changes, schema changes), consider the relevant items below. Surface any concerns before proceeding — e.g., "This touches the auth flow — verifying RLS coverage first."

**1. Existing patterns** — Check `_lib/server/`, existing services, and similar features before building new. Match what exists. Deviating from established patterns wastes reconciliation time. See `patterns.md`.

**2. Blast radius** — Identify affected files and features. Check for tests covering the changed area — breaking untested code silently causes production regressions discovered later.

**3. Security surface** — If this handles user input, touches auth, or accesses data: run through the checklist in `security.md`. Missing RLS on a new table is the most common way tenant data leaks between accounts.

**4. Performance** — Does this run on every page load? Does it introduce N+1 queries? Could it affect bundle size by importing heavy server/data dependencies into a client component?

**5. Maintainability** — Choose the simplest approach. Follow service, `enhanceAction`, and loader patterns from `patterns.md` and `coding-style.md`. Future developers (and Claude sessions) need to understand this without extra context.

**6. Multi-tenant safety** — Verify data is scoped to `account_id` and RLS enforces isolation. Cross-tenant data exposure is a P0 incident for the user's customers.

**7. Upstream compatibility** — If the change touches MakerKit-maintained code, consider merge conflicts during upstream updates. Custom divergence from MakerKit patterns creates maintenance burden the user has to resolve manually.

## Output

Not every item needs a written response. Only surface concerns that the analysis actually finds — a brief note before proceeding is enough. No output needed when nothing concerning is found.
