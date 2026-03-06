---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# Coding Style -- Next.js Supabase TypeScript

## Immutability

Mutations create subtle bugs when the same object is referenced elsewhere. Immutable updates ensure predictable React re-renders:

```typescript
// WRONG: Mutation
user.name = name;

// CORRECT: Immutability
return { ...user, name };
```

## Error Handling & Structured Logging

`console.error` in production breaks structured logging and makes debugging impossible. Use a proper logger for production observability.

Always include a context object with a meaningful `name` and relevant IDs:

```typescript
import { logger } from '@/lib/logger';

const ctx = {
  name: 'notes.create',    // meaningful domain name
  userId: user.id,          // authenticated user
  accountId: data.accountId // relevant entity
};

logger.info(ctx, 'Creating note...');

try {
  const result = await riskyOperation();
  logger.info(ctx, 'Note created successfully');
  return result;
} catch (error) {
  logger.error({ ...ctx, error }, 'Failed to create note');
  throw new Error('User-friendly message');
}
```

## Server Actions

Every Server Action must validate inputs with Zod and verify authentication. See `patterns.md` for the full example pattern.

> If your project has a `project-implementation.md` rule, check it for framework-specific overrides.

Naming conventions:
- File: always name `server-actions.ts`
- Exports: always suffix with `Action` (e.g., `createNoteAction`)
- Schema: in a separate `_lib/schema/` file for reuse with `react-hook-form`

## Server-Only Code

Without `import 'server-only'`, server files can accidentally get bundled into the client -- leaking API keys, database credentials, and internal logic to the browser:

```typescript
import 'server-only';

export function createMyService(client: SupabaseClient<Database>) {
  // ...
}
```

## Client Components

Missing `'use client'` on components that use hooks, state, or browser APIs causes cryptic server-side rendering errors that are hard to debug. Add the directive at the top.

## Input Validation

Use Zod schemas in `_lib/schema/` (singular). Share between client forms and server actions:

```typescript
import { z } from 'zod';

export const ProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().optional(),
});
```

## Import Ordering

```typescript
'use client';

// 1. React
import { useState } from 'react';

// 2. Third-party
import { formatDistanceToNow } from 'date-fns';
import { Bell, CheckCircle } from 'lucide-react';

// 3. Internal packages / component library
import { useSupabase } from '@/lib/supabase/hooks';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// 4. Local imports
import { MyComponent } from './_components/my-component';
```

## React

- `useEffect` is a code smell -- must be justified, avoid if possible
- Prefer single state object over multiple `useState` calls (unless independent)
- Prefer server-side data fetching with RSC over client-side fetching
- Display loading indicators where appropriate
- Add `data-test` attributes for E2E tests on interactive elements
- Encapsulate repeated UI blocks into reusable local components
- Use named exports for components, not default exports (except page/layout files)
- Use Container/Presenter pattern to separate data fetching from rendering
- Apply `useMemo` for expensive calculations, `useCallback` for props passed to children
- Use `React.lazy()` / dynamic imports for code splitting when appropriate
