---
paths:
  - "**/route.ts"
  - "**/route.tsx"
---

# Route Handlers (API Routes)

Every API route handler must validate inputs and authenticate requests. Skipping either means unauthenticated or unvalidated requests reach the handler.

> If your project has a `project-implementation.md` rule, check it for framework-specific overrides.

## Pattern

```typescript
import { z } from 'zod';
import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/lib/supabase/server';

const MySchema = z.object({
  email: z.string().email(),
});

// Authenticated route with validation
export async function POST(request: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const data = MySchema.parse(body);

  // Process validated data...
  return NextResponse.json({ success: true });
}

// Unauthenticated route (use with caution -- e.g., webhooks)
export async function GET() {
  return NextResponse.json({ status: 'ok' });
}
```

## When to Use

| Scenario | Use |
|----------|-----|
| Client Component mutations | Server Actions |
| Client Component data fetching | Route Handlers |
| Webhooks | Route Handlers with signature verification |
| Server Component data fetching | Direct Supabase client (no route handler needed) |
