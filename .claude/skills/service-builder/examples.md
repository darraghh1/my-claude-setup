# Service Builder Examples

## Service with Multiple Dependencies

When a service needs more than just a database client, inject all dependencies.

```typescript
// _lib/server/invoice.service.ts
import type { SupabaseClient } from '@supabase/supabase-js';

interface InvoiceServiceDeps {
  client: SupabaseClient;
  storage: SupabaseClient['storage'];
}

export function createInvoiceService(deps: InvoiceServiceDeps) {
  return new InvoiceService(deps);
}

class InvoiceService {
  constructor(private readonly deps: InvoiceServiceDeps) {}

  async generatePdf(invoiceId: string): Promise<{ url: string }> {
    const { data: invoice, error } = await this.deps.client
      .from('invoices')
      .select('*')
      .eq('id', invoiceId)
      .single();

    if (error) throw error;

    const pdf = this.buildPdf(invoice);

    const { data: upload, error: uploadError } = await this.deps.storage
      .from('invoices')
      .upload(`${invoiceId}.pdf`, pdf);

    if (uploadError) throw uploadError;

    return { url: upload.path };
  }

  private buildPdf(invoice: Record<string, unknown>): Uint8Array {
    // Pure logic — no I/O
    // ...
    return new Uint8Array();
  }
}
```

**Server action adapter:**

```typescript
'use server';

import { z } from 'zod';

import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';

import { GenerateInvoiceSchema } from '../schema/invoice.schema';
import { createInvoiceService } from './invoice.service';

export async function generateInvoicePdfAction(input: z.infer<typeof GenerateInvoiceSchema>) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const data = GenerateInvoiceSchema.parse(input);

  const client = await createClient();
  const service = createInvoiceService({
    client,
    storage: client.storage,
  });

  return service.generatePdf(data.invoiceId);
}
```

## Service Composing Other Services

Services can depend on other services — compose at the adapter level.

```typescript
// _lib/server/onboarding.service.ts
import type { ProjectService } from './project.service';
import type { NotificationService } from './notification.service';

interface OnboardingServiceDeps {
  projects: ProjectService;
  notifications: NotificationService;
}

export function createOnboardingService(deps: OnboardingServiceDeps) {
  return new OnboardingService(deps);
}

class OnboardingService {
  constructor(private readonly deps: OnboardingServiceDeps) {}

  async onboardAccount(params: { accountId: string; accountName: string }) {
    // Create default project
    const project = await this.deps.projects.create({
      name: `${params.accountName}'s First Project`,
      accountId: params.accountId,
    });

    // Send welcome notification
    await this.deps.notifications.send({
      accountId: params.accountId,
      type: 'welcome',
      data: { projectId: project.id },
    });

    return { project };
  }
}
```

**Adapter composes the dependency tree:**

```typescript
'use server';

import { z } from 'zod';

import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';

import { OnboardAccountSchema } from '../schema/onboarding.schema';
import { createOnboardingService } from './onboarding.service';
import { createProjectService } from './project.service';
import { createNotificationService } from './notification.service';

export async function onboardAccountAction(input: z.infer<typeof OnboardAccountSchema>) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const data = OnboardAccountSchema.parse(input);

  const client = await createClient();

  const service = createOnboardingService({
    projects: createProjectService(client),
    notifications: createNotificationService(client),
  });

  return service.onboardAccount(data);
}
```

## Pure Validation Service (No I/O)

Some services are entirely pure — they don't even need a database client.

```typescript
// _lib/server/pricing.service.ts

interface PricingInput {
  plan: 'starter' | 'pro' | 'enterprise';
  seats: number;
  billingPeriod: 'monthly' | 'yearly';
}

interface PricingResult {
  unitPrice: number;
  total: number;
  discount: number;
  currency: string;
}

export function calculatePricing(input: PricingInput): PricingResult {
  const basePrices = { starter: 900, pro: 2900, enterprise: 9900 };
  const unitPrice = basePrices[input.plan];
  const yearlyDiscount = input.billingPeriod === 'yearly' ? 0.2 : 0;
  const seatDiscount = input.seats >= 10 ? 0.1 : 0;
  const discount = Math.min(yearlyDiscount + seatDiscount, 0.3);
  const total = Math.round(unitPrice * input.seats * (1 - discount));

  return { unitPrice, total, discount, currency: 'usd' };
}
```

This is the simplest case — a plain function, no class, no dependencies. Trivially testable:

```typescript
import { calculatePricing } from '../pricing.service';

it('applies yearly discount', () => {
  const result = calculatePricing({
    plan: 'pro',
    seats: 1,
    billingPeriod: 'yearly',
  });

  expect(result.discount).toBe(0.2);
  expect(result.total).toBe(2320); // 2900 * 0.8
});
```

## Testing with Mock Client

Full mock pattern for Supabase client:

```typescript
import { vi } from 'vitest';
import type { SupabaseClient } from '@supabase/supabase-js';

/**
 * Creates a chainable mock that mimics Supabase's query builder.
 * Override any method in the chain via the `overrides` param.
 */
export function createMockSupabaseClient(
  resolvedValue: { data: unknown; error: unknown } = { data: null, error: null },
  overrides: Record<string, unknown> = {},
) {
  const chain: Record<string, ReturnType<typeof vi.fn>> = {};

  // Every method returns `this` (chainable) by default
  const methods = [
    'select', 'insert', 'update', 'upsert', 'delete',
    'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'in',
    'like', 'ilike', 'is', 'order', 'limit', 'range',
    'single', 'maybeSingle',
  ];

  for (const method of methods) {
    chain[method] = vi.fn().mockReturnThis();
  }

  // Terminal methods resolve with data
  chain.single = vi.fn().mockResolvedValue(resolvedValue);
  chain.maybeSingle = vi.fn().mockResolvedValue(resolvedValue);

  // Apply overrides
  for (const [key, value] of Object.entries(overrides)) {
    chain[key] = vi.fn().mockImplementation(
      typeof value === 'function' ? value : () => value,
    );
  }

  // Non-terminal chains that don't end with single/maybeSingle
  // resolve when awaited via .then()
  const proxyHandler: ProxyHandler<typeof chain> = {
    get(target, prop) {
      if (prop === 'then') {
        return (resolve: (v: unknown) => void) => resolve(resolvedValue);
      }
      return target[prop as string] ?? vi.fn().mockReturnValue(target);
    },
  };

  const chainProxy = new Proxy(chain, proxyHandler);

  return {
    from: vi.fn(() => chainProxy),
    chain,
  } as unknown as SupabaseClient & { chain: typeof chain };
}
```

Usage:

```typescript
import { createMockSupabaseClient } from '../test-utils';
import { createProjectService } from '../project.service';

it('lists projects for an account', async () => {
  const projects = [
    { id: '1', name: 'Alpha', account_id: 'acc-1' },
    { id: '2', name: 'Beta', account_id: 'acc-1' },
  ];

  const client = createMockSupabaseClient({ data: projects, error: null });
  const service = createProjectService(client);

  const result = await service.list('acc-1');

  expect(result).toEqual(projects);
  expect(client.from).toHaveBeenCalledWith('projects');
  expect(client.chain.eq).toHaveBeenCalledWith('account_id', 'acc-1');
});
```
