---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# Patterns — Next.js Supabase TypeScript

Consistent patterns across the codebase make code easier for future developers (and Claude) to navigate.

## Data Fetching: Server Components with Loaders

Async server components call loader functions for initial data:

```typescript
// Page: app/home/[account]/projects/page.tsx
async function ProjectsPage({ params }: Props) {
  const { account } = await params;
  const supabase = await createClient();
  const projects = await loadProjectsPageData(supabase, account);
  return <ProjectsList projects={projects} />;
}
```

```typescript
// Loader: _lib/server/projects-page.loader.ts
import 'server-only';

import { SupabaseClient } from '@supabase/supabase-js';
import { Database } from '@/types/database';

export async function loadProjectsPageData(
  client: SupabaseClient<Database>,
  slug: string,
) {
  const { data, error } = await client
    .from('projects')
    .select('*')
    .eq('account_slug', slug);
  if (error) throw error;
  return data ?? [];
}
```

## Mutations: Server Actions with Validation

Every Server Action must validate inputs and verify authentication:

```typescript
// _lib/server/server-actions.ts
'use server';

import { z } from 'zod';
import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';
import { createProjectsService } from './projects.service';
import { CreateProjectSchema } from '../schema/create-project.schema';

export async function createProjectAction(formData: FormData) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const data = CreateProjectSchema.parse(Object.fromEntries(formData));
  const supabase = await createClient();
  const service = createProjectsService(supabase);
  return service.createProject(data);
}
```

<!-- CUSTOMIZE: If your framework provides a Server Action wrapper that handles auth + validation,
use it consistently instead of manual checks. -->

## Service Pattern

Private class + factory function enables dependency injection for testing while keeping class internals hidden:

```typescript
import 'server-only';

import { SupabaseClient } from '@supabase/supabase-js';
import { Database } from '@/types/database';

class ProjectsService {
  constructor(private client: SupabaseClient<Database>) {}

  async createProject(data: CreateProjectData) {
    const { data: result, error } = await this.client
      .from('projects')
      .insert(data)
      .select()
      .single();
    if (error) throw error;
    return result;
  }
}

export function createProjectsService(client: SupabaseClient<Database>) {
  return new ProjectsService(client);
}
```

## Supabase Client Selection

<!-- CUSTOMIZE: Update import paths to match your Supabase client setup.
If using @supabase/ssr, typical pattern is createClient() for server and createBrowserClient() for client. -->

| Context | Client | Import |
|---------|--------|--------|
| Server Components, Actions, Route Handlers | `createClient()` | `@/lib/supabase/server` |
| Client Components | `createBrowserClient()` or `useSupabase()` | `@/lib/supabase/client` |
| Bypassing RLS (rare) | Admin client | `@/lib/supabase/admin` |

## Route Structure

```
app/home/[account]/
├── feature/
│   ├── page.tsx                    # Server Component page
│   ├── _components/                # Feature-specific UI
│   │   └── feature-list.tsx
│   └── _lib/
│       ├── server/                 # Server-side logic
│       │   ├── feature-page.loader.ts
│       │   └── server-actions.ts
│       └── schema/                 # Zod validation (singular)
│           └── feature.schema.ts
```

## Multi-Tenant Account Model

<!-- CUSTOMIZE: Adjust to match your auth/account model. Remove if not multi-tenant. -->

- **Personal Accounts:** User's own workspace
- **Team Accounts:** Shared workspaces with members via memberships table
- **Data isolation:** All data links to accounts via `account_id` foreign key
- **RLS enforces access:** No manual auth checks needed with standard Supabase client

## Client-Side Data Fetching: React Query

When fetching data in Client Components, use `useQuery` from `@tanstack/react-query`. Separate the data provider from the presenter:

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { createBrowserClient } from '@/lib/supabase/client';

// Data provider component
function RolesDataProvider({ children }: { children: (data: Role[]) => React.ReactNode }) {
  const client = createBrowserClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['roles'],
    queryFn: () => client.from('roles').select('*').then(({ data }) => data ?? []),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  return children(data);
}

// Presenter component
function RolesList({ roles }: { roles: Role[] }) {
  return <ul>{roles.map(r => <li key={r.id}>{r.name}</li>)}</ul>;
}
```

## Redirect After Server Action

Use `redirect()` server-side. Handle in client with `isRedirectError`:

```typescript
import { isRedirectError } from 'next/dist/client/components/redirect-error';

try {
  await myServerAction(data);
} catch (error) {
  if (isRedirectError(error)) throw error;
  // handle real error
}
```
