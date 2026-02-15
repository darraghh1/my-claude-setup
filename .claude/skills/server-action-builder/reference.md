# Server Action Reference

## Server Action Pattern

```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';

import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';
import { logger } from '@/lib/logger';

import { MySchema } from '../schema/my.schema';
import { createMyService } from './my.service';

export async function myAction(input: z.infer<typeof MySchema>) {
  // 1. Authenticate
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  // 2. Validate
  const data = MySchema.parse(input);

  // 3. Execute
  const client = await createClient();
  const service = createMyService(client);
  const result = await service.doSomething(data);

  // 4. Revalidate
  revalidatePath('/home/[account]/my-feature');

  return { success: true, data: result };
}
```

### Action Structure

| Step | Purpose | Required |
|------|---------|----------|
| `getSession()` | Verify authentication | Yes (for protected actions) |
| `Schema.parse(input)` | Validate input with Zod | Yes |
| `createClient()` | Get Supabase client with RLS | Yes |
| `createService(client)` | Instantiate service with client | Yes |
| `revalidatePath()` | Refresh cached data | Yes (after mutations) |

### Handler Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `input` | `z.infer<Schema>` | Raw input data from the client |
| `session.user` | `User` | Authenticated user (from `getSession()`) |

## Route Handler Pattern

```typescript
// app/api/my-feature/route.ts
import { NextRequest, NextResponse } from 'next/server';

import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';

import { MySchema } from '../_lib/schema/my.schema';
import { createMyService } from '../_lib/server/my.service';

export async function POST(request: NextRequest) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const data = MySchema.parse(body);

  const client = await createClient();
  const service = createMyService(client);
  const result = await service.doSomething(data);

  return NextResponse.json(result);
}

export async function GET(request: NextRequest) {
  const session = await getSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const url = new URL(request.url);
  const param = url.searchParams.get('param');

  const client = await createClient();
  const service = createMyService(client);
  const result = await service.get(param);

  return NextResponse.json({ data: result });
}
```

## Common Zod Patterns

```typescript
import { z } from 'zod';

// Basic schema
export const CreateItemSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  accountId: z.string().uuid('Invalid account ID'),
});

// With transforms
export const SearchSchema = z.object({
  query: z.string().trim().min(1),
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(10),
});

// With refinements
export const DateRangeSchema = z.object({
  startDate: z.coerce.date(),
  endDate: z.coerce.date(),
}).refine(
  (data) => data.endDate > data.startDate,
  { message: 'End date must be after start date' }
);

// Enum values
export const StatusSchema = z.object({
  status: z.enum(['active', 'inactive', 'pending']),
});
```

## Revalidation

```typescript
import { revalidatePath } from 'next/cache';
import { revalidateTag } from 'next/cache';

// Revalidate specific path
revalidatePath('/home/[account]/items');

// Revalidate with dynamic segment
revalidatePath(`/home/${accountSlug}/items`);

// Revalidate by tag
revalidateTag('items');
```

## Redirect

```typescript
import { redirect } from 'next/navigation';

// Redirect after action
redirect('/success');

// Redirect with dynamic path
redirect(`/home/${accountSlug}/items/${itemId}`);
```

## Logging

```typescript
import { logger } from '@/lib/logger';

// Context object for all logs
const ctx = {
  name: 'action-name',
  userId: session.user.id,
  accountId: data.accountId,
};

// Log levels
logger.info(ctx, 'Starting operation');
logger.warn({ ...ctx, warning: 'details' }, 'Warning message');
logger.error({ ...ctx, error }, 'Operation failed');
```

## Supabase Clients

```typescript
// Standard client (RLS enforced) - pass to services
import { createClient } from '@/lib/supabase/server';
const client = await createClient();
const service = createFeatureService(client);

// Admin client (bypasses RLS - use sparingly)
import { createAdminClient } from '@/lib/supabase/admin';
const adminClient = await createAdminClient();
```

## Error Handling

```typescript
import { isRedirectError } from 'next/dist/client/components/redirect-error';

try {
  await operation();
  redirect('/success');
} catch (error) {
  if (!isRedirectError(error)) {
    // Handle actual error
    logger.error({ error }, 'Operation failed');
    throw error;
  }
  throw error; // Re-throw redirect
}
```
