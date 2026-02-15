---
name: builder-workflow
description: "Phase-level implementation workflow for builder agents. Handles reading phase files, finding references, invoking domain skills, implementing all steps, testing, and running code review. Preloaded into builder agents via skills: field — not user-invocable."
user-invocable: false
metadata:
  version: 1.0.0
  category: workflow-automation
  tags: [implementation, building, phase-execution]
---

# Builder Phase Workflow

You have been assigned a **full phase** to implement. Your spawn prompt contains the phase file path and plan folder. This skill teaches you how to handle the entire phase end-to-end.

## Why This Workflow Exists

The user experienced builders that guessed at patterns, skipped tests, and produced inconsistent code. Each step below prevents a specific failure:

| Step | Prevents |
|------|----------|
| Read phase completely | Missing requirements, user has to re-explain |
| Pre-flight test check | Cascading failures from broken previous phases |
| Find reference file | Guessing at patterns, code doesn't match codebase |
| Invoke domain skill | Missing project-specific conventions |
| TDD first (Step 0) | Untested code, bugs discovered in production |
| Code review at end | Blind spots from self-review |

## Step 1: Read the Phase

Read the phase file from your spawn prompt. Extract:

- **Prerequisites & Clarifications** — check for unanswered questions first
- **Requirements** (Functional + Technical)
- **Implementation Steps** (Step 0 through Step N)
- **Acceptance Criteria** (your success metrics)

If ANY prerequisite question is unanswered:
```
SendMessage({
  type: "message",
  recipient: "team-lead",
  content: "Phase has unanswered prerequisite questions. Cannot proceed.",
  summary: "Blocked: unanswered prerequisites"
})
```
Then STOP and wait for instructions.

## Step 2: Pre-Flight Test Check

**Skip for Phase 01** — no previous phases exist.

For Phase 02+:

```bash
pnpm test
```

- Exit code 0 → proceed to Step 3
- Exit code ≠ 0 → check if failures are from current phase's TDD (expected) or previous phases
  - Previous phase failures: fix them first, re-run to confirm green
  - Current phase TDD failures: expected, proceed

## Step 3: Identify Domain Skill and Reference

Check the phase frontmatter for a `skill` field, or determine from content:

| Phase Focus | Skill | Reference Glob |
|-------------|-------|---------------|
| Database schema, migrations, RLS | `postgres-expert` | `supabase/migrations/*.sql` |
| Server actions, services, API | `server-action-builder` | `app/home/[account]/**/*server-actions*.ts` |
| React forms with validation | `react-form-builder` | `app/home/[account]/**/_components/*.tsx` |
| E2E tests | `playwright-e2e` | `e2e/tests/**/*.spec.ts` |
| React components, pages | `vercel-react-best-practices` | `app/home/[account]/**/_components/*.tsx` |
| UI/UX | `web-design-guidelines` | `app/home/[account]/**/_components/*.tsx` |
| Service layer | `service-builder` | `app/home/[account]/**/*service*.ts` |

1. **Glob** the reference pattern → read ONE file
2. **Extract 3-5 key patterns**: function signatures, imports, naming, error handling, post-operation hooks
3. **Invoke the domain skill**: `Skill({ skill: "skill-name" })`

The reference file is your ground truth. Your code must structurally match it.

## Step 4: Create Internal Task List

Create tasks via `TaskCreate` for each implementation step. Tasks survive context compacts — if your context gets compacted mid-phase, `TaskList` → `TaskGet` tells you exactly where you were.

**Task descriptions must be self-contained:**
- File paths to create/modify
- Function signatures, key parameters
- Which services/actions to call
- Acceptance criteria for that step

Bad: `"Create the dropdown component"`
Good: `"Create app/home/[account]/roles/_components/change-role-dropdown.tsx. Props: { membershipId, accountSlug }. Fetch roles via listRolesAction, filter by hierarchy_level. Use @/components/ui Select, Badge."`

**Always start with Step 0: TDD.**

## Step 5: Implement

1. **Step 0 (TDD) first** — write failing tests before implementation code
2. **Remaining steps sequentially** — follow the phase document exactly
3. **After each step**: run `pnpm test`, fix failures before moving on
4. **Mark each task completed** via `TaskUpdate` as you finish it

**Scope boundary — implement ONLY what's in the phase:**
- Do NOT add improvements not specified in the phase
- Do NOT refactor adjacent code
- Do NOT create documentation files

**Key project patterns:**
- Server actions: validate with Zod, verify auth before processing
- Services: `createXxxService(client)` factory wrapping private class, `import 'server-only'`
- Imports: path aliases, ordering: React > third-party > internal > local
- After mutations: `revalidatePath('/home/[account]/...')`

**IMPORTANT:** Before using the Write tool on any existing file, you MUST Read it first or the write will silently fail. Prefer Edit for modifying existing files.

## Step 6: Final Verification

Before code review, run the full verification:

```bash
pnpm test
pnpm run typecheck
```

Both must pass. Fix any failures before proceeding.

## Step 7: Code Review

Invoke the code review skill against your phase:

```
/code-review [phase-file-path]
```

Read the review file. **Fix ALL Critical, High, and Medium issues:**

| Severity | Action |
|----------|--------|
| **Critical** | Fix immediately — security, crashes, data leakage |
| **High** | Fix immediately — pattern violations, missing auth |
| **Medium** | Fix now — real quality issues. Only skip if clearly hallucinated |
| **Low** | Fix unless clearly hallucinated OR purely cosmetic |

**Hallucination detection** — skip an item ONLY if:
- It references a file that doesn't exist (verify with Glob)
- It contradicts patterns from your Step 3 reference read
- It cites a reference but the claim doesn't match what the file contains

After fixing, re-run `/code-review` until verdict is "Yes".

## Step 8: Report Completion

Send completion message to the orchestrator:

```
SendMessage({
  type: "message",
  recipient: "team-lead",
  content: "Phase [NN] complete.\n\nFiles created/modified:\n- [list]\n\nTests: passing\nTypecheck: passing\nCode review: PASS\n\nAcceptance criteria met:\n- [list key criteria]",
  summary: "Phase NN complete — all checks pass"
})
```

Then go idle. The orchestrator will either assign the next phase or send a shutdown request.

## Resuming After Context Compact

If your context was compacted mid-phase:

1. `TaskList` → find the `in_progress` or first `pending` task
2. `TaskGet` on that task → read the self-contained description
3. Continue from that task — don't restart the phase
4. The task list is your source of truth, not your memory

## Troubleshooting

### Tests fail but code looks correct

**Cause:** Reference patterns may have changed since the phase was written.
**Fix:** Re-read the reference file (Step 3). If the phase's code blocks differ from the current reference, follow the reference — it's the ground truth.

### Domain skill not found

**Cause:** Skill name in phase frontmatter doesn't match available skills.
**Fix:** Check the table in Step 3 for the correct skill name. If the phase focus doesn't match any skill, skip skill invocation and rely on the reference file.

### Code review keeps failing on the same issue

**Cause:** The fix doesn't match what the reference shows.
**Fix:** Re-read the reference file cited in the review finding. Compare your code line-by-line against the reference pattern.
