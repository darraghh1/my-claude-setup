---
name: implement
description: "Implement phases from a plan — one group per session with full 1M context. Reads the full plan for cross-phase awareness, then implements each phase in the assigned group directly (TDD, domain skills, code review, verification). Use when a reviewed plan is ready for implementation, e.g. '/implement plans/folder group-name'. Do NOT use without a reviewed plan — use /create-plan first."
argument-hint: "[plan-folder] [group-name | --audit]"
metadata:
  version: 6.0.0
---

# Implement Plan — Solo Session

Implement phases from: **$ARGUMENTS**

Parse arguments: first arg is the plan folder, second is the group name OR `--audit`.

## Architecture (1M Context — Solo Builder)

Each Claude Code session implements **one group** with its own 1M context. No subagents — you read everything, implement everything, review everything yourself. The user coordinates parallelism by opening multiple terminals.

```
Terminal 1: /implement plans/260314-auth auth-system
Terminal 2: /implement plans/260314-auth dashboard-ui
Terminal 3: /implement plans/260314-auth --audit    ← after all groups done
```

### Why Solo?

Subagents get 200K context, not 1M. By doing everything in one session, every phase implementation benefits from the full 1M window — you can hold the entire plan, all reference files, and accumulated implementation context simultaneously. The fat orchestrator doesn't delegate; it *is* the builder.

### Quality Gates (5 layers)

| Layer | When | What |
|-------|------|------|
| **PostToolUse hook** | Every Write/Edit | Regex checks for `any`, missing `server-only`, `console.log` |
| **TDD** | Before each phase | Write failing tests first, then implement |
| **Self-verification** | After each phase | `pnpm test` + `pnpm run typecheck` |
| **Self code-review** | After each phase | `/code-review` against the phase file |
| **Playwright smoke check** | After group completes | Navigate key pages, check for console errors |

---

## Standard Mode: `/implement [plan-folder] [group-name]`

### Step 1: Read and Understand the Full Plan

Read everything — you have 1M context.

1. Read `{plan-folder}/plan.md` — Phase Table, Group Summary, Architectural North Star, Security Requirements, Decision Log
2. Read **every phase file** in the plan (not just your group) — understand what other groups build and how your group connects
3. Build a mental model: what services exist from earlier groups, what schemas are in place, what your group's output will feed into later groups

**Why read phases outside your group?** You need to know the service signatures, table structures, and patterns established by other groups to write compatible code. At 1M, this costs almost nothing.

### Step 2: Gate Check

1. Check `{plan-folder}/reviews/planning/plan.md` exists — if not, tell the user to run `/review-plan` first
2. Read the review verdict — if "No", **STOP** and report Critical Issues
3. For plans with 3+ phases, check `{plan-folder}/reviews/planning/flow-audit.md`
   - If missing, tell user to run `/audit-plan` first
   - "Unusable" or "Major Restructuring" → **STOP**
   - "Significant Issues" → warn user, ask whether to proceed

### Step 3: Identify Your Group's Phases

From the Phase Table and Group Summary, extract all phases in your assigned group. Verify each phase has a review at `{plan-folder}/reviews/planning/phase-{NN}.md` with verdict "Ready: Yes".

**Skeleton check** for each phase:
```bash
echo '{"cwd":"."}' | uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_no_placeholders.py \
  --directory {plan-folder} --extension .md
```

### Step 4: Create Task List

Create tasks for progress tracking. Tasks survive context compacts and give the user visibility.

```
TaskCreate({
  subject: "Phase {NN}: {title}",
  description: "Implement phase at {plan-folder}/phase-{NN}-{slug}.md
Skill: {skill-from-frontmatter}
Key deliverables:
- {acceptance criterion 1}
- {acceptance criterion 2}
- {acceptance criterion 3}",
  activeForm: "Implementing Phase {NN}",
  metadata: { phase: "P{NN}", group: "{group-name}", skill: "{skill}" }
})
```

### Step 5: Implement Each Phase

For each phase in your group, sequentially:

**5a: Mark task in_progress**

**5b: Read the phase** — extract requirements, implementation steps, acceptance criteria

**5c: Find reference + invoke domain skill**

