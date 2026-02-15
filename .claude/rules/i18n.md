---
paths:
  - "**/locales/**/*.json"
  - "**/i18n/**"
---

# Internationalization (i18n)

<!-- CUSTOMIZE: Update this file to match your i18n setup.
Common libraries: next-intl, react-i18next, next-i18next, or Next.js built-in i18n routing. -->

## Architecture

| Component | Location | Purpose |
|-----------|----------|---------|
| Translation files | `public/locales/[language]/[namespace].json` | Translation strings |
| i18n config | `lib/i18n/` or `i18n.config.ts` | Language/namespace settings |

## Usage

### Server Components

```typescript
// Using next-intl or your i18n library
import { getTranslations } from 'next-intl/server';

export async function generateMetadata() {
  const t = await getTranslations('common');
  return { title: t('myPage') };
}
```

### Client Components

```tsx
'use client';

import { useTranslations } from 'next-intl'; // or useTranslation from react-i18next

export function MyComponent() {
  const t = useTranslations('common');
  return <h1>{t('homeTabLabel')}</h1>;
}
```

## Available Namespaces

<!-- CUSTOMIZE: List your project's translation namespaces.

| Namespace | Content |
|-----------|---------|
| `common` | General UI, navigation, errors |
| `auth` | Authentication text |
| `account` | Account settings, profile |
| `billing` | Subscriptions, payments |
-->

## Adding Translations

1. Add keys to `public/locales/en/<namespace>.json`
2. New namespace? Add to your i18n configuration
3. New language? Add language code to your languages array

## Rules

- Hardcoded strings bypass the translation pipeline, meaning language support cannot be added without finding and replacing every string. Use translation functions for all user-facing text.
- Always provide fallback text for missing translations to keep the UI readable
- Use appropriate namespace for translation keys
- Keep HTML in translations minimal
