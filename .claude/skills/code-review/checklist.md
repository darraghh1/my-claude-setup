# Code Review Checklist

Detailed criteria for reviewing phase implementations against both quality standards and actual codebase patterns.

## Why This Checklist Exists

The user created this checklist after experiencing bugs that shipped to production. Each item represents a real failure mode. When reviewing code, understanding *why* each check matters helps you catch issues rather than just checking boxes.

**Important:** This checklist supplements — not replaces — reading reference implementations. Always read a real file from the codebase (Step 3 in SKILL.md) before applying these rules. If a rule here conflicts with what you see in the codebase, the codebase wins.

## Part 1: Completeness Criteria

### Implementation Steps

For each step in the phase document:
- **Step 0: TDD** - Were test files created?
  - **Backend** (services, schemas, APIs): Full unit tests with real assertions
  - **Frontend** (React components): Component tests using happy-dom (default) and @testing-library/react
- **Step 1-N** - Was each sub-task completed as specified?
- **Documentation step** - Were README/CLAUDE.md updated if required?

### Frontend Test Requirements

- [ ] Component tests use default happy-dom environment (do NOT add jsdom directive — causes ESM errors)
- [ ] Tests use `@testing-library/react` for rendering and queries
- [ ] User interactions tested (clicks, form inputs, etc.)
- [ ] Conditional rendering and state changes verified
- [ ] Server actions and API calls properly mocked
- [ ] Accessibility queries preferred (`getByRole`, `getByLabelText`)

### Requirements

- Each Functional requirement addressed
- Each Technical constraint satisfied

### Acceptance Criteria

- Each criterion met and verifiable

---

## Part 2: Code Quality Criteria

### TypeScript Standards

- [ ] No `any` types — strict TypeScript usage
- [ ] Implicit type inference preferred (explicit only when impossible to infer)
- [ ] Proper error handling with try/catch blocks and typed error objects
- [ ] Clean, clear code without obvious comments
- [ ] Service patterns used for server-side APIs
- [ ] `import 'server-only';` added at top of exclusively server-side files
- [ ] No mixing of client and server imports from the same file or package
- [ ] Consider using classes for server-side services, export factory functions
- [ ] Consider enums or union types of string literals as appropriate
- [ ] Type guards used instead of type assertions (`x as Type`)
- [ ] All types and interfaces exported by default

### React & Next.js Compliance

- [ ] Functional components only with proper `'use client'` directives
- [ ] Repeated code blocks encapsulated into reusable local components
- [ ] useEffect usage flagged as code smell (must be justified)
- [ ] Single state objects preferred over multiple useState (4-5+ is too many)
- [ ] Server-side data fetching uses React Server Components where appropriate
- [ ] Loading indicators (LoadingSpinner) in async operations
- [ ] `data-test` attributes added for E2E testing where needed
- [ ] Forms use `react-hook-form` with your form components (`@/components/ui/form`)
- [ ] Server actions use `'use server'` + Zod validation + `getSession()` auth check
- [ ] Server actions and route handlers use reusable services for business logic
- [ ] Redirects after server actions use `redirect()` with proper `isRedirectError` handling
- [ ] Back-end does not expose sensitive data

### React Forms

Load `/react-form-builder` for full patterns reference.

**Structure:**
- [ ] Uses `useForm` from react-hook-form with `zodResolver`
- [ ] NO redundant generic types on `useForm` (let zodResolver infer)
- [ ] Schema imported from `_lib/schema/` (singular directory)
- [ ] Uses `mode: 'onChange'` and `reValidateMode: 'onChange'`

**Components:**
- [ ] Uses form components: `Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormMessage` from `@/components/ui/form`
- [ ] Uses `@/components/ui/input`, `@/components/ui/button` (not external packages)
- [ ] Uses `Alert` from `@/components/ui/alert` for error display
- [ ] Uses conditional rendering patterns appropriate to the project

**State & Submission:**
- [ ] Uses `useTransition` for pending state (not useState for loading)
- [ ] Uses `useState` only for error state
- [ ] Calls server action inside `startTransition`
- [ ] Handles `isRedirectError` in catch block
- [ ] Submit button disabled during `pending` state
- [ ] Shows toast on success via `toast` from `sonner`

**Testing:**
- [ ] Has `data-test` attributes on form inputs and submit button

### Project Architecture Validation

