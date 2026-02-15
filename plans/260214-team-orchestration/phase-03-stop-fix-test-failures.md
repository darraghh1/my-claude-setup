---
title: "Phase 03: Stop-and-Fix on Test Failures"
description: "Add pre-flight test checks and stop-on-failure logic to prevent broken tests from piling up"
skill: "n/a"
status: done
dependencies: []
tags: [phase, implementation, workflow-automation, testing, quality-gate]
created: 2026-02-14
updated: 2026-02-14
---

# Phase 03: Stop-and-Fix on Test Failures

**Context:** [[plan|Master Plan]] | **Dependencies:** None | **Status:** Pending

---

## Overview

Currently when tests from previous phases fail during current phase implementation, agents ignore the failures and pile up broken tests until the end. This makes debugging cascading failures extremely difficult.

**Goal:** Add pre-flight test checks before deploying builders for phase N, update builder/validator prompts to require green test suite, and document the pattern in the anti-patterns table.

---

## Context & Workflow

### How This Phase Fits Into the Project

- **UI Layer:** N/A — workflow automation only
- **Server Layer:** N/A
- **Database Layer:** N/A
- **Integrations:** None — modifies skill definition file

### User Workflow

**Trigger:** `/implement` about to deploy builders for phase N (where N > 1)

**Steps:**
1. **NEW:** Pre-flight test check runs BEFORE deploying builders
2. If tests FAIL (and failures are NOT from current phase's TDD):
   - STOP deployment
   - Identify which previous phase's tests are failing
   - Create fix task for broken tests
   - Assign fix task to builder
   - Re-run tests to confirm fix
   - Only then proceed with current phase builders
3. **NEW:** Builder completes task, runs test suite for affected area
4. **NEW:** If ANY tests fail (including previous phases), STOP and fix before marking complete
5. **NEW:** Validator runs full test suite, reports FAIL if any test failures exist

**Success Outcome:** Broken tests from previous phases never reach current phase implementation. Each phase starts with a green test suite.

### Problem Being Solved

**Pain Point:** Broken tests pile up across phases, creating cascading failures that are hard to debug and requiring extensive backtracking to identify which phase broke which test.

**Alternative Approach:** Manual test running between phases, which gets skipped due to time pressure.

### Integration Points

**Upstream Dependencies:**
- Test suite must exist and be runnable (`npm test` or equivalent)
- `/implement` skill defines builder and validator behavior

**Downstream Consumers:**
- All `/implement` invocations on multi-phase plans
- Builder and validator agents spawned by `/implement`

**Data Flow:**
```
/implement ready to deploy builders for phase N
→ NEW: Run pre-flight test check
→ If failures from previous phases:
  → STOP
  → Create fix task
  → Deploy builder to fix
  → Re-run tests
  → Confirm green
→ Deploy builders for current phase
→ NEW: Builder runs tests after implementing
→ NEW: Validator runs full test suite
```

---

## Prerequisites & Clarifications

**Purpose:** Resolve ambiguities before implementation begins.

### Questions for User

1. **Test Command:** What command should pre-flight check run?
   - **Context:** Need to know exact command to run test suite
   - **Assumptions if unanswered:** `npm test` (standard Node.js convention)
   - **Impact:** If wrong, pre-flight check won't detect failures

2. **Test Scope:** Should pre-flight run full suite or subset?
   - **Context:** Full suite might be slow, subset might miss issues
   - **Assumptions if unanswered:** Full suite for completeness
   - **Impact:** If wrong, either too slow or misses failures

3. **Phase 01 Exemption:** Should phase 01 skip pre-flight check?
   - **Context:** Phase 01 has no previous phases, so no previous tests to check
   - **Assumptions if unanswered:** Yes, skip for phase N=1, only run for N>1
   - **Impact:** If wrong, phase 01 fails unnecessarily

### Validation Checklist

- [ ] All questions answered or assumptions explicitly approved
- [ ] User has reviewed phase deliverables and confirmed expectations
- [ ] Dependencies from prior phases are confirmed available (none)
- [ ] Environment variables and credentials are documented (none)
- [ ] Any third-party services/APIs are registered and configured (none)

---

## Requirements

### Functional

- Add pre-flight test check to `/implement` Step 7 (before deploying builders)
- Pre-flight check runs ONLY for phase N where N > 1
- Pre-flight check runs test suite command (e.g., `npm test`)
- If failures exist AND failures are NOT from current phase's TDD step:
  - STOP builder deployment
  - Identify failing tests and which phase they belong to
  - Create fix task with specific test names
  - Deploy builder to fix
  - Re-run tests to confirm green
  - Only then deploy builders for current phase
- Update builder prompt template to include "run tests after implementing, fix failures before marking complete"
- Update validator checks to include "run full test suite, report FAIL if any failures"
- Add to "Patterns That Prevent User-Reported Failures" table

### Technical

- Modify `.claude/skills/implement/SKILL.md` Step 7 (insert new 7c, renumber 7c→7d, 7d→7e, 7e→7f)
- Modify builder prompt template in Step 7d (formerly 7c)
- Modify validator prompt template in Step 7e (formerly 7d)
- Add entry to anti-patterns table at end of skill file
- Version bump: 1.2.0 → 1.3.0 (cumulative with Phase 01 and Phase 02)

---

## Decision Log

### Full Test Suite vs Subset (ADR-03-01)

**Date:** 2026-02-14
**Status:** Accepted

**Context:**
Full test suite might be slow (30+ seconds on large projects). Subset might miss regressions in unrelated areas.

**Decision:**
Run full test suite for completeness. Speed is secondary to correctness.

**Consequences:**
- **Positive:** Catches all regressions, no missed failures
- **Negative:** Pre-flight check adds 30-60 seconds per phase
- **Neutral:** Acceptable tradeoff for preventing cascading failures

**Alternatives Considered:**
1. **Run subset:** Rejected — risk of missing failures in unrelated code
2. **User configurable:** Rejected — adds complexity, most users want full suite

### Stop vs Warn on Failures (ADR-03-02)

**Date:** 2026-02-14
**Status:** Accepted

**Context:**
Could WARN user about failures and let them decide whether to proceed, or STOP immediately.

**Decision:**
STOP immediately. No deployment until tests are green.

**Consequences:**
- **Positive:** Forces fixing failures, prevents cascading issues
- **Negative:** Slows implementation if failures are unrelated to current work
- **Neutral:** User can choose to skip tests manually if truly unrelated

**Alternatives Considered:**
1. **Warn and proceed:** Rejected — defeats purpose of pre-flight check
2. **User confirmation:** Rejected — friction without benefit

---

## Implementation Steps

### Step 0: Test Definition (TDD)

**Purpose:** This phase modifies skill definition markdown, not unit testable. Validation is manual integration testing.

**Manual Test Plan:**
1. Create test plan where Phase 02 breaks Phase 01's tests
2. Run `/implement` for Phase 03
3. Verify pre-flight check catches broken tests from Phase 01
4. Verify deployment STOPS until tests fixed
5. Verify builders and validators check tests

**No automated tests for this phase.**

---

### Step 1: Add Pre-Flight Test Check to /implement

**File:** `.claude/skills/implement/SKILL.md`

#### 1.1: Insert Pre-Flight Check Before Step 7c

Add new section between Step 7b (Identify Skill and Reference) and Step 7c (Deploy Builders):

```markdown
#### 7c: Pre-Flight Test Check (Phase N > 1)

> **Note:** This inserts a new Step 7c. Renumber existing 7c → 7d, 7d → 7e, 7e → 7f when implementing.

**Purpose:** Ensure tests from previous phases are passing before deploying builders for current phase.

**Skip this check for Phase 01** — no previous phases exist.

**For Phase 02 and later:**

1. **Run test suite:**

   ```bash
   npm test
   ```

2. **Check exit code:**

   - If exit code = 0 → All tests passing, proceed to 7c
   - If exit code ≠ 0 → Tests failing, continue to step 3

3. **Identify failing tests:**

   - Read test output to identify which tests failed
   - Determine which phase's tests are failing (check file paths, test descriptions)
   - If failures are from current phase's TDD step (Step 0), proceed to 7c (expected to fail initially)
   - If failures are from PREVIOUS phases, continue to step 4

4. **STOP deployment:**

   - Do NOT deploy builders for current phase yet
   - Report to user: "Tests from Phase X are failing. Fixing before proceeding with Phase Y."

5. **Create fix task:**

   ```
   TaskCreate({
     subject: "Fix failing tests from Phase X",
     description: "Fix failing tests from phase X: [test-name-1], [test-name-2], ...

     File paths: [affected-test-files]

     Run the test suite to identify failures, debug the cause, and fix the broken code.
     After fixing, re-run tests to confirm green before marking complete."
   })
   ```

6. **Deploy fix builder:**

   Deploy a single builder to address the fix task (use builder pattern from 7c).

7. **Re-run tests:**

   After fix builder completes, re-run `npm test` to confirm green.

8. **Proceed to 7c:**

   Only after tests pass, deploy builders for current phase.

**Why this check exists:** Broken tests from previous phases pile up and create cascading failures that are hard to debug. Fixing each failure as it happens prevents this.
```

#### 1.2: Update Builder Prompt Template (Step 7c)

Add to builder prompt:
```markdown
**Test requirement:** If this task has tests, run them after implementation. If ANY tests fail — including tests from previous phases — STOP and fix them before marking your task complete. Do not leave broken tests for later.

Command: npm test
```

#### 1.3: Update Validator Checks (Step 7d)

Add to validator prompt:
```markdown
**Validator rules:**
- [existing rules]
- Run the full test suite (not just current task's tests)
- If any test failures exist, report FAIL even if the current task's tests pass
- A green task on a red test suite is not acceptable
```

---

### Step 2: Add to Anti-Patterns Table

**File:** `.claude/skills/implement/SKILL.md`

At the end, in "Patterns That Prevent User-Reported Failures" section, add row:

| Ignoring test failures from previous phases | Broken tests pile up, eventually blocking the entire plan with cascading failures that are hard to debug |

---

### Step 3: Bump Version

**File:** `.claude/skills/implement/SKILL.md`

- [ ] Bump version (minor increment from current version at time of implementation)
  - Note: Current SKILL.md is at 1.0.0. If Phases 01 and 02 bump to 1.1.0 and 1.2.0 respectively, this becomes 1.2.0 → 1.3.0. If implementing before those phases, bump from actual current version.

---

### Step 4: Manual Integration Test

#### 4.1: Create Test Plan with Cascading Failures

- [ ] Create 3-phase test plan
- [ ] Phase 01: implements feature with tests
- [ ] Phase 02: implements feature that BREAKS Phase 01's tests
- [ ] Phase 03: unrelated feature

#### 4.2: Test Pre-Flight Check

- [ ] Run `/implement` through Phase 01 (should pass)
- [ ] Run `/implement` for Phase 02 (should create broken tests)
- [ ] Run `/implement` for Phase 03
- [ ] **Verify:** Pre-flight check catches Phase 01 test failures
- [ ] **Verify:** Deployment STOPS
- [ ] **Verify:** Fix task created
- [ ] **Verify:** Builder deployed to fix
- [ ] **Verify:** Tests re-run and pass
- [ ] **Verify:** Phase 03 builders then deploy

#### 4.3: Test Builder Test Running

- [ ] Create task with tests
- [ ] Deploy builder via `/implement`
- [ ] **Verify:** Builder runs tests after implementing
- [ ] **Verify:** Builder stops if tests fail
- [ ] **Verify:** Builder only marks complete when tests green

#### 4.4: Test Validator Test Running

- [ ] Create task, implement, deploy validator
- [ ] **Verify:** Validator runs full test suite
- [ ] **Verify:** Validator reports FAIL if any failures exist

#### 4.5: Cleanup

- [ ] Delete test plans
- [ ] Confirm no regressions

---

## Verifiable Acceptance Criteria

**Critical Path:**

- [ ] Pre-flight test check exists before Step 7c in `/implement`
- [ ] Pre-flight check skipped for Phase 01
- [ ] Pre-flight check STOPS deployment on failures from previous phases
- [ ] Fix task created with specific test names
- [ ] Builder prompt includes test requirement
- [ ] Validator prompt includes full suite check
- [ ] Anti-patterns table updated
- [ ] Version bumped to 1.3.0

**Quality Gates:**

- [ ] Manual integration test passes for cascading failure scenario
- [ ] Existing single-phase plans still work (no regression)
- [ ] Test suite command configurable (currently hardcoded to `npm test`)

**Integration:**

- [ ] Builders run tests after implementing
- [ ] Validators run full test suite
- [ ] Fix tasks correctly identify failing phase

---

## Quality Assurance

### Test Plan

#### Manual Testing

- [ ] **Cascading Failure:** Phase 02 breaks Phase 01 tests, Phase 03 pre-flight catches
  - Expected: Deployment stops, fix task created, tests fixed before proceeding
  - Actual: [To be filled]

- [ ] **Phase 01 Skip:** Phase 01 skips pre-flight check
  - Expected: No pre-flight check, deployment proceeds normally
  - Actual: [To be filled]

- [ ] **Builder Test Run:** Builder implements task, runs tests, stops on failure
  - Expected: Task not marked complete until tests green
  - Actual: [To be filled]

#### Automated Testing

Not applicable — skill definitions not unit testable.

#### Performance Testing

- [ ] **Pre-Flight Overhead:** Measure time for test suite run
  - Target: <60 seconds (acceptable overhead)
  - Actual: [To be measured]

### Review Checklist

- [ ] **Code Review Gate:**
  - [ ] Run `/code-review plans/260214-team-orchestration/phase-03-stop-fix-test-failures.md`
  - [ ] Files: `.claude/skills/implement/SKILL.md`
  - [ ] Critical findings addressed
  - [ ] Phase approved

- [ ] **Pattern Compliance:**
  - [ ] Markdown formatting valid
  - [ ] Version bump follows semver
  - [ ] Backward compatible

---

## Dependencies

### Upstream (Required Before Starting)

- Test suite exists and is runnable via `npm test`
- `/implement` skill defines builder/validator behavior

### Downstream (Will Use This Phase)

- All `/implement` invocations on multi-phase plans

### External Services

None

---

## Completion Gate

### Sign-off

- [ ] All acceptance criteria met
- [ ] Manual integration tests passing
- [ ] Code review passed
- [ ] Existing plans still work
- [ ] Phase marked DONE in plan.md
- [ ] Committed: `feat(workflow): add pre-flight test checks`

---

## Notes

### Technical Considerations

- Test command currently hardcoded to `npm test` — could make configurable in future
- Identifying which phase's tests failed relies on file paths — might need heuristics
- TDD failures (Step 0) should be allowed through pre-flight check (expected to fail initially)

### Known Limitations

- No support for test subsets (always runs full suite)
- No parallel test running (might be slow on large projects)
- Can't distinguish "flaky test" from "real failure" — treats all failures as real

### Future Enhancements

- Configurable test command (support pytest, jest, vitest, etc.)
- Test subset support for faster pre-flight checks
- Flaky test detection (retry failed tests before blocking)
- Test coverage threshold enforcement

---

**Previous:** [[phase-02-accept-all-review-items|Phase 02: Accept All Valid Review Items]]
**Next:** [[phase-04-improve-team-prompts|Phase 04: Improve Team Prompt Quality]]
