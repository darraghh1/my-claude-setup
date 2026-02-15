---
title: "Phase 01: Integrate Flow Audit Gate"
description: "Add mandatory flow audit check to /implement before starting implementation"
skill: "n/a"
status: done
dependencies: []
tags: [phase, implementation, workflow-automation, quality-gate]
created: 2026-02-14
updated: 2026-02-14
---

# Phase 01: Integrate Flow Audit Gate

**Context:** [[plan|Master Plan]] | **Dependencies:** None | **Status:** Pending

---

## Overview

Add a mandatory flow audit check to the `/implement` skill between Step 1 (Read and Review the Plan) and Step 2 (Find Next Pending Phase). This ensures plans with 3+ phases have their flow coherence verified before implementation begins.

**Goal:** Integrate `/audit-plan` as a required quality gate that catches structural plan issues (circular dependencies, wrong ordering, stale artifacts) before implementation when they're 10x cheaper to fix.

---

## Context & Workflow

### How This Phase Fits Into the Project

- **UI Layer:** N/A — workflow automation only
- **Server Layer:** N/A
- **Database Layer:** N/A
- **Integrations:** None — modifies skill definition file only

### User Workflow

**Trigger:** User invokes `/implement plans/feature-name/`

**Steps:**
1. `/implement` reads and reviews plan.md (existing Step 1)
2. **NEW:** Check if flow audit exists at `$ARGUMENTS/reviews/planning/flow-audit.md`
3. **NEW:** If no audit AND plan has 3+ phases, run `/audit-plan $ARGUMENTS` first
4. **NEW:** Read audit report's "Overall Assessment" field
5. **NEW:** Gate behavior:
   - "Major Restructuring Needed" → STOP, report to user
   - "Significant Issues" → WARN, list Critical/High items, ask user to proceed
   - "Minor Issues" or "Coherent" → proceed, note items for awareness
6. Continue to Step 2 (Find Next Pending Phase) if gate passes

**Success Outcome:** Plans with structural problems are caught before implementation starts, saving hours of wasted work.

### Problem Being Solved

**Pain Point:** Plans with circular dependencies, wrong phase ordering, or stale artifacts proceed to implementation where discovering these problems costs 10x more to fix (hours of refactoring vs 5 minutes of plan restructuring).

**Alternative Approach:** Manual plan review before implementing, which is often skipped due to time pressure.

### Integration Points

**Upstream Dependencies:**
- `/audit-plan` skill must exist and produce reports at `$ARGUMENTS/reviews/planning/flow-audit.md`
- Audit report must have "Overall Assessment" field with severity levels

**Downstream Consumers:**
- `/implement` orchestrator in all future implementation sessions
- Users invoking `/implement` on plans with 3+ phases

**Data Flow:**
```
User invokes /implement
→ Step 1: Read plan.md, verify plan review exists
→ Step 1b (NEW): Check flow audit
  → If no audit: invoke /audit-plan
  → Read audit report
  → Parse Overall Assessment
  → Gate logic (STOP/WARN/PROCEED)
→ Step 2: Find next pending phase (existing)
```

---

## Prerequisites & Clarifications

**Purpose:** Resolve ambiguities before implementation begins.

### Questions for User

1. **Small Plans:** Should 1-2 phase plans skip the audit entirely?
   - **Context:** Overhead of running audit exceeds value for trivial plans
   - **Assumptions if unanswered:** Plans with 1-2 phases skip audit check
   - **Impact:** If wrong, users annoyed by mandatory audit on tiny plans

2. **Audit Verdict Mapping:** Confirm severity levels for gate behavior
   - **Context:** Task description specifies hard block for "Major Restructuring Needed", soft block for "Significant Issues"
   - **Assumptions if unanswered:** Use the mapping from task description exactly as specified
   - **Impact:** If wrong, inappropriate blocking or insufficient blocking

3. **Re-audit After Fixes:** If user fixes issues, should we re-run audit or trust fixes?
   - **Context:** User might fix issues without re-auditing
   - **Assumptions if unanswered:** Trust user fixes — don't force re-audit loop
   - **Impact:** If wrong, fixed issues might not actually be fixed

