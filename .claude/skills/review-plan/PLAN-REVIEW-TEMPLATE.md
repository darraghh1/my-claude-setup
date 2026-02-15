# Plan Review Template

This template defines the **exact output format** for `/review-plan` reviews. Agents MUST follow this structure precisely — do not add, remove, or rename sections.

Two variants exist:
- **Variant A:** Plan.md review (template compliance only)
- **Variant B:** Phase review (template compliance + codebase compliance + auto-fix)

---

## Variant A: Plan.md Review

Use this format when reviewing `plan.md`.

```markdown
# Plan Review: [Plan Title]

**Date:** YYYY-MM-DD
**File:** plan.md
**Verdict:** PASS | FAIL

---

## Template Compliance

| # | Section | Status | Notes |
|---|---------|--------|-------|
| 1 | YAML Frontmatter | pass/fail | [Required fields: title, description, status, priority, tags, created, updated] |
| 2 | Executive Summary | pass/fail | [Mission, Big Shift, Primary Deliverables] |
| 3 | Phasing Strategy | pass/fail | [Phase Constraints, Phase File Naming] |
| 4 | Phase Table | pass/fail | [Columns: Phase, Title, Focus, Status; links use correct pattern] |
| 5 | Architectural North Star | pass/fail | [Patterns with Core Principle + Enforcement] |
| 6 | Project Framework Alignment | pass/fail | [Component Usage Priority, Required Utilities table] |
| 7 | Security Requirements | pass/fail | [RLS, Input Validation, Authorization, Error Handling] |
| 8 | Implementation Standards | pass/fail | [Test Strategy, Documentation Standard, Code Quality Gates] |
| 9 | Success Metrics & Quality Gates | pass/fail | [Measurable metrics, quality gate checklist] |
| 10 | Global Decision Log | pass/fail | [ADRs with Status, Context, Decision, Consequences] |
| 11 | Resources & References | pass/fail | [Links to related docs, external references] |

**Template Score:** X/11 sections

---

## Critical Issues

[List issues that must be fixed before implementation, or "None" if clean]

1. [Issue description with specific location]
2. ...

---

## Verdict

**Template Score:** X/11
**Ready:** Yes | No — [reason if No]
```

---

## Variant B: Phase Review

Use this format when reviewing a phase file (`phase-NN-*.md`).

```markdown
# Phase Review: [Phase Title]

**Date:** YYYY-MM-DD
**File:** phase-NN-slug.md
**Verdict:** PASS | FAIL (X critical, Y high, Z medium)

---

## Part 1: Template Compliance

| # | Section | Status | Notes |
|---|---------|--------|-------|
| 1 | YAML Frontmatter | pass/fail | [title, description, skill, status, dependencies, tags, created, updated] |
| 2 | Overview | pass/fail | [Brief description + single-sentence Goal] |
| 3 | Context & Workflow | pass/fail | [4 layers, User Workflow, Problem Being Solved, Integration Points] |
| 4 | Prerequisites & Clarifications | pass/fail | [Questions with Context/Assumptions/Impact, Validation Checklist] |
| 5 | Requirements | pass/fail | [Functional + Technical separated] |
| 6 | Decision Log | pass/fail | [ADRs with Status, Context, Decision, Consequences, Alternatives] |
| 7 | Implementation Steps | pass/fail | [Numbered steps starting with Step 0] |
| 8 | Step 0: TDD | pass/fail | [Backend unit tests, frontend component tests, run-tests-should-fail] |
| 9 | Verifiable Acceptance Criteria | pass/fail | [Critical Path, Quality Gates, Integration checklists] |
| 10 | Quality Assurance | pass/fail | [Manual Testing, Automated Testing, Performance Testing, Review Checklist with /code-review] |
| 11 | Dependencies | pass/fail | [Upstream, Downstream, External Services] |
| 12 | Completion Gate | pass/fail | [Sign-off checklist] |

**Template Score:** X/12 sections

---

## Part 2: Codebase Compliance

**Reference files used:**
- `[path/to/reference-1.ts]` (for [pattern type])
- `[path/to/reference-2.ts]` (for [pattern type])

### Issues Found

| # | Severity | Category | Location | Issue | Expected (from codebase) |
|---|----------|----------|----------|-------|--------------------------|
| 1 | Critical/High/Medium/Low | [category] | Step N, line N | [what's wrong] | [what the reference shows] |
| 2 | ... | ... | ... | ... | ... |

**Codebase Score:** X issues (Y critical, Z high, W medium, V low)

If no issues found, write: "No codebase compliance issues found."

---

## Critical Issues Detail

[For each Critical and High issue, provide:]

### Issue #N: [Short title] (Severity)

**Problem:** [What's wrong]
**Why [Severity]:** [Impact if not fixed]
**Fix:** [Specific fix with code if applicable]

---

## Fixes Applied

[Critical/High issues auto-fixed in the phase file by the review agent. "N/A" if no auto-fix performed or no issues found.]

| # | Original Issue | Fix Applied |
|---|---------------|-------------|
| 1 | [issue from Part 2] | [what was changed in the phase file] |

[If any issues were deferred: "Issues marked 'Deferred to main agent' were not auto-fixed because [reason]."]

---

## Next Steps (Main Agent)

[Medium/Low issues framed as improvement opportunities. "None" if no medium/low issues.]

| # | Severity | Issue | Suggested Improvement |
|---|----------|-------|----------------------|
| 1 | Medium/Low | [issue] | [concrete improvement worth doing now] |

**Note to main agent:** These improvements are worth addressing now — phases are rarely revisited after completion. Discuss with user and implement what makes sense.

---

## Verdict

**Template Score:** X/12 sections
**Codebase Score:** X issues (Y critical, Z high, W medium, V low)
**Ready:** Yes | No

A phase is NOT ready if:
- Any template sections are missing (template score < 12/12)
- Any Critical or High codebase issues exist that were not auto-fixed

### Must Fix Before Implementation

[Numbered list of remaining unfixed issues, grouped by severity. Omit if Ready: Yes]

1. **[Critical]** [fix description]
2. **[High]** [fix description]
3. **[Medium]** [fix description]
```

---

## Rules for Using This Template

1. **Copy the structure exactly** — do not add sections like "Positive Observations", "Additional Observations", or "Implementation Verification"
2. **Use the exact table columns** shown — do not add or rename columns
3. **Severity levels** are: Critical, High, Medium, Low (in that order)
4. **Status values** in template compliance tables are: `pass` or `fail` (lowercase)
5. **Verdict values** are: `Yes` or `No` (not emoji checkmarks)
6. **"Ready: Yes"** means the Verdict section should not add caveats (the Next Steps section handles medium/low suggestions separately)
7. **Keep it concise** — the review should be parseable, not a narrative essay
8. **Fixes Applied section** — only populated when the agent auto-fixed issues. Use "N/A" when no auto-fix was performed or no issues found.
9. **Next Steps section** — always populated with medium/low improvement suggestions, or "None" if clean. Frame as concrete improvements worth doing now — not optional niceties.
