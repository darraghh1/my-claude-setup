---
paths:
  - "**/app/**/page.tsx"
  - "**/app/**/layout.tsx"
  - "**/app/**/loading.tsx"
---

# Pages, Layouts & Route Patterns

> If your project has a `project-implementation.md` rule, check it for framework-specific overrides.

## Creating a New Page

Every page needs: `generateMetadata` and a `loading.tsx`. Missing `loading.tsx` causes the entire page tree to block on data fetching -- users see a blank screen instead of a loading indicator.

### Page Template

```tsx
// app/home/[account]/my-feature/page.tsx
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'My Feature',
};

async function MyFeaturePage({ params }: { params: Promise<{ account: string }> }) {
  const { account } = await params;
  // Load data via loader function
  return (
    <div>
      <h1>My Feature</h1>
      {/* Content */}
    </div>
  );
}

export default MyFeaturePage;
```

### Loading State (required for every route)

```tsx
// app/home/[account]/my-feature/loading.tsx
export default function Loading() {
  return <div>Loading...</div>;
}
```

## Layout Patterns

### User Layout

```tsx
// app/home/(user)/layout.tsx
import { createClient } from '@/lib/supabase/server';

async function UserLayout({ children }: React.PropsWithChildren) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) redirect('/auth/sign-in');

  return <div>{children}</div>;
}

export default UserLayout;
```

### Team/Account Layout

```tsx
// app/home/[account]/layout.tsx
import { createClient } from '@/lib/supabase/server';

async function TeamLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ account: string }>;
}) {
  const { account } = await params;
  const supabase = await createClient();

  // Load team workspace data
  return <div>{children}</div>;
}

export default TeamLayout;
```

## Dynamic Route Params (Next.js 15+)

Forgetting to `await params` causes runtime errors that are hard to trace because the error message doesn't mention `params`:

```tsx
interface Params {
  params: Promise<{ account: string }>;
}

async function Page({ params }: Params) {
  const { account } = await params;
  // ...
}
```

## Route Organization

```
app/home/
  (user)/           # Personal account context
    settings/
  [account]/        # Team account context (slug-based)
    _components/
    _lib/
      server/   # Loaders, server actions, services
      schema/   # Zod schemas (singular)
    my-feature/
      page.tsx
      loading.tsx
```

## Feature Flags

Common pattern for toggling features:

```typescript
// config/feature-flags.ts
export const featureFlags = {
  enableBilling: process.env.NEXT_PUBLIC_ENABLE_BILLING === 'true',
  enableNotifications: process.env.NEXT_PUBLIC_ENABLE_NOTIFICATIONS === 'true',
};
```