### Validation Checklist

- [ ] All questions answered or assumptions explicitly approved
- [ ] User has reviewed phase deliverables and confirmed expectations
- [ ] Dependencies from prior phases are confirmed available (none for this phase)
- [ ] Environment variables and credentials are documented (none required)
- [ ] Any third-party services/APIs are registered and configured (none required)

---

## Requirements

### Functional

- Add Step 1b to `/implement` skill between existing Step 1 and Step 2
- Check for `$ARGUMENTS/reviews/planning/flow-audit.md` existence
- If no audit AND plan has 3+ phases, invoke `/audit-plan $ARGUMENTS`
- Read audit report and extract "Overall Assessment" severity level
- Implement gate logic:
  - "Major Restructuring Needed" → STOP, report critical issues to user
  - "Significant Issues" → WARN, list Critical/High items, ask user to proceed
  - "Minor Issues" or "Coherent" → proceed, optionally note items
- Plans with 1-2 phases skip audit check entirely

### Technical

- Modifications limited to `.claude/skills/implement/SKILL.md`
- Count phases by reading Phase Table in plan.md
- Use Read tool to access audit report
- Parse markdown to extract "Overall Assessment" field value
- Preserve existing Step 1 and Step 2 unchanged (only insert Step 1b between them)
- Version number bumped from 1.0.0 to 1.1.0 in frontmatter

---

## Decision Log

### Skip Audit for Small Plans (ADR-01-01)

**Date:** 2026-02-14
**Status:** Accepted

**Context:**
Plans with only 1-2 phases are typically simple (e.g., "add a button", "update schema"). Running a full flow audit adds overhead (30 seconds) that exceeds the value for such small plans.

**Decision:**
If phase count is 1-2, skip the audit check entirely and proceed directly to Step 2.

**Consequences:**
- **Positive:** No audit overhead for trivial plans
- **Negative:** Tiny plans with structural issues won't be caught (acceptable risk given simplicity)
- **Neutral:** Adds phase counting logic to Step 1b

**Alternatives Considered:**
1. **Always audit:** Rejected — overhead exceeds value for small plans
2. **User flag to skip:** Rejected — adds complexity, user shouldn't have to decide

### Hard Block vs Soft Block Thresholds (ADR-01-02)

**Date:** 2026-02-14
**Status:** Accepted

**Context:**
Audit reports have 4 severity levels: "Coherent", "Minor Issues", "Significant Issues", "Major Restructuring Needed". Need to map these to gate behavior.