- [ ] Multi-tenant architecture with proper account-based access control
- [ ] Data uses `account_id` foreign keys for association
- [ ] Personal vs Team accounts pattern implemented correctly
- [ ] Proper Row Level Security (RLS) policies in place
- [ ] UI components from your component library (`@/components/ui`) used instead of external packages
- [ ] Form schemas organized for reusability between server and client
- [ ] Imports follow correct pattern (especially toast, forms, UI components)

### Database Security & Design

Load `/postgres-expert` for full patterns reference.

**Schema Design:**
- [ ] Tables in `supabase/schemas/` with numbered prefixes
- [ ] Uses `extensions.uuid_generate_v4()` for UUIDs
- [ ] Includes `created_at`, `updated_at` timestamps
- [ ] Has `created_by`, `updated_by` user tracking where appropriate
- [ ] Foreign keys have indexes (`ix_table_column`) — *missing indexes cause slow queries as data grows*
- [ ] Uses existing triggers: `trigger_set_timestamps`, `trigger_set_user_tracking`

**RLS Policies (Security Critical):**

These checks prevent data leakage between tenant accounts:

- [ ] RLS enabled on all tables (`alter table enable row level security`) — *without this, RLS policies are ignored*
- [ ] Default permissions revoked (`revoke all from authenticated, service_role`) — *principle of least privilege*
- [ ] Specific permissions granted (`grant select, insert, update, delete to authenticated`)
- [ ] Uses existing helper functions (DO NOT recreate):
  - `has_role_on_account(account_id)` - team membership check
  - `has_permission(user_id, account_id, permission)` - permission check
  - `is_account_owner(account_id)` - ownership check
- [ ] **No `USING(true)` in policies** — *allows ANY authenticated user to access ALL rows, critical security vulnerability*
- [ ] Personal + team access pattern: `account_id = auth.uid() OR has_role_on_account(account_id)`

**Migration Safety:**
- [ ] Uses `IF NOT EXISTS` / `IF EXISTS` for idempotency
- [ ] Indexes created with `CONCURRENTLY` where possible
- [ ] Types generated after migration (`npx supabase gen types typescript --local`)

### Server Actions & API Routes

Load `/server-action-builder` for full patterns reference.

**File Structure & Naming:**
- [ ] Schema in `_lib/schema/{feature}.schema.ts` (singular `schema/` directory)
- [ ] Service in `_lib/server/{feature}.service.ts` — factory function wrapping class
- [ ] Actions in `_lib/server/server-actions.ts` with `'use server'` directive
- [ ] Action export names end in `Action` (e.g., `saveConfigAction`, `deleteItemAction`)
- [ ] Server actions NOT re-exported from `_lib/server/index.ts` barrel file

**Server Action Pattern:**

```typescript
// CORRECT pattern — verify against reference file
'use server';

import { z } from 'zod';
import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';

const MySchema = z.object({ /* ... */ });

export async function myAction(formData: FormData) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const data = MySchema.parse(Object.fromEntries(formData));
  const client = await createClient();
  const service = createFeatureService(client);
  // ... implementation
  return { success: true };
}
```

- [ ] Uses `'use server'` directive at top of file
- [ ] Validates session with `getSession()` before processing
- [ ] Validates input with Zod schema before database operations
- [ ] Creates Supabase client via `createClient()` from `@/lib/supabase/server`

**Account Slug Resolution:**

```typescript
// CORRECT: Resolve slug to ID via DB lookup
const { data: account } = await client
  .from('accounts')
  .select('id')
  .eq('slug', data.accountSlug)
  .single();

// CORRECT: Then check permission with resolved ID
const { data: hasPermission } = await client.rpc('has_permission', {
  user_id: user.id,
  account_id: account.id,
  permission_name: 'manage_integrations',
});
```

- [ ] Account slug resolved to ID via DB lookup (not used directly)
- [ ] `has_permission` RPC called with `user_id`, `account_id`, `permission_name`
- [ ] Error messages use i18n keys (not hardcoded English strings)
- [ ] All queries scoped to `account_id` from the resolved account

**Service Pattern (Factory + Class):**

```typescript
// CORRECT: Factory function wrapping a class
import 'server-only';

import { SupabaseClient } from '@supabase/supabase-js';
import type { Database } from '@/types/database';

export function createFeatureService(client: SupabaseClient<Database>) {
  return new FeatureService(client);
}

class FeatureService {
  private readonly namespace = 'feature';

  constructor(private readonly client: SupabaseClient<Database>) {}

  async getConfig(accountId: string) {
    const { data, error } = await this.client
      .from('feature_config')
      .select('*')
      .eq('account_id', accountId)
      .single();
    if (error) throw error;
    return data;
  }
}
```

