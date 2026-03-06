---
description: "Compressed critical patterns from all domain skills — React/Next.js, PostgreSQL, Server Actions, Services, Forms, Playwright. Passive context loaded natively via alwaysApply: true — available to all agents including team teammates."
alwaysApply: true
---

# Domain Patterns — Passive Context Index

> IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning for framework-specific tasks.
> When you need deeper guidance, read the full skill file at the `ref:` path listed for each domain.

This file provides compressed critical patterns from domain knowledge skills. It exists because Vercel's evals showed passive context (always available) achieves 100% pass rate vs 53-79% for on-demand skill invocation. These patterns are injected into every builder/validator/auditor at spawn time.

---

## React & Next.js Performance | ref: .claude/skills/vercel-react-best-practices/SKILL.md

**CRITICAL — Eliminating Waterfalls:**
- `async-parallel` — Use Promise.all() for independent async operations, never sequential awaits
- `async-suspense-boundaries` — Use Suspense to stream content, don't block full page on one fetch
- `async-defer-await` — Move await into branches where actually used

**CRITICAL — Bundle Size:**
- `bundle-barrel-imports` — Import directly from module, never through barrel/index files
- `bundle-dynamic-imports` — Use next/dynamic for heavy components below the fold
- `bundle-defer-third-party` — Load analytics/logging after hydration

**HIGH — Server-Side:**
- `server-cache-react` — Use React.cache() for per-request deduplication across components
- `server-serialization` — Minimize data passed to client components (serialize only what's displayed)
- `server-parallel-fetching` — Restructure components to parallelize fetches, not waterfall

**MEDIUM — Re-renders:**
- `rerender-derived-state-no-effect` — Derive state during render, not in useEffect
- `rerender-functional-setstate` — Use functional setState for stable callbacks
- `rerender-move-effect-to-event` — Put interaction logic in event handlers, not effects

## React Composition | ref: .claude/skills/vercel-composition-patterns/SKILL.md

- `architecture-avoid-boolean-props` — Don't add boolean props to customize behavior; use composition
- `architecture-compound-components` — Structure complex components with shared context
- `patterns-explicit-variants` — Create explicit variant components instead of boolean modes
- `state-context-interface` — Define generic interface with state, actions, meta for dependency injection
- `react19-no-forwardref` — React 19+: use ref as a prop directly, use `use()` instead of `useContext()`

## React Native / Expo | ref: .claude/skills/vercel-react-native-skills/SKILL.md

- `list-performance-virtualize` — Use FlashList for large lists, never plain ScrollView
- `list-performance-item-memo` — Memoize list item components, stabilize callback refs
- `animation-gpu-properties` — Animate only transform and opacity (GPU-accelerated)
- `navigation-native-navigators` — Use native stack/tabs over JS navigators
- `ui-expo-image` — Use expo-image for all images (not React Native Image)

---

## PostgreSQL / Supabase | ref: .claude/skills/postgres-expert/SKILL.md

**What breaks if you deviate:**
| Deviation | Impact |
|-----------|--------|
| Missing RLS policies | Data leaks between tenant accounts |
| `USING(true)` in policies | Any authenticated user reads all rows |
| Missing `account_id` scoping | Cross-tenant data exposure |
| Missing indexes on FKs | Slow queries as data grows |
| Non-idempotent migrations | Deployment failures requiring manual intervention |

**Key rules:**
- Use existing helpers: `has_role_on_account()`, `has_permission()`, `is_account_owner()` — don't recreate
- Personal + team access: `account_id = auth.uid() OR has_role_on_account(account_id)`
- Migrations: `IF NOT EXISTS` / `IF EXISTS` for idempotency
- Indexes: `CREATE INDEX CONCURRENTLY` to avoid locking
- Naming: snake_case everything, include `created_at` + `updated_at` with `trigger_set_timestamps`

---

## Server Actions | ref: .claude/skills/server-action-builder/SKILL.md

**What breaks if you deviate:**
| Deviation | Impact |
|-----------|--------|
| No auth check | Unauthenticated data reaches database |
| No Zod validation | Invalid data causes crashes or corruption |
| Business logic in action | Untestable, can't reuse from MCP/CLI |
| Missing `revalidatePath` | UI shows stale data after mutations |

**Pattern: auth → validate → service → revalidate**
```
'use server' → getSession() → Schema.parse() → createXxxService(client) → service.method() → revalidatePath()
```

**File structure:** `_lib/schema/*.schema.ts` + `_lib/server/*.service.ts` + `_lib/server/server-actions.ts`

---

## Service Layer | ref: .claude/skills/service-builder/SKILL.md

**What breaks if you deviate:**
| Deviation | Impact |
|-----------|--------|
| Service imports `createClient()` | Can't test without running database |
| Business logic in adapter | Must duplicate fixes across every interface |
| Missing `import 'server-only'` | Server code leaks to browser bundle |

**Pattern:** Factory function + private class + injected client
```
export function createXxxService(client: SupabaseClient<Database>) { return new XxxService(client); }
```

**Rules:**
- Services are pure: plain data in, plain data out — no Request/Response/FormData
- Adapters are trivial glue: resolve deps → call service → handle revalidation
- One service, many callers: server action + route handler + MCP tool all call same service

---

## React Forms | ref: .claude/skills/react-form-builder/SKILL.md

**What breaks if you deviate:**
| Deviation | Impact |
|-----------|--------|
| Missing `useTransition` | No loading state — users double-submit |
| Missing `isRedirectError` | Errors swallowed after successful redirects |
| External UI components | Inconsistent styling, bundle bloat |
| Multiple `useState` for loading/error | State sync bugs |

**Pattern:** `useForm` + `zodResolver` + `startTransition` + `toast.promise`
- Always import from `@/components/ui/form` — check component library before external packages
- Schemas in `_lib/schema/` — shared between client forms and server actions
- `mode: 'onChange'` + `reValidateMode: 'onChange'` for immediate feedback
- `data-test` attributes on all interactive elements

---

## Playwright E2E | ref: .claude/skills/playwright-e2e/SKILL.md

**What makes tests flaky:**
| Anti-Pattern | Impact |
|--------------|--------|
| `page.waitForTimeout()` | Timing-dependent — passes locally, fails in CI |
| Brittle CSS selectors | Break with minor UI changes |
| Shared state between tests | Pass alone, fail together |
| Missing `await` on actions | Race conditions |

**Pattern:** `goto → waitForLoadState → interact → assert`
- Use `data-testid` + ARIA roles + semantic HTML for selectors
- Use Playwright's web-first assertions (auto-retry) via `expect().toBeVisible()`
- Every test fully isolated — no shared state, deterministic setup/teardown