**Decision:**
- "Major Restructuring Needed" → HARD BLOCK (STOP immediately, user must fix)
- "Significant Issues" → SOFT BLOCK (WARN, present issues, user decides to proceed or fix)
- "Minor Issues" or "Coherent" → PROCEED (note items for awareness, don't block)

**Consequences:**
- **Positive:** Only truly broken plans hard block; user has agency for judgment calls
- **Negative:** User might proceed despite Significant Issues and regret it later
- **Neutral:** Matches task description specification

**Alternatives Considered:**
1. **Hard block on Significant:** Rejected — too strict, user loses agency
2. **Never block, always warn:** Rejected — defeats purpose of mandatory gate

---

## Implementation Steps

### Step 0: Test Definition (TDD)

**Purpose:** This phase modifies a skill definition markdown file, which is not unit testable. Validation is manual integration testing with actual plan execution.

**Manual Test Plan:**
1. Create a 5-phase test plan
2. Invoke `/implement` on the test plan without pre-existing audit
3. Verify audit is invoked automatically
4. Verify gate logic works for each severity level
5. Verify 1-2 phase plans skip audit

**No automated tests for this phase.**

---

### Step 1: Add Step 1b to /implement SKILL.md

**File:** `.claude/skills/implement/SKILL.md`

Insert new Step 1b between existing Step 1 and Step 2.

#### 1.1: Read the Current File

- [ ] Read `.claude/skills/implement/SKILL.md` completely
- [ ] Locate Step 1 end and Step 2 start
- [ ] Note the exact markdown structure for consistency

#### 1.2: Draft Step 1b Content

New section to insert:

```markdown
### Step 1b: Check Flow Audit

Before proceeding to find the next phase, verify the plan's flow has been audited for structural coherence.

**1. Count phases:**

Read the Phase Table in plan.md and count how many phase rows exist (excluding header).

**2. Skip audit for small plans:**

If phase count is 1 or 2, skip this step entirely and proceed to Step 2. The audit overhead exceeds value for trivial plans.

**3. Check if audit exists:**

Look for `$ARGUMENTS/reviews/planning/flow-audit.md`.

**4. Run audit if missing:**

If no audit exists AND phase count is 3+, invoke:

    /audit-plan $ARGUMENTS

Wait for audit to complete before continuing.

**5. Read the audit report:**

Read `$ARGUMENTS/reviews/planning/flow-audit.md` and extract the "Overall Assessment" field value.

**6. Gate logic:**

| Overall Assessment | Behavior |
|--------------------|----------|
| **"Major Restructuring Needed"** | **HARD BLOCK:** STOP immediately. Report the Critical and High issues from the audit to the user. Do not proceed to implementation. The plan has structural problems that must be fixed first. |
| **"Significant Issues"** | **SOFT BLOCK:** WARN the user. List the Critical and High issues from the audit. Ask the user: "The plan has significant structural issues. Do you want to proceed anyway, or fix these first?" Respect user's decision. |
| **"Minor Issues"** or **"Coherent"** | **PROCEED:** Optionally note any Medium issues for awareness, but continue to Step 2. These don't block implementation. |

**Why this gate exists:** Plans with circular dependencies, wrong phase ordering, or stale artifacts are 10x costlier to fix during implementation than before it starts. Catching these early saves hours of rework.
```

#### 1.3: Insert Step 1b

- [ ] Use Edit tool to insert the new Step 1b section
- [ ] Preserve all existing Step 1 content
- [ ] Preserve all existing Step 2 and later content
- [ ] Verify markdown formatting is consistent

#### 1.4: Update "Hard gates that block implementation" Section

If a summary table exists in the workflow overview, add the flow audit gate to it.

---

### Step 2: Bump Version Number

**File:** `.claude/skills/implement/SKILL.md`

#### 2.1: Update YAML Frontmatter

- [ ] Change `version: 1.0.0` to `version: 1.1.0`
- [ ] This is a minor version bump (new feature, backward compatible)

---

### Step 3: Manual Integration Test

#### 3.1: Create Test Plan

- [ ] Create a 5-phase test plan in `plans/test-audit-gate/`
- [ ] Do NOT create a flow audit file initially

#### 3.2: Invoke /implement

- [ ] Run `/implement plans/test-audit-gate/`
- [ ] Verify Step 1b runs automatically
- [ ] Verify `/audit-plan` is invoked
- [ ] Verify audit report is created at `plans/test-audit-gate/reviews/planning/flow-audit.md`

#### 3.3: Test Gate Logic

Create test scenarios:

**Scenario 1: Major Restructuring Needed**
- [ ] Modify test plan to have circular dependencies
- [ ] Run `/implement`
- [ ] Verify HARD BLOCK behavior (stops immediately)

**Scenario 2: Significant Issues**
- [ ] Modify test plan to have ordering issues but not circular deps
- [ ] Run `/implement`
- [ ] Verify SOFT BLOCK behavior (warns, asks user)

**Scenario 3: Minor Issues or Coherent**
- [ ] Fix test plan to be coherent
- [ ] Run `/implement`
- [ ] Verify PROCEED behavior (notes items, continues)

**Scenario 4: Small Plan (1-2 phases)**
- [ ] Create a 2-phase test plan
- [ ] Run `/implement`
- [ ] Verify audit is skipped entirely

#### 3.4: Cleanup

- [ ] Delete test plans after validation
- [ ] Confirm no regressions in existing plan execution

---

## Verifiable Acceptance Criteria

**Critical Path:**

- [ ] Step 1b exists in `/implement` SKILL.md between Step 1 and Step 2
- [ ] Gate logic correctly blocks on "Major Restructuring Needed"
- [ ] Gate logic correctly warns on "Significant Issues"
- [ ] Gate logic correctly proceeds on "Minor Issues" or "Coherent"
- [ ] Small plans (1-2 phases) skip audit check entirely
- [ ] Version number bumped to 1.1.0

**Quality Gates:**

- [ ] Manual integration test passes for all 4 scenarios
- [ ] Existing plans (created before this change) still work
- [ ] No regression in Step 1 or Step 2 behavior

**Integration:**

- [ ] `/audit-plan` can be invoked from within `/implement`
- [ ] Audit report is readable and parsable for Overall Assessment field
- [ ] User sees clear messaging for STOP, WARN, PROCEED states

---

## Quality Assurance

### Test Plan

#### Manual Testing

- [ ] **Scenario 1 (Hard Block):** Create plan with circular deps, verify STOP
  - Expected: Implementation halts, critical issues reported to user
  - Actual: [To be filled during testing]

- [ ] **Scenario 2 (Soft Block):** Create plan with ordering issues, verify WARN
  - Expected: User asked to proceed or fix, respects decision
  - Actual: [To be filled during testing]

- [ ] **Scenario 3 (Proceed):** Create coherent plan, verify continues
  - Expected: Step 2 executes normally, no blocking
  - Actual: [To be filled during testing]

- [ ] **Scenario 4 (Skip):** Create 2-phase plan, verify audit skipped
  - Expected: No audit invocation, proceeds directly to Step 2
  - Actual: [To be filled during testing]

#### Automated Testing

Not applicable — skill definitions are not unit testable.

#### Performance Testing

- [ ] **Audit Overhead:** Measure time to run audit on 10-phase plan
  - Target: <30 seconds
  - Actual: [To be measured]

### Review Checklist

- [ ] **Code Review Gate:**
  - [ ] Run `/code-review plans/260214-team-orchestration/phase-01-integrate-flow-audit-gate.md`
  - [ ] Files: `.claude/skills/implement/SKILL.md`
  - [ ] Read review at `reviews/code/phase-01.md`
  - [ ] Critical findings addressed (0 remaining)
  - [ ] Phase approved for completion

- [ ] **Code Quality:**
  - [ ] Markdown formatting valid (no broken headers)
  - [ ] Step numbering consistent
  - [ ] Gate logic table correctly formatted

- [ ] **Pattern Compliance:**
  - [ ] Follows existing step structure in `/implement`
  - [ ] Version number bumped correctly
  - [ ] Backward compatible with existing plans

- [ ] **Integration:**
  - [ ] Works with existing `/audit-plan` skill
  - [ ] Parsable audit report format
  - [ ] User messaging clear and actionable

---

## Dependencies

### Upstream (Required Before Starting)

- `/audit-plan` skill exists and produces reports at `$ARGUMENTS/reviews/planning/flow-audit.md`
- Audit report format includes "Overall Assessment" field with standard severity values

### Downstream (Will Use This Phase)

- All future `/implement` invocations on plans with 3+ phases
- Users who run the planning → implement pipeline

### External Services

None

---

## Completion Gate

### Sign-off

- [ ] All acceptance criteria met
- [ ] Manual integration tests passing for all 4 scenarios
- [ ] Code review passed
- [ ] Existing plans still work (no regression)
- [ ] Phase marked DONE in plan.md
- [ ] Committed: `feat(workflow): integrate flow audit gate in /implement`

---

## Notes

### Technical Considerations

- Phase counting logic must handle edge cases (deprecated phases, renumbered phases)
- Audit report parsing must be robust to format variations
- User decision on soft block should be recorded (maybe in task description or phase notes)

### Known Limitations

- No automated retry if audit fails — user must fix and re-invoke manually
- Audit is a one-time check at start — doesn't re-audit if plan changes mid-implementation
- Small plans (1-2 phases) bypass audit even if they have structural issues (acceptable risk)

### Future Enhancements

- Auto-fix mode for flow audit (automatically restructure plan based on audit findings)
- Continuous audit — re-check flow after each phase completes
- Audit caching — skip re-audit if plan.md unchanged since last audit

---

**Previous:** [[plan|Master Plan]]
**Next:** [[phase-02-accept-all-review-items|Phase 02: Accept All Valid Review Items]]
