# Plan Review Checklist

Detailed criteria for reviewing plans and phases against templates and codebase patterns.

## Why Template Compliance Matters

The user created these templates to ensure planning documents are complete before implementation begins. Each required section exists because missing it caused problems:

| Missing Section | Harm During Implementation |
|-----------------|---------------------------|
| Prerequisites & Clarifications | Wrong assumptions built into code, rework needed |
| Acceptance Criteria | No way to verify completion, scope creep |
| Step 0: TDD | Tests written after code (or not at all), bugs ship |
| Dependencies | Phase started before prerequisites ready, blocked mid-work |
| Security Requirements | RLS and validation added as afterthought, vulnerabilities |

Catching missing sections now costs 30 seconds. Discovering them during implementation costs hours.

## Plan.md Required Sections

From `../create-plan/references/PLAN-TEMPLATE.md`:

### YAML Frontmatter
- [ ] `title` field present
- [ ] `status` field (pending/in-progress/done)
- [ ] `priority` field
- [ ] `tags` array
- [ ] `created` date
- [ ] `updated` date

### Executive Summary
- [ ] "The Mission" one-sentence objective
- [ ] "The Big Shift" architectural change description
- [ ] Primary Deliverables list (3 items)

### Phasing Strategy
- [ ] Strategy description
- [ ] Phase Constraints subsection (size, scope, dependencies, review gate)
- [ ] Phase File Naming subsection (pattern, examples)
- [ ] Phase Table with columns: Phase, Title, Focus, Status

### Architectural North Star
- [ ] At least one pattern defined
- [ ] Each pattern has Core Principle and Enforcement

### Project Framework Alignment
- [ ] Component Usage Priority (1. project component library, 2. shadcn, 3. custom)
- [ ] Required Utilities table (Server Action pattern, data loaders, etc.)
- [ ] Reference to project documentation or patterns

### Security Requirements
- [ ] RLS Policy Rules subsection
- [ ] Input Validation subsection
- [ ] Authorization subsection
- [ ] Error Handling subsection

### Implementation Standards
- [ ] Global Test Strategy
- [ ] Global Documentation Standard

### Success Metrics & Quality Gates
- [ ] Project Success Metrics list
- [ ] Global Quality Gates checklist

### Global Decision Log
- [ ] At least one ADR or placeholder
- [ ] ADR format: Status, Context, Decision, Consequences

### Resources & References
- [ ] Links to relevant docs

## Phase File Required Sections

From `../create-plan/references/PHASE-TEMPLATE.md`:

### YAML Frontmatter
- [ ] `title` field
- [ ] `description` one-sentence goal
- [ ] `status` field
- [ ] `dependencies` array
- [ ] `tags` array
- [ ] `created` and `updated` dates

### Overview
- [ ] Brief description of deliverables
- [ ] Single-sentence Goal

### Context & Workflow
- [ ] How This Phase Fits Into the Project (UI, Server, Database, Integrations)
- [ ] User Workflow (Trigger, Steps, Outcome)
- [ ] Problem Being Solved

### Prerequisites & Clarifications
- [ ] Questions for User (with Context, Assumptions, Impact)
- [ ] Validation Checklist

### Requirements
- [ ] Functional requirements list
- [ ] Technical constraints list

### Decision Log
- [ ] Section present (even if empty initially)
- [ ] ADR format defined

### Implementation Steps
- [ ] **Step 0: TDD** (first step) — *tests written after code are often skipped; TDD ensures coverage*
  - [ ] Backend Unit Tests (services, schemas, APIs) with real assertions
  - [ ] Frontend Component Tests using happy-dom and @testing-library/react
  - [ ] Run Tests (Should Fail - red phase of TDD)
- [ ] Numbered implementation steps
- [ ] Documentation Updates step

### Verifiable Acceptance Criteria
- [ ] Critical Path checklist
- [ ] Quality Gates checklist
- [ ] Integration checklist

### Quality Assurance
- [ ] Manual Testing section
- [ ] Automated Testing section
- [ ] Performance Testing section
- [ ] Review Checklist with `/code-review` reference

### Dependencies
- [ ] Upstream (Required Before Starting)
- [ ] Downstream (Will Use This Phase)
- [ ] External Services

### Completion Gate
- [ ] Sign-off checklist

## Additional Checks

### Phase Constraints
- [ ] Each phase file < 15KB
- [ ] Dependencies explicit in frontmatter
- [ ] Single implementation session scope

### Cross-References
- [ ] Phase Table links to existing files
- [ ] Phase files reference correct plan.md
- [ ] Dependencies reference valid phase numbers

### Project Pattern Checks

Verify these are **correctly used** (not just mentioned):

