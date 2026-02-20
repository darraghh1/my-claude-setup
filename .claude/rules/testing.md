---
paths:
  - "**/__tests__/**/*.test.{ts,tsx}"
  - "**/vitest.*.ts"
---

# Testing -- Next.js Supabase TypeScript

## Framework

- **Unit/Integration:** Vitest with happy-dom (default)
- **E2E:** Playwright

## Test Location

Tests go in `__tests__/{feature}/` directories:

```
__tests__/
  auth/                    # Auth feature tests
    login.test.ts
  dashboard/               # Dashboard tests
    dashboard.test.tsx
  helpers/                  # Shared test utilities
```

## Component Tests

The default test environment is `happy-dom` (configured in `vitest.config.ts`). It works correctly for all React component tests:

```typescript
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
```

## Mock Patterns

Use `vi.hoisted()` for mocks that need to be available before module evaluation:

```typescript
const { mockService } = vi.hoisted(() => ({
  mockService: {
    getData: vi.fn(),
  },
}));

vi.mock('@/lib/services/my-service', () => ({
  createMyService: () => mockService,
}));
```

For Supabase client mocks, add `.then()` to make query chains awaitable:

```typescript
const mockChain = {
  select: vi.fn().mockReturnThis(),
  eq: vi.fn().mockReturnThis(),
  single: vi.fn().mockReturnThis(),
  then: vi.fn((resolve) => resolve({ data: mockData, error: null })),
};
```

## Running Tests

```bash
pnpm test                               # All tests
pnpm run test:watch                     # Interactive test watcher
pnpm run test:coverage                  # Test with coverage report
pnpm run typecheck                      # TypeScript check
```

## Radix UI in Tests

Radix Select requires polyfills in `vitest.setup.ts`:

```typescript
Element.prototype.hasPointerCapture = () => false;
Element.prototype.setPointerCapture = () => {};
Element.prototype.releasePointerCapture = () => {};
```

Radix renders text in trigger AND dropdown -- use `getAllByText` not `getByText`.
