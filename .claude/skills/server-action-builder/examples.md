# Server Action Examples

Real examples from the Next.js/Supabase codebase.

## Team Billing Action

Location: `app/home/[account]/billing/_lib/server/server-actions.ts`

```typescript
'use server';

import { z } from 'zod';

import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';

import { TeamCheckoutSchema } from '../schema/team-billing.schema';
import { createTeamBillingService } from './team-billing.service';

export async function createTeamAccountCheckoutSession(input: z.infer<typeof TeamCheckoutSchema>) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const data = TeamCheckoutSchema.parse(input);

  const client = await createClient();
  const service = createTeamBillingService(client);

  return service.createCheckout(data);
}
```

## Team Billing Service

Location: `app/home/[account]/billing/_lib/server/team-billing.service.ts`

```typescript
import 'server-only';

import { SupabaseClient } from '@supabase/supabase-js';

import { logger } from '@/lib/logger';
import { Database } from '@/types/database';

export function createTeamBillingService(client: SupabaseClient<Database>) {
  return new TeamBillingService(client);
}

class TeamBillingService {
  private readonly namespace = 'billing.team-account';

  constructor(private readonly client: SupabaseClient<Database>) {}

  async createCheckout(params: { accountId: string; planId: string }) {
    const ctx = {
      accountId: params.accountId,
      name: this.namespace,
    };

    logger.info(ctx, 'Creating checkout session');

    // ... implementation
  }
}
```

## Action with Redirect

```typescript
'use server';

import { z } from 'zod';
import { redirect } from 'next/navigation';

import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';

import { CreateProjectSchema } from '../schema/project.schema';
import { createProjectService } from './project.service';

export async function createProjectAction(input: z.infer<typeof CreateProjectSchema>) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const data = CreateProjectSchema.parse(input);

  const client = await createClient();
  const service = createProjectService(client);
  const project = await service.create(data);

  redirect(`/home/${data.accountSlug}/projects/${project.id}`);
}
```

## Delete Action with Confirmation

```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';

import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';
import { logger } from '@/lib/logger';

import { DeleteItemSchema } from '../schema/item.schema';

export async function deleteItemAction(input: z.infer<typeof DeleteItemSchema>) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const data = DeleteItemSchema.parse(input);

  const ctx = { name: 'delete-item', userId: session.user.id, itemId: data.itemId };
  logger.info(ctx, 'Deleting item');

  const client = await createClient();

  const { error } = await client
    .from('items')
    .delete()
    .eq('id', data.itemId)
    .eq('account_id', data.accountId);

  if (error) {
    logger.error({ ...ctx, error }, 'Failed to delete item');
    throw error;
  }

  logger.info(ctx, 'Item deleted successfully');

  revalidatePath(`/home/${data.accountSlug}/items`);

  return { success: true };
}
```

## Error Handling with isRedirectError

```typescript
'use server';

import { z } from 'zod';
import { isRedirectError } from 'next/dist/client/components/redirect-error';
import { redirect } from 'next/navigation';

import { getSession } from '@/lib/auth';
import { logger } from '@/lib/logger';

import { FormSchema } from '../schema/form.schema';

export async function submitFormAction(input: z.infer<typeof FormSchema>) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const data = FormSchema.parse(input);

  const ctx = { name: 'submit-form', userId: session.user.id };

  try {
    logger.info(ctx, 'Submitting form');

    await processForm(data);

    logger.info(ctx, 'Form submitted, redirecting');

    redirect('/success');
  } catch (error) {
    if (!isRedirectError(error)) {
      logger.error({ ...ctx, error }, 'Form submission failed');
      throw error;
    }
    throw error;
  }
}
```