- [ ] Factory function `createXxxService(client)` wrapping a private class
- [ ] Takes `SupabaseClient<Database>` as parameter
- [ ] Class has `private readonly client` and `private readonly namespace` for logging
- [ ] `import 'server-only'` at top of service files
- [ ] Methods return data or throw — not `{ success, error }` wrappers

**Revalidation:**
- [ ] Calls `revalidatePath('/home/[account]/...')` after mutations
- [ ] Uses `revalidateTag()` for cache invalidation where appropriate

**Logging:**
- [ ] Uses the project's logger (e.g., from `@/lib/logger`)
- [ ] Logs before and after operations with context object

**Error Handling:**
- [ ] Handles `isRedirectError` when using `redirect()`
- [ ] Re-throws redirect errors after catching
- [ ] Uses standard Supabase client (RLS enforced), admin client only when justified
- [ ] Inner try-catch for operations that could fail (explicit error handling in server actions)
- [ ] Error messages use i18n keys (e.g., `common:unknownError`) — no hardcoded strings
- [ ] No secrets, API keys, or internal paths in error messages

### Import Patterns

**Verify these against the reference file read in Step 3:**

| Import | Correct Source | Common Mistake |
|--------|---------------|----------------|
| `z` | `import { z } from 'zod'` | Wrong import path |
| `Database` | `import { Database } from '@/types/database'` | Wrong path or `~/app/lib/...` |
| `SupabaseClient` | `import { SupabaseClient } from '@supabase/supabase-js'` | Missing `<Database>` generic |
| `createClient` | `import { createClient } from '@/lib/supabase/server'` | Wrong package path |
| `server-only` | `import 'server-only';` at file top | Missing entirely |
| Path aliases | `~/home/[account]/...` | `~/app/home/[account]/...` (tilde = `./app`) |
| `getSession` | `import { getSession } from '@/lib/auth'` | Missing auth check entirely |

### Zod Schema Patterns

- [ ] Uses `z.enum(['value1', 'value2'])` for string unions (not `z.nativeEnum(MyEnum)`)
- [ ] Schema names match pattern: `SaveConfigSchema`, `UpdateItemSchema`, `DeleteItemSchema`
- [ ] Type exports via `z.infer<typeof Schema>` with `export type`
- [ ] Schemas exported for reuse between client validation and server actions

### Input Validation & Error Handling

- [ ] UUID parameters validated before DB queries
- [ ] All external data validated with Zod schemas
- [ ] User text fields sanitized to prevent XSS
- [ ] Generic error messages externally (no implementation details exposed)
- [ ] Detailed internal logging for debugging
- [ ] PII redacted from logs
- [ ] No hardcoded credentials or secrets

### Testing Standards