- [ ] Project component library used for UI (not raw HTML or custom equivalents)
- [ ] Server Actions use `'use server'` + Zod validation + `getSession()` auth check
- [ ] RLS helpers used (your RLS helper function, your permission check function) -- not custom auth checks
- [ ] `import 'server-only'` present in all server-side files

### Security Mentions

These checks prevent security issues from being designed into the feature:

- [ ] No `USING(true)` instruction present — *would allow any user to access all rows*
- [ ] `account_id` scoping mentioned — *ensures multi-tenant data isolation*
- [ ] Input validation mentioned — *prevents malformed data and injection attacks*
- [ ] Error handling patterns mentioned — *prevents sensitive data leakage in error messages*

---

## Codebase Compliance Checks

**These checks apply to phase files only (not plan.md).** For each code block in the phase, verify patterns match the actual codebase.

### Phase Type Classification

Classify the phase to determine which checks apply:

| Phase Type | Primary Deliverable | Key Checks |
|------------|-------------------|------------|
| **Schema/Database** | SQL migrations, RLS policies | Checks 10 (SQL Safety), 9 (CLAUDE.md Rules) |
| **Service** | `createXxxService()` functions | Checks 1, 4, 5, 6, 7, 9 |
| **Server Action** | Server Action mutations | Checks 1, 2, 3, 4, 5, 7, 8, 9 |
| **Schema (Zod)** | Validation schemas | Checks 1, 4, 5, 7, 9 |
| **UI/Component** | React components, pages | Checks 4, 5, 7, 9 (CLAUDE.md) |
| **Mixed** | Multiple deliverables | All applicable checks |

### Check 1: Naming Conventions

**How to verify:** Glob for existing files matching the pattern, confirm the phase follows the same convention.

| Pattern | Correct | Wrong |
|---------|---------|-------|
| Schema directory | `_lib/schema/` (singular) | `_lib/schemas/` (plural) |
| Schema file | `{feature}.schema.ts` | `{feature}Schema.ts`, `schemas.ts` |
| Action file | `server-actions.ts` or `{feature}-server-actions.ts` | `{feature}-actions.ts`, `actions.ts` |
| Action export names | `saveConfigAction`, `deleteItemAction` | `saveConfig`, `handleDelete` |
| Service file | `{feature}.service.ts` | `{feature}Service.ts` |
| Service factory | `createXxxService(client)` wrapping class | Object literal, exported class |
| Component file | `kebab-case.tsx` | `PascalCase.tsx`, `camelCase.tsx` |

### Check 2: Server Action Pattern

**How to verify:** Read an existing `server-actions.ts` file. Compare auth check, validation, and service usage.

```typescript
// CORRECT pattern from codebase
'use server';

import { z } from 'zod';
import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';
import { createFeatureService } from './feature.service';

const MySchema = z.object({ /* ... */ });

export async function myAction(formData: FormData) {
  const session = await getSession();        // ← Auth check FIRST
  if (!session) throw new Error('Unauthorized');

  const data = MySchema.parse(              // ← Zod validation
    Object.fromEntries(formData)
  );
  const supabase = await createClient();
  const service = createFeatureService(supabase);
  return service.doSomething(data);
}
```

| Check | What to Look For |
|-------|-----------------|
| `'use server'` directive | Missing at top of file |
| `getSession()` auth check | Missing authentication before processing |
| Zod schema validation | Missing `Schema.parse()` on input data |
| Service layer usage | Business logic inline instead of in service |

### Check 3: Account Resolution

**How to verify:** Read an existing server action that operates on account data.

```typescript
// CORRECT: Resolve slug to ID via DB lookup
const { data: account } = await client
  .from('accounts')
  .select('id')
  .eq('slug', data.accountSlug)
  .single();

// CORRECT: Then check permission
const { data: hasPermission } = await client.rpc('has_permission', {
  user_id: user.id,
  account_id: account.id,
  permission_name: 'your_app.manage_feature',
});
```

| Check | What to Look For |
|-------|-----------------|
| Slug → ID resolution | Using `data.accountId` directly instead of slug lookup |
| Permission RPC call | Missing permission check, or wrong RPC name |
| Error messages | Hardcoded user-facing error messages without proper error handling pattern |
| Account scoping | Queries missing `account_id` filter |

### Check 4: Import Patterns

**How to verify:** Read existing files to confirm import sources.

| Import | Correct Source | Common Mistake |
|--------|---------------|----------------|
| `z` | `import { z } from 'zod'` | Wrong import path |
| `Database` | `import { Database } from '@/types/database'` | Wrong path |
| `SupabaseClient` | `import { SupabaseClient } from '@supabase/supabase-js'` | Missing generic `<Database>` |
| `createClient` | `import { createClient } from '@/lib/supabase/server'` | Wrong package |
| `server-only` | `import 'server-only';` at file top | Missing entirely in server files |
| Path aliases | Use `@/` prefix consistently | Mixing alias styles or using wrong base path |

