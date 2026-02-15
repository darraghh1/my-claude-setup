---
title: "[Project Name] Master Plan"
description: "[High-level summary of the mission]"
status: pending
priority: P1
tags: [architecture, planning]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Project Name] Master Plan

## Executive Summary

**The Mission:** [One sentence describing the primary objective]

**The Big Shift:** [Describe the fundamental architectural or philosophical change from the previous version, if any.]

> [!NOTE]
> _Example: Moving from direct API calls to server actions with RLS._

**Primary Deliverables:**

1. **[Foundation]:** [Brief description]
2. **[Intelligence/Core]:** [Brief description]
3. **[Experience/UI]:** [Brief description]

---

## Phasing Strategy (Roadmap)

We follow a **[e.g., Progressive Enhancement]** strategy. The goal is to establish the [Spine/Core] first to enable rapid expansion.

### Phase Constraints

- **Size:** 10-15KB max per phase document
- **Scope:** Single implementation session target
- **Dependencies:** Explicit in phase header
- **Review gate:** Code review via `code-quality-reviewer` sub-agent before marking DONE

### Phase File Naming

- Pattern: `phase-NN-descriptive-slug.md`
- Example: `phase-01-docker-setup.md`, `phase-15-persona-index.md`
- No sub-phases (no 01a, 01b) - flat sequential numbering only

### Phase Table

| Phase  | Title                              | Focus              | Status    |
| :----- | :--------------------------------- | :----------------- | :-------- |
| **01** | [Title](./phase-01-slug.md)        | [Core Deliverable] | [Pending] |
| **02** | [Title](./phase-02-slug.md)        | [Core Deliverable] | [Pending] |
| **03** | [Title](./phase-03-slug.md)        | [Core Deliverable] | [Pending] |
| **...** | ...                               | ...                | ...       |

---

## Architectural North Star

**Purpose:** Define the immutable patterns that every phase must follow.

### 1. [Pattern Name, e.g., Server Actions with RLS]

- **Core Principle:** [Why we use this]
- **Enforcement:** [How it is implemented]

### 2. [Pattern Name, e.g., Supabase RLS First]

- **Core Principle:** All data access through RLS-protected queries.
- **Enforcement:** No admin client usage without explicit justification.

### 3. [Pattern Name, e.g., Component Library Priority]

- **Core Principle:** Use your component library (e.g., `@/components/ui/*`) before custom implementations.
- **Enforcement:** Review for custom components that duplicate existing library components.

---

## Project Framework Alignment

<!-- CUSTOMIZE: Document your project's framework patterns here. -->

Deviating from established project patterns causes inconsistency and maintenance burden. Document your framework's conventions below.

### Component Usage Priority

1. **First:** Your component library (e.g., `@/components/ui/*`)
2. **Second:** Well-maintained community packages (e.g., shadcn/ui)
3. **Third:** Custom components (only as last resort)

### Required Utilities

<!-- CUSTOMIZE: Replace these with your project's actual patterns. -->

| Task | Pattern |
|------|---------|
| Server Action | `'use server'` + Zod validation + `getSession()` auth check |
| Route Handler | `NextRequest`/`NextResponse` with manual auth + validation |
| Data Loader | `cache(async () => {...})` |
| Permission | Your RLS helper functions |
| Supabase | `createClient()` from `@/lib/supabase/server` |
| Forms | `react-hook-form` + `@/components/ui/form` + Zod |
| Tables | Your data table component |

---

## Global Decision Log (Project ADRs)

**Purpose:** Record decisions that bind the entire project lifecycle.

### [Global Decision Title] (ADR-G-01)

**Status:** [Accepted]

**Context:** [Why this choice was made for the whole project]

**Decision:** [What we decided]

**Consequences:** [Tradeoffs for all phases]

---

## Security Requirements

The user's codebase follows specific security patterns learned from past vulnerabilities. Deviating causes security regressions that are costly to fix.

### RLS Policy Rules

- Never use `USING(true)` for any RLS policy
- Always validate `account_id` in policy conditions
- SECURITY DEFINER functions need explicit auth checks
- Prefer SECURITY INVOKER when RLS can enforce access

### Input Validation

- UUID parameters validated before DB queries
- All external data validated with Zod schemas
- User text fields sanitized to prevent XSS

### Authorization

- Helper functions include `account_id` parameter
- Pattern: `function(user_id, account_id)` not `function(user_id)`

### Error Handling

- Generic external messages (no implementation details exposed)
- Detailed internal logging
- PII redacted from logs

---

## Implementation Standards

### Global Test Strategy

- **Unit:** 100% logic coverage in `packages/core`.
- **Integration:** Required for cross-layer features (UI + Server + DB).
- **E2E:** Scenario-based testing in Playwright.

### Global Documentation Standard

The user depends on documentation updates to understand changes across sessions. Skipping these causes confusion and lost context in future work:

1. `packages/[component]/README.md` (Usage)
2. `packages/[component]/ARCHITECTURE.md` (Design)
3. Root `CLAUDE.md` (Commands)
4. Root `ARCHITECTURE.md` (System Topology)

---

## Success Metrics & Quality Gates

### Project Success Metrics

- [Metric 1, e.g., <2s Briefing Load]
- [Metric 2, e.g., 100% Type Safety]
- [Metric 3, e.g., WCAG 2.1 AA Compliance]

### Global Quality Gates (Pre-Release)

- [ ] No `TODO` comments in `main` branch
- [ ] Documentation coverage 100%
- [ ] Integration tests pass across all integrations
- [ ] Security audit (Secrets, RLS Policies) complete

---

## Resources & References

- **Design Spec:** [Link to UI/UX docs]
- **API Registry:** [Link to Protocol/Message docs]
- **Environment:** [Link to .env.example or Setup guide]

---

**Next:** [[phase-01-slug|Phase 01: Title]]
