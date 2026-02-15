<!--
CLAUDE.md Template for Next.js / Supabase / TypeScript Projects

This file provides coding standards and architecture patterns for Claude Code.

SETUP INSTRUCTIONS:
1. Search for all <!-- CUSTOMIZE --> markers
2. Fill in your project-specific details
3. Remove examples that don't apply to your project
4. Adjust rules to match your team's conventions

This template is generalized from a production SaaS setup. Adapt as needed.
-->

<!-- CUSTOMIZE: Replace with a brief description of your project
Example: "Acme SaaS platform — Next.js App Router, Supabase, TypeScript."
-->

## Critical Rules

These rules address recurring mistakes that cause real issues. Each one prevents debugging time, security vulnerabilities, or broken builds:

- Using `any` defeats TypeScript's safety net — bugs and security issues reach production undetected. Use proper types or `unknown`.
- `console.log`/`console.error` in production breaks structured logging, making production debugging impossible. Use a proper logger (e.g., Pino, Winston, or your framework's logging utility).
- Missing `import 'server-only'` allows server code to bundle into the client, leaking API keys and database credentials to the browser.
- Server actions must validate inputs with Zod schemas and verify authentication before processing. Unauthenticated or unvalidated data must never reach the database.
- Tables without RLS expose all rows to any authenticated user — one missing policy means customer data leaks across accounts.
- Forgetting to `await params` in async server components causes runtime errors in Next.js that are hard to trace.
- `useEffect` often masks logic that belongs in a server component, event handler, or derived state. Each use should be justified with a comment.
- Multiple separate `useState` calls that change together cause re-renders and state sync bugs. Prefer a single state object.
- Custom form handling bypasses the shared validation pipeline. Use `react-hook-form` + Zod to keep validation consistent.
- Building custom UI when your component library already has the component creates visual inconsistency and double maintenance. Check your component library first.

<!-- CUSTOMIZE: Add any project-specific or framework-specific critical rules here.
Examples:
- "When merging upstream, propagate infrastructure changes to all product apps."
- "Use your framework's Server Action wrapper for auth + validation on every mutation."
- "Never use the admin Supabase client without documenting why RLS bypass is needed."
-->

## Monorepo

<!-- CUSTOMIZE: List your apps/packages here, or remove this section for single-app projects. -->

## Commands

<!-- CUSTOMIZE: Add your project's dev, build, test, and lint commands here. -->

## Architecture

<!-- CUSTOMIZE: Describe your app's architecture (multi-tenant, data fetching, auth, type safety). -->

## Code Style

- Interfaces over types for object shapes; export all types
- Use type guards, not type assertions
- Service pattern: private class + exported factory function
- Use destructuring: `const { name } = user` not `const name = user.name`
- Use millisecond constants (e.g., `const TIMEOUT = 30_000`) instead of magic numbers
- See `.claude/rules/coding-style.md` for full style guide

## Delegate to Agents

Use the Task tool to delegate tasks to specialized sub-agents. Agents are defined in `.claude/agents/` — check agent descriptions to find the right one for your task.

## Verification

<!-- CUSTOMIZE: Add your project's typecheck, lint, and test commands here. -->
