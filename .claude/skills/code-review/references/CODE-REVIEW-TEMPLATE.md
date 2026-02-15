# Code Review Template

This template defines the **exact output format** for `/code-review` reviews. Agents MUST follow this structure precisely — do not add, remove, or rename sections.

---

```markdown
# Code Review: [Phase Title]

**Date:** YYYY-MM-DD
**Phase File:** [path to phase file]
**Files Reviewed:** [count]
**Reference Files:** [list of reference files read for pattern comparison]
**Verdict:** PASS | FAIL (X critical, Y high)

---

## Part 1: Completeness Check

| # | Step/Requirement | Status | Notes |
|---|------------------|--------|-------|
| 1 | Step 0: TDD | pass/fail | [details] |
| 2 | Step 1: [name] | pass/fail | [details] |
| 3 | Step 2: [name] | pass/fail | [details] |
| ... | ... | ... | ... |
| N | [Acceptance Criterion 1] | pass/fail | [details] |
| N+1 | [Acceptance Criterion 2] | pass/fail | [details] |

**Completeness:** X/Y items complete

---

## Part 2: Code Quality

### Critical Issues

[Security vulnerabilities, data leakage risks, breaking violations. "None" if clean.]

| # | File:Line | Issue | Expected (from reference) | Fix |
|---|-----------|-------|---------------------------|-----|
| 1 | path/file.ts:42 | [issue] | [what reference shows] | [specific fix] |

### High Priority Issues

[TypeScript any types, missing error handling, pattern violations. "None" if clean.]

| # | File:Line | Issue | Expected (from reference) | Fix |
|---|-----------|-------|---------------------------|-----|
| 1 | path/file.ts:42 | [issue] | [what reference shows] | [specific fix] |

### Medium Priority Issues

[Naming violations, missing loading states, useEffect usage. "None" if clean.]

| # | File:Line | Issue | Fix |
|---|-----------|-------|-----|
| 1 | path/file.ts:42 | [issue] | [fix] |

### Low Priority Issues

[Style, ordering, minor naming. "None" if clean.]

| # | File:Line | Issue | Fix |
|---|-----------|-------|-----|
| 1 | path/file.ts:42 | [issue] | [fix] |

---

## Part 3: Security Assessment

| Check | Status | Notes |
|-------|--------|-------|
| RLS policies (no USING(true)) | pass/fail | [details] |
| Account scoping (account_id) | pass/fail | [details] |
| Input validation | pass/fail | [details] |
| Error handling (no internal details exposed) | pass/fail | [details] |
| Authentication/Authorization | pass/fail | [details] |
| Credential handling (no hardcoded secrets) | pass/fail | [details] |

---

## Action Items

### Critical (Must Fix)

1. [File:line — specific fix]

### High Priority

1. [File:line — specific fix]

### Recommended

1. [File:line — specific fix]

[Write "None" for empty severity levels]

---

## Fixes Applied

[Critical/High issues auto-fixed in the source files by the review agent. "N/A" if no auto-fix performed or no issues found.]

| # | File:Line | Original Issue | Fix Applied |
|---|-----------|---------------|-------------|
| 1 | path/file.ts:42 | [issue] | [what was changed] |

[If any issues were deferred: "Issues marked 'Deferred to main agent' were not auto-fixed because [reason]."]

---

## Next Steps (Main Agent)

[Medium/Low issues framed as improvement opportunities. "None" if no medium/low issues.]

| # | Severity | File:Line | Issue | Suggested Improvement |
|---|----------|-----------|-------|----------------------|
| 1 | Medium/Low | path/file.ts:42 | [issue] | [concrete improvement worth doing now] |

**Note to main agent:** These improvements are worth addressing now — phases are rarely revisited after completion. Discuss with user and implement what makes sense.

---

## Verdict

**Completeness:** X/Y items
**Issues:** X critical, Y high, Z medium, W low
**Auto-fixed:** X critical, Y high
**Ready for Completion:** Yes | No — [reason if No]

A phase is NOT ready if:
- Critical or High issues exist that were not auto-fixed
- Key implementation steps are incomplete
```

---

## Rules for Using This Template

1. **Copy the structure exactly** — do not add sections like "Positive Observations", "Technical Excellence", "Next Phase Readiness", or narrative summaries
2. **Use the exact table columns** shown — do not add or rename columns
3. **Severity levels** are: Critical, High, Medium, Low (in that order)
4. **Status values** are: `pass` or `fail` (lowercase)
5. **Verdict values** are: `Yes` or `No` (not emoji checkmarks)
6. **"Ready: Yes"** means the Verdict section should not add caveats (the Next Steps section handles medium/low suggestions separately)
7. **Keep it concise** — actionable findings with file:line references, not narrative prose
8. **Cite references** — when flagging pattern issues, include the reference file:line that shows the correct pattern
9. **Every issue gets a Fix column** — don't flag problems without providing a specific fix
10. **Fixes Applied section** — only populated when the agent auto-fixed issues. Use "N/A" when no auto-fix was performed or no issues found.
11. **Next Steps section** — always populated with medium/low improvement suggestions, or "None" if clean. Frame as concrete improvements worth doing now — not optional niceties.
