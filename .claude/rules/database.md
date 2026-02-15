---
paths:
  - "**/*.sql"
  - "**/migrations/**"
  - "**/supabase/**"
---

# Database Patterns — Supabase Postgres

## Schema Files & Migrations

<!-- CUSTOMIZE: Update paths to match your project structure. -->

- Create migrations: `npx supabase db diff --schema public -f <migration_name>`
- Apply migrations: `npx supabase db reset`
- Generate types: `npx supabase gen types typescript --local > types/database.ts`

## Type Inference

Use auto-generated types for compile-time safety. Manually duplicating row shapes creates drift that causes runtime errors when the schema changes:

```typescript
import { Database } from '@/types/database'; // Auto-generated

type Account = Database['public']['Tables']['accounts']['Row'];
type InsertAccount = Database['public']['Tables']['accounts']['Insert'];
```

## SQL Coding Style

- Tables: `snake_case`, plural nouns (`accounts`, `subscriptions`)
- Functions: `snake_case`, verb phrases (`create_team_account`, `verify_nonce`)
- Explicit schema references (`public.accounts` not `accounts`) — without them, `search_path` changes can silently resolve to wrong schemas
- `search_path = ''` on all function definitions — without this, functions can access unintended schemas, creating security vulnerabilities
- `security definer` bypasses the caller's RLS context — using it without justification could expose cross-tenant data. Warn if you use it.

## RLS Helper Functions

Create reusable helper functions for common auth checks to avoid duplicating access-control logic across RLS policies:

```sql
-- Example: Check if user is a member of an account
CREATE OR REPLACE FUNCTION public.has_role_on_account(target_account_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.memberships
    WHERE user_id = (SELECT auth.uid())
    AND account_id = target_account_id
  );
$$;
```

<!-- CUSTOMIZE: Add your project's RLS helper functions here.
Common helpers include: membership check, role check, permission check, ownership check. -->

### RLS Policy Patterns

```sql
-- Team-level access
CREATE POLICY "team_read" ON public.my_table FOR SELECT
  TO authenticated USING (
    public.has_role_on_account(account_id)
  );

-- Personal account access
CREATE POLICY "personal_read" ON public.my_table FOR SELECT
  TO authenticated USING (
    account_id = (select auth.uid())
  );

-- Both personal + team
CREATE POLICY "mixed_read" ON public.my_table FOR SELECT
  TO authenticated USING (
    account_id = (select auth.uid()) OR
    public.has_role_on_account(account_id)
  );
```

## Views

Views without `security_invoker = true` use the view owner's permissions, bypassing the caller's RLS context. This defeats multi-tenant isolation:

```sql
CREATE OR REPLACE VIEW public.my_view
WITH (security_invoker = true) AS
SELECT ...;
```

## Common Patterns

| Pattern | Implementation |
|---------|---------------|
| Account association | `account_id UUID REFERENCES public.accounts(id) ON DELETE CASCADE NOT NULL` |
| Timestamps | `CREATE TRIGGER ... EXECUTE FUNCTION public.trigger_set_timestamps()` |
| User tracking | `CREATE TRIGGER ... EXECUTE FUNCTION public.trigger_set_user_tracking()` |
| Enums | `CREATE TYPE public.my_status AS ENUM('active', 'inactive', 'pending')` |
| Constraints | `CHECK (count >= 0)`, `CHECK (email ~* '^.+@.+\..+$')` |

## OTP / One-Time Tokens

For sensitive operations (account deletion, ownership transfer), use one-time tokens:

```sql
-- Functions: create_nonce(), verify_nonce(), revoke_nonce()
-- Pattern: Generate token → send to user → verify on submission → revoke after use
```

<!-- CUSTOMIZE: If your framework provides OTP components, reference them here. -->
