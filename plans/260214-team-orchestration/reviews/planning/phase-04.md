# Phase Review: Improve Team Prompt Quality

**Date:** 2026-02-14
**File:** phase-04-improve-team-prompts.md
**Verdict:** PASS (all issues auto-fixed)

---

## Part 1: Template Compliance

| # | Section | Status | Notes |
|---|---------|--------|-------|
| 1 | YAML Frontmatter | pass | title, description, skill, status, dependencies, tags, created, updated all present |
| 2 | Overview | pass | Brief description + single-sentence Goal present |
| 3 | Context & Workflow | pass | 4 layers (N/A for most), User Workflow, Problem Being Solved present |
| 4 | Prerequisites & Clarifications | pass | Questions with Context/Assumptions/Impact, Validation Checklist present |
| 5 | Requirements | pass | Functional + Technical separated |
| 6 | Decision Log | pass | ADR-04-01 with Status, Context, Decision, Consequences, Alternatives |
| 7 | Implementation Steps | pass | Numbered steps starting with Step 0 |
| 8 | Step 0: TDD | pass | Manual test plan defined (appropriate for markdown modification) |
| 9 | Verifiable Acceptance Criteria | pass | Critical Path, Quality Gates, Integration checklists |
| 10 | Quality Assurance | pass | Review Checklist with /code-review reference |
| 11 | Dependencies | pass | Upstream, Downstream sections present |
| 12 | Completion Gate | pass | Sign-off checklist present |

**Template Score:** 12/12 sections

---

## Part 2: Codebase Compliance

**Reference files used:**
- `.claude/skills/implement/SKILL.md` (current state of target file)

### Issues Found

| # | Severity | Category | Location | Issue | Expected (from codebase) |
|---|----------|----------|----------|-------|--------------------------|
| 1 | Critical | Version Discrepancy | Step 4 | Says to change version from 1.3.0 to 1.4.0 | Current SKILL.md shows version: 1.0.0 (line 7) |
| 2 | Critical | Step Numbering | Step 3, Implementation | Proposes "Step 7a-2" between 7b and 7c | Should use sequential numbering (e.g., make it 7c and renumber subsequent steps) |
| 3 | High | Pattern Extraction Location | Step 1.2 | Says "add to Step 7b" but doesn't specify exact insertion point | Step 7b ends at line 192; new section should specify "append after identifying skill and reference" |
| 4 | Medium | Task Description Examples | Step 1, builder prompt template | Builder prompt includes example patterns but doesn't show how to populate from reference | Should reference "patterns extracted in Step 7b" explicitly |
| 5 | Medium | Validator Scope Boundary | Step 2.1, validator prompt template | Says "Do not suggest improvements beyond task acceptance criteria" but acceptance criteria location not specified | Should tell validator where to find acceptance criteria in phase file |

**Codebase Score:** 5 issues (2 critical, 1 high, 2 medium)

---

## Critical Issues Detail

### Issue #1: Version Number Mismatch (Critical)

**Problem:** Step 4 instructs to change version from 1.3.0 to 1.4.0, but the current SKILL.md shows version: 1.0.0

**Why Critical:** Following this instruction will create an invalid version jump (1.0.0 → 1.4.0) that doesn't follow semantic versioning. This could confuse version tracking and changelog generation.

**Fix:** Change Step 4 instruction to: `Change version: 1.0.0 to version: 1.1.0` (minor version bump for new builder/validator prompt features)

### Issue #2: Awkward Step Numbering (Critical)

**Problem:** Proposes inserting "Step 7a-2" between existing steps 7b and 7c

**Why Critical:** Creates confusing numbering scheme. Steps should be sequential (7a, 7b, 7c) or use sub-numbering consistently (7.1, 7.2, 7.3). "7a-2" is not a standard numbering pattern.

**Fix:** Either:
- Make it "Step 7c: Spawn Architect (Optional)" and renumber current 7c → 7d, current 7d → 7e, etc., OR
- Use sub-numbering: "Step 7.2.1: Spawn Architect (Optional)" under 7b as a conditional substep

### Issue #3: Missing Insertion Point Specification (High)

**Problem:** Step 1.2 says to add pattern extraction logic "In Step 7b" but doesn't specify exactly where within that section

**Why High:** Implementer must guess where to insert the new content. Step 7b spans multiple paragraphs; unclear if new content goes at beginning, middle, or end.

**Fix:** Specify exact insertion point: "After the reference Glob table (line 192), append a new section titled 'Extract Patterns for Builder Prompts'"

---

## Fixes Applied

| # | Original Issue | Fix Applied |
|---|---------------|-------------|
| 1 | Version 1.3.0 → 1.4.0 mismatch (Critical) | Changed Step 4 to: "Change `version: 1.0.0` to `version: 1.1.0`" |
| 2 | Step 7a-2 numbering (Critical) | Changed Step 3 to insert "Step 7c: Spawn Architect (Optional)" with note to renumber subsequent steps (7c→7d, 7d→7e, etc.) |
| 3 | Pattern extraction location (High) | Updated Step 1.2 to specify "append after line 192 (end of reference Glob table)" |
| 4 | Builder prompt lacks pattern reference (Medium) | Added "Patterns list populated from Step 7b pattern extraction" to Key Patterns section |
| 5 | Validator acceptance criteria location (Medium) | Added "(located in 'Verifiable Acceptance Criteria' section of phase file)" to validator Role section |

---

## Next Steps (Main Agent)

None (all medium improvements auto-fixed along with critical/high issues).

---

## Verdict

**Template Score:** 12/12 sections
**Codebase Score:** 5 issues (2 critical, 1 high, 2 medium) → all 5 auto-fixed
**Ready:** Yes

### Must Fix Before Implementation

None (all issues auto-fixed).
