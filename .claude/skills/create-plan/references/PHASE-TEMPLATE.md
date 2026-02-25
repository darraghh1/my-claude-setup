---
title: "Phase NN: [Title]"
description: "[One sentence goal]"
skill: "[postgres-expert | server-action-builder | service-builder | react-form-builder | playwright-e2e | vercel-react-best-practices | web-design-guidelines | none]"
status: pending
group: "[group-name — identifies connected phases audited together, e.g. auth-system, dashboard-ui, data-pipeline]"
dependencies: []
tags: [phase, implementation]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

<!--
PHASE SIZE CONSTRAINTS:
- Target: 10-15KB file max
- If getting large, split into multiple phases
- Each phase = single implementation session

GROUP FIELD:
- Connected phases share a group name (e.g. "auth-system", "dashboard-ui")
- Groups define audit boundaries — all phases in a group are reviewed together after completion
- A phase belongs to exactly one group
- Single-phase groups are valid for standalone work
- Group ordering determines the implementation sequence: group A before group B if B depends on A
-->

# Phase [NN]: [Title]

**Context:** [[plan|Master Plan]] | **Dependencies:** None or P01, P02 | **Status:** Pending

---

## Overview

[Brief description of what this phase delivers and why it matters]

**Goal:** [One sentence describing the end state]

---

## Context & Workflow

### How This Phase Fits Into the Project

- **UI Layer:** [What pages/components are affected]
  - [Specific user-facing changes]

- **Server Layer:** [What server actions/loaders change]
  - [Specific data operations]

- **Database Layer:** [What schema/RLS changes]
  - [Specific tables or policies affected]

- **Integrations:** [What external services are involved]
  - [Specific API calls or webhooks]

### User Workflow

**Trigger:** [What causes this feature to activate]

**Steps:**
1. [User action or system event]
2. [System response]
3. [Next user action]
4. [Final outcome]

**Success Outcome:** [What the user sees/experiences when working correctly]

### Problem Being Solved

**Pain Point:** [What frustration does this eliminate]
**Alternative Approach:** [What would users do without this feature]

### Integration Points

**Upstream Dependencies:**
- [Phase/Component that must exist before this works]
- [Specific features required]

**Downstream Consumers:**
- [Phase/Component that will use the output of this phase]
- [Specific features that build on this]

**Data Flow:**
```
[ASCII diagram showing how information moves through the system]
```

---

## Prerequisites & Clarifications

**Purpose:** Resolve ambiguities before implementation begins.

### Questions for User

1. **[Topic Area]:** [Specific question about unclear requirement]
   - **Context:** [Why this matters]
   - **Assumptions if unanswered:** [What Claude will assume]
   - **Impact:** [What could go wrong with wrong assumption]

2. **[Topic Area]:** [Next question]
   - **Context:** [Why this matters]
   - **Assumptions if unanswered:** [What Claude will assume]
   - **Impact:** [What could go wrong with wrong assumption]

[Add 3-5 questions covering the most ambiguous aspects of the phase]

### Validation Checklist

- [ ] All questions answered or assumptions explicitly approved
- [ ] User has reviewed phase deliverables and confirmed expectations
- [ ] Dependencies from prior phases are confirmed available
- [ ] Environment variables and credentials are documented
- [ ] Any third-party services/APIs are registered and configured

> [!CAUTION]
> The user configured this checkpoint because proceeding with unresolved questions leads to incorrect implementations requiring rework. Verify all items are checked before continuing.

---

## Requirements

### Functional

- [Functional requirement 1]
- [Functional requirement 2]
- [Functional requirement 3]

### Technical

- [Technical constraint 1]
- [Technical constraint 2]
- [Technical constraint 3]

---

## Decision Log

**Purpose:** Record key decisions made during this phase for future reference

### [Short Title] (ADR-[Phase]-[Number])

**Date:** [YYYY-MM-DD]
**Status:** [Proposed / Accepted / Deprecated / Superseded by ADR-X-Y]

**Context:**
[What problem needed solving? What constraints existed?]

**Decision:**
[What did we decide to do?]

**Consequences:**
- **Positive:** [Benefits of this decision]
- **Negative:** [Tradeoffs or limitations]
- **Neutral:** [Other implications]

**Alternatives Considered:**
1. [Alternative 1]: [Why rejected]
2. [Alternative 2]: [Why rejected]

---

[Additional decisions as they arise during implementation]

---

## Implementation Steps

### Step 0: Test Definition (TDD)

**Purpose:** Define acceptance tests before writing implementation code

#### 0.1: Backend Unit Tests

For services, schemas, utilities, and server-side code:

- [ ] Create test files in `__tests__/` directory
- [ ] Write complete tests with real assertions
- [ ] Define test fixtures and mocks using `vi.mock()` and `vi.hoisted()`
- [ ] Test both success paths and error handling

**Example Backend Test:**

```typescript
describe('MyService', () => {
  it('should return data on success', async () => {
    const result = await service.getData();
    expect(result.data).toHaveLength(3);
  });

  it('should throw on invalid input', async () => {
    await expect(service.getData(null)).rejects.toThrow('Invalid input');
  });
});
```

#### 0.2: Frontend Component Tests

For React components (`.tsx` files):

- [ ] Create test files in `__tests__/` directory
- [ ] Use the default happy-dom environment (do NOT switch to jsdom)
- [ ] Use `@testing-library/react` for rendering and queries
- [ ] Test user interactions, state changes, and conditional rendering
- [ ] Mock server actions and API calls appropriately

