---
paths:
  - "**/admin/**"
---

# Admin Section

## Security Context

Admin pages have elevated database access that bypasses RLS. A single oversight here exposes the entire database to unauthorized access:

- Pages without admin guards are accessible to any authenticated user — wrap all admin pages with an admin check
- The admin client (service role) bypasses all RLS policies. Verify admin status server-side before using it.
- Client-side admin checks can be bypassed by modifying JavaScript in the browser. Only server-side validation is reliable.
- Admin operations without audit logging make security incidents untraceable. Log all admin actions.

## Admin Operation Pattern

```typescript
import 'server-only';

import { createClient } from '@/lib/supabase/server';

async function adminOperation() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) throw new Error('Unauthorized');

  // Verify admin status server-side
  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single();

  if (profile?.role !== 'admin') {
    throw new Error('Unauthorized: Admin access required');
  }

  // Safe to proceed with elevated privileges
}
```

<!-- CUSTOMIZE: Replace the admin check with your project's admin verification pattern.
Common patterns: super_admin flag on profile, admin role in memberships, separate admin table. -->

## Admin Server Actions

Admin mutations must verify admin status before processing:

```typescript
'use server';

export async function banUserAction(formData: FormData) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  await verifyAdmin(session.userId); // Your admin check
  const data = BanUserSchema.parse(Object.fromEntries(formData));

  // Only executes if current user is admin
}
```

## Admin Services

Admin services must validate the admin is not acting on their own account:

```typescript
private async assertNotSelf(targetId: string) {
  const { data } = await this.client.auth.getUser();
  if (data.user?.id === targetId) {
    throw new Error('Cannot perform destructive action on your own account');
  }
}
```

## Checklist

- [ ] Admin status validated server-side before operations
- [ ] Operations logged for audit trail
- [ ] Admin cannot act on their own account for destructive operations
- [ ] Sensitive data not exposed in error messages or logs
- [ ] Proper loading states for admin operations
