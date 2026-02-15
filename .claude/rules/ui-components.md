---
paths:
  - "**/_components/**/*.tsx"
  - "**/components/**/*.tsx"
---

# UI Components & JSX Patterns

## Component Library

<!-- CUSTOMIZE: Update to match your component library (shadcn/ui, Radix, your own packages, etc.)

All reusable UI lives in your shared component library. Building custom components when the library
already has the equivalent creates double maintenance and visual inconsistency.

### Import Pattern

```typescript
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
```
-->

Check your component library before building custom UI. Common components to look for:

| Category | Components |
|----------|-----------|
| Actions | Button, IconButton, Link |
| Layout | Card, Page, PageHeader, PageBody |
| Feedback | Dialog, AlertDialog, Toast |
| Forms | Input, Textarea, Select, Checkbox |
| Data | DataTable, List, EmptyState |
| Navigation | Tabs, Breadcrumbs, DropdownMenu |
| Overlays | Sheet, Popover, Tooltip |

## JSX Patterns

### Class Names — Use `cn` for Tailwind Merging

Without `cn`, conflicting Tailwind classes produce unpredictable results. Use `cn` (from `clsx` + `tailwind-merge`) to resolve conflicts deterministically:

```typescript
import { cn } from '@/lib/utils'; // or wherever your cn utility lives

// Merges Tailwind classes correctly, resolves conflicts
<div className={cn('base-class', { 'text-lg': isLarge }, className)} />
```

### Conditional Rendering

```tsx
// Ternary for simple cases
{isLoading ? <Spinner /> : <Content />}

// Early return for complex cases
if (!data) return <EmptyState />;
return <DataView data={data} />;
```

### Toasts

```typescript
import { toast } from 'sonner'; // or your toast library

toast.promise(myAction(data), {
  loading: 'Creating...',
  success: 'Created!',
  error: 'Failed to create',
});
```

## Tailwind Styling

Use theme classes instead of fixed colors for dark mode compatibility:

| Avoid | Use Instead |
|-------|------------|
| `bg-gray-500` | `bg-muted` |
| `text-gray-700` | `text-muted-foreground` |
| `bg-white` | `bg-background` |
| `text-black` | `text-foreground` |
| `bg-blue-500` | `bg-primary` |
| `text-white` on primary | `text-primary-foreground` |
| `border-gray-200` | `border-border` |

## Testing Attributes

Add `data-test` to interactive elements:

```tsx
<button data-test="submit-button">Submit</button>
<form data-test="signup-form">{/* ... */}</form>
```
