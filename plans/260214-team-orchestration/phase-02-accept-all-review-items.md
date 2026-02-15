---
title: "Phase 02: Accept All Valid Review Items"
description: "Update /implement, /review-plan, and delegation docs to fix ALL severity levels, not just Critical"
skill: "n/a"
status: done
dependencies: []
tags: [phase, implementation, workflow-automation, code-review]
created: 2026-02-14
updated: 2026-02-14
---

# Phase 02: Accept All Valid Review Items

**Context:** [[plan|Master Plan]] | **Dependencies:** None | **Status:** Pending

---

## Overview

Currently `/implement` Step 8 only fixes Critical issues from code review. Medium and Low items are presented as "suggestions" but effectively ignored. This creates a disconnect — review skills say "fix these" but the pipeline discards non-critical ones.

**Goal:** Process ALL severity levels during implementation. Critical/High block immediately, Medium/Low are fixed unless clearly hallucinated or purely cosmetic.

---

## Context & Workflow

### How This Phase Fits Into the Project

- **UI Layer:** N/A — workflow automation only
- **Server Layer:** N/A
- **Database Layer:** N/A
- **Integrations:** None — modifies skill and delegation doc files

### User Workflow

**Trigger:** `/implement` completes a phase and runs `/code-review`

**Steps:**
1. Code review completes and writes review file
2. **CURRENT:** /implement Step 8 only fixes Critical issues
3. **NEW:** /implement Step 8 fixes Critical, High, Medium, Low (unless hallucinated)
4. Implementer re-runs review after each fix batch
5. Repeat until verdict is "Yes" with no unfixed valid items

**Success Outcome:** Review findings have teeth. Quality improves because phases aren't left with "suggestions" that never get addressed.

### Problem Being Solved

**Pain Point:** Medium/Low issues are valid quality problems but get ignored because the pipeline treats them as optional. Phases are rarely revisited, so "fix later" effectively means "never."

**Alternative Approach:** Manual review follow-up, which gets skipped due to time pressure.

### Integration Points

**Upstream Dependencies:**
- `/code-review` and `/review-plan` skills produce review files with severity-graded issues

**Downstream Consumers:**
- All `/implement` invocations that trigger code review
- Delegation docs guide main agent behavior after reviews complete

**Data Flow:**
```
Code review completes
→ Review file has issues table with Critical/High/Medium/Low
→ /implement Step 8 reads review file
→ OLD: fixes only Critical
→ NEW: fixes all severities (hallucination check for Med/Low)
→ Re-run review
→ Repeat until clean
```

---

## Prerequisites & Clarifications

**Purpose:** Resolve ambiguities before implementation begins.

### Questions for User

1. **Hallucination Detection:** How should we distinguish valid Medium/Low items from hallucinated ones?
   - **Context:** Medium/Low items might reference non-existent patterns or contradict actual codebase
   - **Assumptions if unanswered:** Check if issue cites a reference file; if cited, validate claim against reference
   - **Impact:** If wrong, we fix hallucinated items or skip valid ones

2. **Purely Cosmetic Exemption:** What counts as "purely cosmetic with no functional impact"?
   - **Context:** Task description allows skipping Low items that are purely cosmetic
   - **Assumptions if unanswered:** Comment style, whitespace, ordering of unrelated declarations
   - **Impact:** If wrong, we fix trivia or skip meaningful style issues

3. **Auto-Fix Scope:** Should /review-plan auto-fix Medium items like it does Critical/High?
   - **Context:** Task says "extend to Medium" for review-plan auto-fix
   - **Assumptions if unanswered:** Yes, auto-fix Medium when correct pattern is clear from reference
   - **Impact:** If wrong, reviewer defers fixable items unnecessarily

### Validation Checklist

- [ ] All questions answered or assumptions explicitly approved
- [ ] User has reviewed phase deliverables and confirmed expectations
- [ ] Dependencies from prior phases are confirmed available (none for this phase)
- [ ] Environment variables and credentials are documented (none required)
- [ ] Any third-party services/APIs are registered and configured (none required)

---

## Requirements

### Functional

- Update `/implement` Step 8 to process all severity levels (Critical/High/Medium/Low)
- Update `/review-plan` Step 9 (Auto-Fix) to include Medium severity
- Update delegation docs for both `/review-plan` and `/code-review` to reflect new main agent responsibilities
- Add hallucination detection logic: skip items that reference non-existent files or contradict reference patterns
- Add cosmetic exemption logic: skip Low items that are purely stylistic with no functional impact

### Technical

- Modify `.claude/skills/implement/SKILL.md` Step 8
- Modify `.claude/skills/review-plan/SKILL.md` Step 9
- Modify `.claude/skills/review-plan/delegation.md` "After a Review Completes" section
- Modify `.claude/skills/code-review/delegation.md` "After a Review Completes" section
- Version bumps:
  - `/implement`: 1.1.0 → 1.2.0 (depends on Phase 01 bump to 1.1.0)
  - `/review-plan`: 1.0.0 → 1.1.0
  - `/code-review`: 1.1.0 → 1.2.0

