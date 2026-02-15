# Database Examples

Reference examples for multi-tenant Supabase projects.

## Accounts Schema

Example location: `supabase/schemas/accounts.sql`

```sql
create table if not exists public.accounts (
  id uuid unique not null default extensions.uuid_generate_v4(),
  primary_owner_user_id uuid references auth.users on delete cascade not null,
  name varchar(255) not null,
  slug varchar(255) unique,
  is_personal_account boolean not null default false,
  picture_url varchar(1000),
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  primary key (id)
);

alter table "public"."accounts" enable row level security;
```

## Account Memberships

Example location: `supabase/schemas/memberships.sql`

```sql
create table if not exists public.accounts_memberships (
  account_id uuid references public.accounts(id) on delete cascade not null,
  user_id uuid references auth.users(id) on delete cascade not null,
  account_role varchar(50) not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  created_by uuid references auth.users(id),
  updated_by uuid references auth.users(id),
  primary key (account_id, user_id)
);

-- RLS policies using helper functions
create policy accounts_memberships_select on public.accounts_memberships
  for select to authenticated using (
    user_id = (select auth.uid())
    or public.has_role_on_account(account_id)
  );
```

## Subscriptions

Example location: `supabase/schemas/subscriptions.sql`

```sql
create table if not exists public.subscriptions (
  id varchar(255) not null,
  account_id uuid not null references public.accounts(id) on delete cascade,
  billing_customer_id varchar(255) not null,
  status public.subscription_status not null,
  currency varchar(10) not null,
  cancel_at_period_end boolean not null default false,
  period_starts_at timestamp with time zone,
  period_ends_at timestamp with time zone,
  trial_starts_at timestamp with time zone,
  trial_ends_at timestamp with time zone,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  primary key (id)
);
```

## Notifications

Example location: `supabase/schemas/notifications.sql`

```sql
create table if not exists public.notifications (
  id uuid primary key default extensions.uuid_generate_v4(),
  account_id uuid references public.accounts(id) on delete cascade not null,
  type public.notification_type not null,
  body jsonb not null default '{}',
  dismissed boolean not null default false,
  link text,
  created_at timestamptz default now() not null
);

-- Only account members can see notifications
create policy read_notifications on public.notifications
  for select to authenticated using (
    public.has_role_on_account(account_id)
  );
```

## Storage Bucket

Example location: `supabase/schemas/storage.sql`

```sql
insert into storage.buckets (id, name, public)
values ('account_image', 'account_image', true)
on conflict (id) do nothing;

-- Storage policies should scope access to the owning account
-- Use your project's helper functions for access control
create policy account_image on storage.objects for all using (
  bucket_id = 'account_image'
  and (
    -- Extract account ID from storage path and verify membership
    public.has_role_on_account(/* extract account_id from name */)
  )
);
```

## Enum Types

```sql
-- Subscription status
create type public.subscription_status as enum (
  'active',
  'trialing',
  'past_due',
  'canceled',
  'unpaid',
  'incomplete',
  'incomplete_expired',
  'paused'
);

-- App permissions
create type public.app_permissions as enum (
  'settings.manage',
  'billing.manage',
  'members.manage',
  'invitations.manage'
);
```
