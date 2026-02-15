---
paths:
  - "**/_components/**/*.tsx"
  - "**/_lib/schema/**/*.ts"
  - "**/_lib/server/server-actions.ts"
---

# Form Patterns

Forms use `react-hook-form` + `zodResolver` + Server Actions. Custom form handling bypasses the shared validation pipeline, creating inconsistent error messages and missing loading states.

## Anti-Patterns

| Avoid | Why | Do Instead |
|-------|-----|-----------|
| `useForm<MyType>(...)` with generic | Breaks type inference from Zod | `useForm({ resolver: zodResolver(Schema) })` — types inferred |
| Custom form handling | Bypasses shared validation pipeline | Use your component library's form components |
| `onSubmit` without `useTransition` | No pending/loading state | Wrap in `startTransition` |

## Complete Form Pattern

### 1. Schema (`_lib/schema/create-note.schema.ts`)

```typescript
import { z } from 'zod';

export const CreateNoteSchema = z.object({
  title: z.string().min(1),
  content: z.string().min(1),
});
```

### 2. Server Action (`_lib/server/server-actions.ts`)

```typescript
'use server';

import { z } from 'zod';
import { createClient } from '@/lib/supabase/server';
import { getSession } from '@/lib/auth';
import { CreateNoteSchema } from '../schema/create-note.schema';

export async function createNoteAction(formData: FormData) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const data = CreateNoteSchema.parse(Object.fromEntries(formData));
  const supabase = await createClient();

  const { error } = await supabase.from('notes').insert(data);
  if (error) throw error;

  return { success: true };
}
```

<!-- CUSTOMIZE: If your framework provides a Server Action wrapper, use it instead of manual auth + validation. -->

### 3. Form Component (`_components/create-note-form.tsx`)

```tsx
'use client';

import { useTransition } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';

import { CreateNoteSchema } from '../_lib/schema/create-note.schema';
import { createNoteAction } from '../_lib/server/server-actions';

export function CreateNoteForm() {
  const [pending, startTransition] = useTransition();

  // Never add generics to useForm — let zodResolver infer types
  const form = useForm({
    resolver: zodResolver(CreateNoteSchema),
    defaultValues: { title: '', content: '' },
  });

  const onSubmit = form.handleSubmit((data) => {
    startTransition(async () => {
      try {
        await createNoteAction(data);
        toast.success('Note created');
        form.reset();
      } catch {
        toast.error('Failed to create note');
      }
    });
  });

  return (
    <form onSubmit={onSubmit}>
      {/* Use your component library's form fields here */}
      <input {...form.register('title')} placeholder="Title" />
      {form.formState.errors.title && (
        <span>{form.formState.errors.title.message}</span>
      )}

      <textarea {...form.register('content')} placeholder="Content" />
      {form.formState.errors.content && (
        <span>{form.formState.errors.content.message}</span>
      )}

      <button disabled={pending} type="submit">Submit</button>
    </form>
  );
}
```

<!-- CUSTOMIZE: Replace the raw HTML form fields with your component library's Form components
(e.g., shadcn/ui Form, FormField, FormItem, FormLabel, FormControl, FormMessage). -->

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Schema file | `_lib/schema/<name>.schema.ts` | `create-note.schema.ts` |
| Server action file | `_lib/server/server-actions.ts` | Single file per feature |
| Action export | Suffix with `Action` | `createNoteAction` |
| Form component | Descriptive name | `CreateNoteForm` |