- [ ] Test files in `__tests__/{feature}/` (not `test/` or `tests/`)
- [ ] Backend code has comprehensive unit tests with real assertions
- [ ] Frontend components have happy-dom-based tests using @testing-library/react
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] Mocks are minimal and focused (don't over-mock)
- [ ] Edge cases and error states are tested
- [ ] Test files use default happy-dom environment (do NOT add jsdom directive — causes ESM errors)
- [ ] TDD stubs use `it.todo('description')` (not empty `it()` blocks)
- [ ] Mock variables use `vi.hoisted()` when needed before module evaluation
- [ ] Supabase client mocks include `.then()` for thenable/awaitable pattern
- [ ] Path aliases in tests: `~/home/...` resolves to `./app/home/...`

### E2E Testing (Playwright)

Load `/playwright-e2e` for full patterns reference.

**Selectors:**
- [ ] Uses `data-test` attributes as primary selectors
- [ ] Falls back to ARIA roles (`getByRole`) and labels (`getByLabel`)
- [ ] Avoids brittle CSS selectors or XPath
- [ ] No reliance on text content that may change

**Waiting & Assertions:**
- [ ] Every Playwright action uses `await`
- [ ] Uses `expect()` with web-first assertions (auto-retry)
- [ ] Uses `waitForLoadState()`, `waitForURL()`, `waitForResponse()` appropriately
- [ ] NO `page.waitForTimeout()` (except as absolute last resort)
- [ ] Chains: interact → wait for response → assert → proceed

**Test Structure:**
- [ ] Tests are isolated (no shared state between tests)
- [ ] Tests can run in any order
- [ ] Uses Page Object Model for complex pages
- [ ] Descriptive test names explaining what and why

**Reliability:**
- [ ] No race conditions from missing waits
- [ ] Handles dynamic content and animations
- [ ] Works across different viewport sizes
- [ ] Resilient to CI/CD timing variations

### Vercel Performance Patterns (React/Next.js Code)

Load `/vercel-react-best-practices` to reference the full 57-rule guide.

**CRITICAL - Eliminating Waterfalls:**
- [ ] Independent operations use `Promise.all()`, not sequential awaits
- [ ] Suspense boundaries wrap async content for streaming
- [ ] API routes start promises early, await late
- [ ] No client-side fetch waterfalls (parallel loading)

**CRITICAL - Bundle Optimization:**
- [ ] No barrel file imports (import directly: `from '@/components/ui/button'` not `from '@/components/ui'`)
- [ ] Heavy components use `next/dynamic` with loading fallback
- [ ] Third-party scripts (analytics, logging) load after hydration
- [ ] Conditional features use dynamic imports

**HIGH - Server-Side Performance:**
- [ ] `React.cache()` used for per-request deduplication
- [ ] Minimal data passed from server to client components
- [ ] Parallel data fetching in server component trees
- [ ] Non-blocking operations use `after()` where available

**MEDIUM - Re-render Optimization:**
- [ ] Derived state computed during render, not in useEffect
- [ ] Expensive computations memoized appropriately
- [ ] `useTransition` for non-urgent state updates
- [ ] Functional `setState` for stable callback references

### Code Quality Metrics

- [ ] No unnecessary complexity or overly abstract patterns
- [ ] Consistent file structure following monorepo patterns
- [ ] Proper package organization in Turborepo structure
- [ ] Established component library (`@/components/ui`) patterns used

---

## Severity Levels

### Critical (Blocks Completion)

These issues represent immediate security risks or data integrity problems:

- **Security vulnerabilities** (RLS bypass, credential exposure) — *attackers can exploit immediately*
- **Data leakage risks between accounts** — *tenant A sees tenant B's data, trust destroyed*
- **Missing `account_id` scoping** — *queries return data from all accounts*
- **`USING(true)` in RLS policies** — *effectively disables row-level security*
- **`any` types in security-critical code** — *type system can't catch authorization bugs*
- **Missing `getSession()` auth check** — *unauthenticated users can call the action*
- **Missing Zod validation in Server Action** — *unvalidated input reaches the database*
- **Bad import paths** — *won't compile, module not found at runtime*

### High Priority

These issues cause bugs or maintenance problems:

- **TypeScript `any` types** — *defeats type safety, bugs caught at runtime not compile time*
- **Missing error handling in async functions** — *unhandled rejections crash the app*
- **Improper RLS policies** — *data access rules don't match business requirements*
- **Missing input validation** — *malformed data corrupts database or causes crashes*
- **Exposed sensitive data** — *error messages leak implementation details*
- **Missing or inadequate tests** — *regressions not caught until production*
- **Frontend components without JSDOM tests** — *UI bugs discovered by users, not CI*
- **Missing account slug resolution** — *using accountId directly instead of slug lookup*
- **Missing `has_permission` check** — *any authenticated user can perform the action*
- **Missing `import 'server-only'`** — *server code could be imported by client bundles*
- **Class instead of factory function** — *violates codebase service pattern*

### Medium Priority
- useEffect usage without justification
- Multiple useState calls (4-5+)
- Missing loading states
- Missing `data-test` attributes
- Custom components when your component library has equivalent
- Wrong directory names (should be `_lib/schema/` singular)
- Hardcoded error messages instead of i18n keys
- Missing `revalidatePath` after mutations
- Exported class instead of factory wrapping private class
- `type` instead of `interface` for object shapes

### Low Priority
- Code organization improvements
- Naming convention suggestions (non-breaking)
- Import ordering
- Minor refactoring opportunities

---

## Output Format

### Overview
Concise summary of overall code quality and compliance level.

### Critical Issues
Security vulnerabilities, data leakage risks, breaking violations.
- Include specific file:line locations
- **Cite reference file** showing the correct pattern
- Provide exact fix recommendations

### High Priority Issues
Violations of core standards that impact functionality.
- Include code snippets showing problem and solution
- **Cite reference file** when the issue is a pattern deviation

### Medium Priority Issues
Best practice violations that should be addressed.
- Provide refactoring suggestions

### Low Priority Suggestions
Improvements for maintainability and consistency.

### Security Assessment
- Authentication/authorization concerns
- Data exposure risks
- Input validation issues
- RLS policy effectiveness

### Positive Observations
Highlight well-implemented patterns to reinforce good practices.

### Action Items
Prioritized list of specific changes needed.