### Check 5: TypeScript Compliance

**How to verify:** Check CLAUDE.md rules and existing code patterns.

| Rule | Correct | Wrong |
|------|---------|-------|
| Services | Classes internally, factory function exported | Exported class, object literal |
| Enums | Consider enums OR union types of string literals | Only `as const` objects |
| Object shapes | `interface Config { ... }` preferred | `type Config = { ... }` |
| Type exports | `export interface`, `export type` | Unexported types |
| Type guards | `function isConfig(x): x is Config` | `x as Config` type assertions |

### Check 6: Service Factory Patterns

**How to verify:** Read an existing `*.service.ts` file or service function.

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

| Check | What to Look For |
|-------|-----------------|
| Factory wrapping class | `createXxxService(client)` returning `new XxxService(client)` |
| Private class | Class is NOT exported, only factory function is |
| Client as constructor param | `private readonly client: SupabaseClient<Database>` |
| `import 'server-only'` | Present at top of service files |
| Namespace property | `private readonly namespace` for logging context |

### Check 7: Export Patterns

**How to verify:** Check how existing features structure their exports.

| Rule | Details |
|------|---------|
| No server actions in barrel exports | `_lib/server/index.ts` should NOT re-export from `server-actions.ts` |
| Type exports always explicit | `export interface`, `export type`, `export enum` |
| Service exports from index | `_lib/server/index.ts` re-exports service factories and types |

### Check 8: Error Handling

**How to verify:** Read existing server actions for error patterns.

| Check | What to Look For |
|-------|-----------------|
| Inner try-catch for operations | Operations that could fail should be wrapped with proper error handling |
| Generic error messages | User-facing errors should not expose implementation details |
| No secrets in errors | Error messages don't include API keys, tokens, or internal paths |
| Typed error returns | `{ success: false, error: string }` not `throw new Error()` for expected failures |

### Check 9: CLAUDE.md Rules

**How to verify:** Read CLAUDE.md and check phase steps against it.

| Rule | What to Flag |
|------|-------------|
| No documentation creation steps | Steps saying "Create README", "Update docs", "Write documentation" |
| `revalidatePath` after mutations | Server actions missing `revalidatePath('/home/[account]/...')` |
| `'use client'` directive | Client components missing the directive |
| `'use server'` directive | Server action files missing the directive |

### Check 10: SQL Safety

**How to verify:** Read existing migrations for patterns.

| Check | What to Look For |
|-------|-----------------|
| `IF EXISTS` / `IF NOT EXISTS` | `DROP` without `IF EXISTS`, `CREATE` without `IF NOT EXISTS` |
| RLS enabled | `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` present |
| `REVOKE` + `GRANT` | Permissions explicitly set, not relying on defaults |
| No `USING(true)` | RLS policies that allow unrestricted access |
| Account scoping in RLS | Policies reference `account_id` or `auth.uid()` |
| Proper cascading | Foreign keys use appropriate `ON DELETE` behavior |

### Check 11: Test Infrastructure

**How to verify:** Read existing test files in `__tests__/`.

| Check | What to Look For |
|-------|-----------------|
| Correct test path | `__tests__/{feature}/` not `test/` or `tests/` |
| `it.todo()` for stubs | TDD stubs use `it.todo('description')` not empty `it()` |
| happy-dom (default) | Component tests use the default happy-dom environment. Only add `// @vitest-environment happy-dom` if explicitly overriding. |
| Mock patterns | Uses `vi.hoisted()` for mock variables, thenable mocks for Supabase |
| Path aliases in tests | Aliases resolve correctly per project config |

### Check 12: Consistency

**How to verify:** Cross-reference the phase file internally and against plan.md.

| Check | What to Look For |
|-------|-----------------|
| Status match | YAML `status` matches plan.md Phase Table status |
| Dependency match | YAML `dependencies` matches Dependencies section |
| Naming across steps | Schema name in Step 1 matches usage in Step 3 |
| File paths across steps | File created in Step 1 imported correctly in Step 3 |
| Feature flag consistency | Same flag name used across all steps |

---

## Severity Definitions

| Severity | Definition | Examples |
|----------|-----------|----------|
| **Critical** | Won't compile or crashes at runtime. Must fix before implementation. | Missing `'use server'` directive; bad import path that doesn't resolve; missing auth check on mutation |
| **High** | Violates security or will cause incorrect behavior. Must fix before implementation. | Missing permission check; `USING(true)` in RLS policy; no account scoping on queries; missing `server-only` import exposing server code |
| **Medium** | Convention violations causing confusion or maintenance burden. Should fix. | Wrong directory name (`schema/` vs `schemas/`); inconsistent naming; hardcoded error messages |
| **Low** | Style or preference issues. Optional fix. | Comment formatting; import ordering; minor naming preferences |
