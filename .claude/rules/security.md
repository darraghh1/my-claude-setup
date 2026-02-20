# Security -- Next.js Supabase TypeScript

> If your project has a `project-implementation.md` rule, check it for framework-specific overrides.

## Row Level Security (RLS)

Every table without RLS exposes all its data to any authenticated user -- this is the most common way customer data leaks between accounts. RLS enforces data isolation automatically:

- **Server Components:** RLS enforces access control via the server Supabase client
- **Server Actions:** RLS validates permissions on mutations
- **No manual auth checks needed** when using standard Supabase client
- **Admin client** (service role key): Only for bypassing RLS in rare cases -- requires careful manual validation

```sql
-- Standard RLS pattern for account-scoped data
CREATE POLICY "Users can view own account data"
  ON my_table FOR SELECT
  USING (account_id IN (
    SELECT account_id FROM memberships
    WHERE user_id = auth.uid()
  ));
```

## Secret Management

```typescript
// Hardcoded secrets get committed to git and leaked -- use env vars
// BAD: const apiKey = "sk-proj-xxxxx";

// GOOD: Environment variables
const apiKey = process.env.OPENAI_API_KEY;

if (!apiKey) {
  throw new Error('OPENAI_API_KEY not configured');
}
```

- `NEXT_PUBLIC_` prefix = exposed to browser. Only use for non-sensitive values.
- Private env vars = server-only. Use for API keys, database URLs, secrets.
- Store secrets in CI/CD env vars, not in `.env` files. Use `.env.local` for local dev.

## Authentication

Every Server Action must verify the user is authenticated before processing. See `patterns.md` for the full Server Action pattern.

## Multi-Tenant Data Isolation

Data without `account_id` or proper RLS policies can leak between tenants -- this is a critical business risk:

- All data must have an `account_id` foreign key
- RLS policies use memberships to verify access
- Cross-account data exposure is a P0 security incident
- Test RLS policies to verify cross-account isolation

## OAuth Callbacks

OAuth callbacks from external providers may not have valid auth cookies:

- Use admin client (service role) for DB operations in OAuth callbacks
- Validate via signed state parameter instead of RLS
- State parameters should be cryptographically signed (HMAC)

## Client Component Data Passing

Client Component props are serialized into the HTML response and visible in browser DevTools. Passing sensitive data here exposes it to any user who inspects the page source:

- Sensitive data (API keys, tokens, secrets) in Client Component props leaks to the browser
- Unsanitized data (raw cookies, client-provided data) can enable XSS when rendered
- Environment variables without `NEXT_PUBLIC_` prefix should stay server-side
- `NEXT_PUBLIC_` prefix on sensitive data exposes it to every user's browser

## Security Checklist

Each item addresses a vulnerability that commonly causes production incidents:

- [ ] No hardcoded secrets -- they persist in git history permanently, even after deletion
- [ ] All user inputs validated with Zod schemas -- unvalidated input enables injection attacks
- [ ] RLS policies on new tables -- missing RLS exposes all rows to any authenticated user
- [ ] Server-only code has `import 'server-only'` -- without it, secrets leak to the browser bundle
- [ ] Error messages don't leak sensitive data -- stack traces and DB errors expose internal architecture
- [ ] Admin client usage is justified and documented -- it bypasses all access controls