| Phase Focus | Skill | Reference Glob |
|-------------|-------|---------------|
| Database/migrations/RLS | `postgres-expert` | `supabase/migrations/*.sql` |
| Server actions | `server-action-builder` | `app/home/[account]/**/*server-actions*.ts` |
| Service layer | `service-builder` | `app/home/[account]/**/*service*.ts` |
| React forms | `react-form-builder` | `app/home/[account]/**/_components/*.tsx` |
| Components/pages | `vercel-react-best-practices` | `app/home/[account]/**/_components/*.tsx` |
| E2E tests | `playwright-e2e` | `e2e/tests/**/*.spec.ts` |

Glob the reference pattern → read ONE file → extract key patterns → invoke the domain skill.

**5d: Step 0 — TDD**

Write failing tests before implementation code. Both backend (Vitest) and frontend (happy-dom + @testing-library/react).

**5e: Implement**

Follow the phase's implementation steps exactly. Key patterns:
- Server actions: validate with Zod, verify auth before processing
- Services: `createXxxService(client)` factory wrapping private class, `import 'server-only'`
- After mutations: `revalidatePath('/home/[account]/...')`

**Scope boundary:** implement ONLY what's in the phase. Do NOT refactor adjacent code or add unspecified features.

**5f: Self-verification**

```bash
pnpm test
pnpm run typecheck
```

Both must pass. Fix any failures before proceeding.

**5g: Self code-review**

```
/code-review {plan-folder}/phase-{NN}-{slug}.md
```

Read the review output. Fix any Critical/High issues. Medium issues — use your judgment.

**5h: Commit**

```bash
git add -A && git commit -m "feat(phase-{NN}): {phase-title}"
```

**5i: Update plan status**

Edit `{plan-folder}/plan.md` — set the phase's status to "Done" in the Phase Table.
Edit the phase file frontmatter — set `status: done`.
Mark the task as completed (retry if TaskCompleted hook blocks first attempt).

**5j: Continue** to the next phase in the group.

### Step 6: Playwright Smoke Check

After all phases in the group are done, check the frontend still works:

1. Start dev server if needed: `pnpm dev &` then wait for startup
2. Navigate to key pages using Playwright MCP:
   ```
   mcp__playwright__browser_navigate → http://localhost:3000/home/[account]
   mcp__playwright__browser_console_messages → check for errors
   mcp__playwright__browser_snapshot → verify page rendered
   ```
3. Check pages relevant to this group's work
4. If console errors or broken pages → fix before reporting done

Skip if the group has no frontend phases.

### Step 7: Close Out Tasks + Summary

Mark ALL tasks completed (`TaskList` → verify all done). If the TaskCompleted hook blocks, retry immediately.

Report:
```
## Group "{group-name}" Complete

**Plan:** {plan-folder}
**Phases:** {count} Done

| Phase | Title | Skill | Status |
|-------|-------|-------|--------|
| P{NN} | {title} | {skill} | Done |

### Verification:
- Tests: passing
- Typecheck: clean
- Code review: {issues found/fixed}
- Playwright: {pass/skip}

### Files Changed:
{git diff --name-only output}
```

---

## Audit Mode: `/implement [plan-folder] --audit`

Run this **after all groups are complete** in a fresh session.

### Step 1: Read Everything

Read plan.md + ALL phase files + ALL code reviews at `{plan-folder}/reviews/code/`.

### Step 2: Cross-Phase Analysis

- **Shared files:** Find files modified by multiple phases — check for overwrites
- **Import chains:** Verify exports still match consumers
- **Deferred items:** Check code review "deferred" items against current code
- **Acceptance criteria:** Verify each phase's criteria are met

### Step 3: Verification

```bash
pnpm test
pnpm run typecheck
```

Correlate any failures to specific phases.

### Step 4: Write Audit Report

Write to `{plan-folder}/reviews/implementation/plan-audit.md` with:
- Acceptance criteria status (met/partial/not met per phase)
- Cross-phase regressions found
- Unresolved deferred items
- Verification results
- Findings by severity (Critical/High/Medium/Low)

### Step 5: Report to User

Present findings with severity ratings. User decides what to fix.

---

## Resuming After Context Compact

At 1M, compaction is rare but possible for very large plans.

1. `TaskList` → find `in_progress` or first `pending` task
2. `TaskGet` → read description for phase and group context
3. Read plan.md Phase Table → check which phases are already "Done"
4. Continue from where you left off

---

## Error Conditions

STOP and report to user if:
- Phase has Critical blocking issues from plan review
- Tests/typecheck fail 3+ times on same issue after fixes
- Code review finds Critical security issues you can't resolve