---

## Decision Log

### Fix Medium/Low Unless Hallucinated (ADR-02-01)

**Date:** 2026-02-14
**Status:** Accepted

**Context:**
Review skills identify real issues but current pipeline discards Medium/Low items. User prefers quality now over speed.

**Decision:**
Fix all severity levels unless the finding is:
1. Hallucinated (references non-existent patterns/files, contradicts actual codebase)
2. Purely cosmetic with no functional impact (Low only)

**Consequences:**
- **Positive:** Higher code quality, review findings actionable
- **Negative:** Slightly longer review cycles, need hallucination detection
- **Neutral:** Aligns pipeline with review skill intent

**Alternatives Considered:**
1. **Fix only Critical/High:** Rejected — current state, causes quality debt
2. **Fix all including cosmetic:** Rejected — wastes time on trivia

---

## Implementation Steps

### Step 0: Test Definition (TDD)

**Purpose:** This phase modifies skill definition markdown files, which are not unit testable. Validation is manual integration testing.

**Manual Test Plan:**
1. Create test phase with Medium/Low review issues
2. Run `/implement` and verify all issues get fixed
3. Verify hallucination detection skips invalid items
4. Verify cosmetic exemption skips pure style issues

**No automated tests for this phase.**

---

### Step 1: Update /implement Step 8

**File:** `.claude/skills/implement/SKILL.md`

#### 1.1: Replace Step 8 Content

Current behavior:
```markdown
If No → FIX the Critical Issues first
```

New behavior:
```markdown
After the review completes:
1. Read the review file at $ARGUMENTS/reviews/code/phase-{NN}.md
2. Check the Verdict section:
  - If "Yes" with no issues → proceed to Step 9
  - If "No" → FIX ALL issues by severity:
    a. Critical: Fix immediately (security, crashes, data leakage)
    b. High: Fix immediately (pattern violations, missing auth)
    c. Medium: Fix now — these are real quality issues, not suggestions.
       Only skip if the finding is clearly a hallucination (references
       non-existent patterns or contradicts actual codebase).
    d. Low: Fix now unless clearly a hallucination or purely cosmetic
       with no functional impact.
  - Re-run /code-review after fixes
  - Repeat until verdict is "Yes"
```

Add hallucination check logic:
- If issue cites a reference file, verify claim by reading that file
- If issue contradicts patterns from Phase Step 6 reference read, it's hallucinated
- If issue references a file that doesn't exist, it's hallucinated

Add cosmetic exemption logic:
- Comment style changes with no semantic impact
- Whitespace or formatting (unless it breaks linting)
- Ordering of independent declarations

#### 1.2: Bump Version

- [ ] Change `version: 1.0.0` to `version: 1.2.0`
  - Note: Depends on Phase 01 completing first and bumping to 1.1.0
  - If Phase 01 is not yet complete, this phase will bump directly from 1.0.0 → 1.2.0

---

### Step 2: Update /review-plan Step 9 Auto-Fix

**File:** `.claude/skills/review-plan/SKILL.md`

#### 2.1: Extend Auto-Fix to Medium

Current: "Fix Critical and High issues directly"

New: "Fix Critical, High, and Medium issues directly"

Update Step 9 instructions:
```markdown
Fix Critical, High, and Medium issues directly in the phase file:

1. For each Critical/High/Medium issue:
   a. Read the reference file cited in the issue (if not already read)
   b. Locate the problem in the phase file
   c. Apply the fix using Edit (for targeted changes) or Write (for larger rewrites)

2. **Examples of fixes to make (never defer these):**
   - [existing list]
   - Medium severity: Pattern deviations where reference shows correct approach
   - Medium severity: Missing code blocks where review says "should have concrete examples"

3. **The ONLY reasons to defer to the main agent** (use sparingly):
   - [existing reasons]

[rest unchanged]
```

#### 2.2: Update Step 10 Summary

Change "Auto-fixed (count and brief list of what was fixed)" to include Medium count.

#### 2.3: Bump Version

- [ ] Change `version: 1.0.0` to `version: 1.1.0`

---

### Step 3: Update review-plan delegation.md

**File:** `.claude/skills/review-plan/delegation.md`

#### 3.1: Update "After a Review Completes" Section

Current text:
```markdown
2. **If there are Medium/Low improvement suggestions:**
   - Present the top suggestions to the user as concrete improvements worth doing now
   - Frame them as "the review found these — want me to fix them?" not just a passive list
   - Apply fixes the user approves
```

New text:
```markdown
2. **If there are Medium/Low improvement suggestions:**
   - Medium/Low findings are valid quality items, not optional suggestions
   - Fix all items that are grounded in actual codebase patterns (reference file cited)
   - Only skip items that are clearly hallucinated:
     * Reference non-existent files
     * Contradict actual codebase conventions
     * Flag patterns that the reference file itself uses
   - For Low items, also skip purely cosmetic changes (comment style, whitespace)
   - Present any deferred items to user with rationale
```