**Example Frontend Component Test:**

```typescript
// @vitest-environment happy-dom
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MyComponent } from '../my-component';

describe('MyComponent', () => {
  it('should render initial state', () => {
    render(<MyComponent />);
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  it('should handle form submission', async () => {
    const onSubmit = vi.fn();
    render(<MyComponent onSubmit={onSubmit} />);

    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(onSubmit).toHaveBeenCalled();
  });

  it('should display error on failure', async () => {
    render(<MyComponent error="Something went wrong" />);
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });
});
```

#### 0.3: Run Tests

- [ ] Execute test suite: `npm test`
- [ ] All tests should fail initially (red phase of TDD)
- [ ] Confirm test infrastructure works before implementing

> [!WARNING]
> The user requires TDD to catch regressions early. Starting implementation before tests exist means bugs won't be caught until later, causing significant rework. Define tests first.

---

### Step 1: [First Implementation Step]

#### 1.1: [Sub-task]

- [ ] [Specific action]
- [ ] [Specific action]

#### 1.2: [Sub-task]

- [ ] [Specific action]
- [ ] [Specific action]

[Continue with additional sub-tasks]

---

### Step 2: [Second Implementation Step]

[Same structure as Step 1]

---

---

## Verifiable Acceptance Criteria

**Critical Path:**

- [ ] [Must-have criterion 1]
- [ ] [Must-have criterion 2]
- [ ] [Must-have criterion 3]

**Quality Gates:**

- [ ] [Performance criterion with specific metric]
- [ ] [Security criterion]
- [ ] [Accessibility criterion if applicable]

**Integration:**

- [ ] [Integration test with upstream dependency]
- [ ] [Integration test with downstream consumer]

---

## Quality Assurance

### Test Plan

#### Manual Testing

- [ ] **[Test Category 1]:** [Specific test to perform]
  - Expected: [Expected outcome]
  - Actual: [To be filled during testing]

- [ ] **[Test Category 2]:** [Specific test to perform]
  - Expected: [Expected outcome]
  - Actual: [To be filled during testing]

#### Automated Testing

```bash
# Commands to run automated tests
npm test
npm run test:integration
```

#### Performance Testing

- [ ] **[Performance Metric]:** Target: [Value], Actual: [To be measured]
- [ ] **[Performance Metric]:** Target: [Value], Actual: [To be measured]

### Review Checklist

- [ ] **Code Review Gate:**
  - [ ] Run `/code-review [path-to-this-phase-file]` with file list
  - [ ] Read review at `reviews/code/phase-{NN}.md`
  - [ ] Critical findings addressed (0 remaining)
  - [ ] Run `review:security-reviewer` if RLS/auth changes
  - [ ] Phase approved for completion

  The user depends on code review to catch issues before they reach production. Skipping review or doing it yourself (without using the skill) causes bugs to slip through.

  **Example:**
  ```
  /code-review plans/feature-name/phase-01-database-schema.md
  Files: src/lib/schema.ts, supabase/migrations/001.sql
  ```

- [ ] **Code Quality:**
  - [ ] All tests pass (`npm test`)
  - [ ] Type checking passes (`npm run typecheck`)
  - [ ] No linting errors
  - [ ] Test coverage >80% for critical paths

- [ ] **Error Handling:**
  - [ ] Generic error messages externally (no implementation details exposed)
  - [ ] Detailed internal logging for debugging
  - [ ] Edge cases handled gracefully
  - [ ] PII redacted from logs

- [ ] **Security:**
  - [ ] No hardcoded credentials or secrets
  - [ ] All external input validated with Zod
  - [ ] No sensitive data in logs
  - [ ] RLS policies for any new tables (never `USING(true)`)
  - [ ] Account-scoped functions include `account_id` parameter

- [ ] **Documentation:**
  - [ ] Complex logic has explanatory comments (avoid obvious comments)
  - [ ] README.md updated if public API changed
  - [ ] CLAUDE.md reflects new commands/patterns

- [ ] **Project Pattern Compliance:**
  - [ ] Uses project's component library where available
  - [ ] Server actions validate with Zod and check auth
  - [ ] Pages follow project's export conventions
  - [ ] Uses project's RLS helper functions
  - [ ] Follows data fetching patterns from project docs

- [ ] **Integration:**
  - [ ] Works with upstream phase dependencies
  - [ ] Downstream phases can use new features
  - [ ] Supabase RLS policies prevent cross-account access
  - [ ] Follows data fetching patterns from project docs

---

## Dependencies

### Upstream (Required Before Starting)

- [Phase/Component name]: [Specific feature needed]
- [Package name]: [Specific functionality needed]

### Downstream (Will Use This Phase)

- [Phase/Component name]: [How they'll use this]
- [Package name]: [What they'll consume]

### External Services

- [Service name]: [What it provides]
- [API/Tool]: [Configuration required]

---

## Completion Gate

### Sign-off

- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] Code review passed (see Review Checklist above)
- [ ] Documentation updated
- [ ] Phase marked DONE in plan.md
- [ ] Committed: `[type](scope): phase NN complete`

---

## Notes

### Technical Considerations

- [Important technical note 1]
- [Important technical note 2]

### Known Limitations

- [Limitation 1 and planned mitigation]
- [Limitation 2 and planned mitigation]

### Future Enhancements

- [Planned enhancement from later phases]
- [Potential optimization not in current scope]

---

**Previous:** [[phase-NN-1-slug|Phase NN-1: Title]]
**Next:** [[phase-NN+1-slug|Phase NN+1: Title]]