---

### Step 4: Update code-review Delegation Documentation

**File:** `.claude/skills/code-review/delegation.md`

#### 4.1: Update "After a Review Completes" Section

Apply the same changes as Step 3.1 to this file.

---

### Step 5: Manual Integration Test

#### 5.1: Create Test Phase with Multi-Severity Issues

- [ ] Create test phase with a known Medium issue (e.g., wrong directory name in a step) and a Low issue (e.g., inconsistent formatting)
- [ ] Run `/code-review` to generate review with mixed severity findings

#### 5.2: Test /implement Step 8 Behavior

- [ ] Run `/implement` on test phase
- [ ] Verify Critical, High, Medium, Low all get fixed
- [ ] Verify hallucinated Medium/Low items are skipped
- [ ] Verify purely cosmetic Low items are skipped

#### 5.3: Test /review-plan Auto-Fix

- [ ] Create test phase with Medium codebase compliance issues
- [ ] Run `/review-plan` on test phase
- [ ] Verify Medium issues are auto-fixed (not just flagged)

#### 5.4: Cleanup

- [ ] Delete test phases after validation
- [ ] Confirm no regressions

---

## Verifiable Acceptance Criteria

**Critical Path:**

- [ ] `/implement` Step 8 processes ALL severity levels (not just Critical)
- [ ] Hallucination detection skips invalid Medium/Low items
- [ ] Cosmetic exemption skips pure style Low items
- [ ] `/review-plan` Step 9 auto-fixes Medium issues (not just Critical/High)
- [ ] Delegation docs updated for both skills
- [ ] Version numbers bumped correctly

**Quality Gates:**

- [ ] Manual integration test passes for multi-severity review
- [ ] Existing phases with only Critical issues still work (no regression)
- [ ] Review cycle doesn't infinitely loop on hallucinated items

**Integration:**

- [ ] Review files produced by `/code-review` and `/review-plan` are parsable
- [ ] Main agent receives updated guidance from delegation docs
- [ ] User sees all valid findings addressed, not just critical ones

---

## Quality Assurance

### Test Plan

#### Manual Testing

- [ ] **Multi-Severity Fix:** Test phase with Critical/High/Medium/Low issues, verify all fixed
  - Expected: All non-hallucinated, non-cosmetic items addressed
  - Actual: [To be filled]

- [ ] **Hallucination Skip:** Test phase with Medium issue referencing non-existent file
  - Expected: Issue skipped with rationale logged
  - Actual: [To be filled]

- [ ] **Cosmetic Skip:** Test phase with Low issue about comment style
  - Expected: Issue skipped as purely cosmetic
  - Actual: [To be filled]

#### Automated Testing

Not applicable — skill definitions not unit testable.

#### Performance Testing

- [ ] **Review Cycle Time:** Measure time to fix all severities vs just Critical
  - Target: <2x increase (acceptable for quality improvement)
  - Actual: [To be measured]

### Review Checklist

- [ ] **Code Review Gate:**
  - [ ] Run `/code-review plans/260214-team-orchestration/phase-02-accept-all-review-items.md`
  - [ ] Files: `.claude/skills/implement/SKILL.md`, `.claude/skills/review-plan/SKILL.md`, delegation docs
  - [ ] Critical findings addressed
  - [ ] Phase approved

- [ ] **Pattern Compliance:**
  - [ ] Markdown formatting valid
  - [ ] Version bumps follow semver
  - [ ] Backward compatible with existing plans

---

## Dependencies

### Upstream (Required Before Starting)

- `/code-review` and `/review-plan` skills produce review files with severity tables

### Downstream (Will Use This Phase)

- All `/implement` invocations
- Main agents receiving delegation doc guidance

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
- [ ] Committed: `feat(workflow): accept all valid review items`

---

## Notes

### Technical Considerations

- Hallucination detection must be conservative — better to fix a questionable item than skip a valid one
- Cosmetic exemption applies only to Low severity — Medium cosmetic items might indicate deeper pattern issues
- Re-review loop must handle edge case where fixing Medium/Low items introduces new Critical issues

### Known Limitations

- Hallucination detection relies on reference file citation — if review doesn't cite references, can't auto-detect
- "Purely cosmetic" is subjective — may need user guidance in edge cases
- No tracking of which Medium/Low items were skipped and why (could add to review file in future)

### Future Enhancements

- Auto-categorize cosmetic vs functional Low items using AST analysis
- Track skipped items in review file with skip rationale
- Learn from user corrections (when user fixes an item marked as hallucinated)

---

**Previous:** [[phase-01-integrate-flow-audit-gate|Phase 01: Integrate Flow Audit Gate]]
**Next:** [[phase-03-stop-fix-test-failures|Phase 03: Stop-and-Fix on Test Failures]]
