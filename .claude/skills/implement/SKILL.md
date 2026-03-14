---
name: implement
description: "Execute phases from a plan. Fat orchestrator reads full plan, writes targeted builder briefings, runs Playwright smoke checks between groups, and spawns a single plan-level auditor. Use when a reviewed plan is ready for implementation, or when asked to 'implement the plan'. Do NOT use without a reviewed plan — use /create-plan first."
argument-hint: "[plan-folder]"
metadata:
  version: 5.0.0
---

# Implement Plan

Implement phases from: **$ARGUMENTS/plan.md**

## Architecture (1M Context — Fat Orchestrator)

With 1M context, the orchestrator is the **most informed agent in the system**. It reads every phase, understands the full architectural picture, and writes targeted builder briefings — not just file paths.

| Role | Responsibility |
|------|---------------|
| **Orchestrator (you)** | Read full plan, write targeted builder briefings, gate checks, spawn/shutdown agents, route verdicts, run Playwright smoke checks between groups, triage auditor findings |
| **Builder** | Group implementation: handle all phases in a group sequentially, accumulating context. Does NOT review its own code. |
| **Validator** | Independent review: runs `/code-review`, then typecheck + tests. Reports PASS/FAIL. |
| **Auditor** | Plan-level audit after ALL groups complete: cross-phase regressions, deferred items, plan drift. Read-only. |

**Builders run in isolated git worktrees.** One worktree per group — the builder commits after each phase, the orchestrator merges, and the validator runs on the merged result.

**One builder per group.** The builder stays alive across all phases in its group, accumulating context. This means the builder that implements the database schema already knows the table structure when it builds the service layer.

### Processing Model

```
Step 1: Read full plan + all phases (orchestrator builds complete picture)
Step 2: Gate check plan reviews
for each group (sequential):
  3. Spawn one builder for the group (all phases)
  4. For each phase in group:
     - Builder implements phase → commits to worktree branch
     - Orchestrator merges branch → spawns validator
     - PASS: update status, continue to next phase in group
     - FAIL: revert merge, send fix instructions to builder, re-validate
  5. Shutdown builder + validators for this group
  6. Playwright smoke check (navigate key pages, check for console errors)
  7. Continue to next group
After all groups:
  8. Spawn plan-level auditor
  9. Triage findings
  10. Cleanup
```

---

## Step 1: Read and Understand the Full Plan

**This is what makes you a fat orchestrator.** Read everything — you have 1M context.

1. Read `$ARGUMENTS/plan.md` — extract Phase Table, Group Summary, Architectural North Star, Security Requirements, Decision Log
2. Read **every phase file** listed in the Phase Table
3. For each phase, extract: title, skill, group, dependencies, key files, acceptance criteria, implementation steps
4. Build a mental model of the entire feature — what connects to what, which services feed which components

**Why this matters:** You'll use this understanding to write targeted builder briefings (Step 6) that include cross-phase context the builder would otherwise have to discover itself.

## Step 2: Gate Check Plan Reviews

1. Check `$ARGUMENTS/reviews/planning/plan.md` exists — if not, run `/review-plan $ARGUMENTS` first
2. Read the review verdict — if "No", **STOP** and report Critical Issues
3. For plans with 3+ phases, check `$ARGUMENTS/reviews/planning/flow-audit.md`
   - If missing, tell user to run `/audit-plan $ARGUMENTS` first
   - "Unusable" or "Major Restructuring" → **HARD BLOCK**
   - "Significant Issues" → **SOFT BLOCK** (ask user)
   - "Minor Issues" or "Coherent" → proceed

## Step 3: Parse Groups and Create Tasks

**3a: Check for existing tasks (compact recovery):**

Run `TaskList` first. If tasks exist from a previous session, find the `in_progress` task and resume.

**3b: Build group execution plan** from plan.md's Phase Table and Group Summary:

```
groups = [
  { name: "auth-system", phases: [P01, P02, P03] },
  { name: "dashboard-ui", phases: [P04, P05] },
]
```

**3c: Create orchestrator tasks** (first run only):

One task per group + one task for the plan audit:

```
TaskCreate({
  subject: "Group: {group-name} — {N} phases: P{NN}, P{MM}, ...",
  description: `Phases: {list with titles}
Skill(s): {skills from frontmatters}
Key deliverables: {top acceptance criteria across group phases}

Spawn builder → implement all phases → validate each → smoke check → done.`,
  activeForm: "Implementing group {group-name}",
  metadata: { created_by: "orchestrator", group: "{group-name}", role: "group" }
})
```

## Step 4: Gate Check Phases

Before spawning a builder for a group, gate-check each phase in the group:

1. **Skeleton check:**
   ```bash
   echo '{"cwd":"."}' | uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_no_placeholders.py \
     --directory $ARGUMENTS --extension .md
   ```

2. **Phase review check:** Verify `$ARGUMENTS/reviews/planning/phase-{NN}.md` exists and verdict is "Ready: Yes". If missing, run `/review-plan $ARGUMENTS phase {NN}`.

## Step 5: Create Team

```
TeamCreate({
  team_name: "{plan-name}-impl",
  description: "Implementation team for {plan title}"
})
```

## Concurrency Limits

| Constraint | Limit | Why |
|-----------|-------|-----|
| Builders per group | 1 | One builder handles all phases in a group |
| Parallel groups | Max 2 | Two groups can build simultaneously if independent |
| Validators per batch | Max 2 | One per active builder completing a phase |
| **Total active agents** | **Max 6** | Orchestrator has 1M context but agent results still consume tokens |
| Auditor | **Runs alone** | Needs undivided orchestrator attention for triage |

## Step 6: Spawn Builder for Group

**Before spawning, use your understanding of the full plan to write a targeted briefing.** This is the key advantage of the fat orchestrator — the builder starts with understanding, not discovery.

Extract the `skill:` field from each phase's YAML frontmatter.

```
Task({
  description: "Implement group {group-name}",
  subagent_type: "builder",
  model: "opus",
  team_name: "{plan-name}-impl",
  name: "builder-{group-name}",
  mode: "bypassPermissions",
  isolation: "worktree",
  prompt: `Implement all phases in the "{group-name}" group.

## Context from the Full Plan

{Write 5-15 lines of targeted context here. Include:
- What earlier groups already built (service signatures, table names, schemas)
- Key architectural decisions from plan.md's Decision Log relevant to this group
- Specific patterns this group should follow (from your reading of all phases)
- Integration points: what this group's output will feed into for later groups}

## Phases to Implement (in order)

### Phase {NN}: {title}
File: $ARGUMENTS/phase-{NN}-{slug}.md
Skill: {skill}
Key deliverables: {2-3 bullet points from acceptance criteria}

### Phase {MM}: {title}
File: $ARGUMENTS/phase-{MM}-{slug}.md
Skill: {skill}
Key deliverables: {2-3 bullet points from acceptance criteria}

[...list all phases in group...]

## Instructions

Your first action: invoke the builder-workflow skill via Skill({ skill: "builder-workflow" }).

Implement each phase sequentially. After completing each phase:
1. Run tests + typecheck
2. Commit: git add -A && git commit -m "feat(phase-{NN}): {title}"
3. Report to team-lead which phase completed, then continue to the next phase in the group

WORKTREE: You are in an isolated git worktree. Commit after EACH phase — the orchestrator merges and validates between phases. Uncommitted changes are lost.

IMPORTANT: Before using Write on any existing file, you MUST Read it first.`
})
```

## Step 7: Builder/Validator Cycle

When the builder reports a phase completion:

### 7a: Merge Worktree Branch

```bash
git merge --no-ff {worktree-branch} -m "merge: phase {NN} - {title}"
```

If conflicts: attempt auto-resolution for trivial conflicts. Non-trivial → **STOP** and report to user.

### 7b: Spawn Validator

```
Task({
  description: "Validate phase {NN}",
  subagent_type: "validator",
  model: "opus",
  team_name: "{plan-name}-impl",
  name: "validator-{N}",
  mode: "bypassPermissions",
  prompt: `Validate phase {NN}. Follow the workflow in your agent instructions.

Phase file: $ARGUMENTS/phase-{NN}-{slug}.md
Plan folder: $ARGUMENTS
Group: {group-name}

Run /code-review against the phase file, then verify with typecheck + tests. Report PASS/FAIL to team-lead.

IMPORTANT: Before using Write on any existing file, you MUST Read it first.`
})
```

### 7c: Handle Verdict

**PASS:**
1. Update phase frontmatter: `status: done`
2. Update Phase Table in plan.md
3. Mark phase complete in task metadata
4. Message builder to proceed to next phase in group (or shutdown if group is done)

**FAIL:**
1. Revert the merge: `git revert --no-edit HEAD`
2. Shutdown the validator (stale context)
3. Message the builder with the validator's specific fix instructions — the builder is still alive with full context of the group
4. Wait for builder to fix + recommit → merge → spawn fresh validator
5. After 3 FAIL cycles on same phase → **STOP** and report to user

### 7d: Group Complete

When all phases in a group pass validation, shutdown the builder and all validators for this group.

## Step 8: Playwright Smoke Check (Between Groups)

**Why:** The user has repeatedly caught issues where the frontend wireup didn't happen or pages stopped loading entirely — problems that unit tests and typecheck don't catch.

After each group completes (before starting the next group), run a quick smoke check:

1. **Start the dev server** (if not already running):
   ```bash
   pnpm dev &
   sleep 5  # Wait for server startup
   ```

2. **Navigate to key app pages** using Playwright MCP:
   ```
   mcp__playwright__browser_navigate → http://localhost:3000
   mcp__playwright__browser_console_messages → check for errors
   mcp__playwright__browser_snapshot → verify page rendered
   ```

3. **Check for:**
   - Console errors (especially import errors, undefined references, hydration mismatches)
   - Pages that fail to render (blank screen, error boundary)
   - 500 errors from server components

4. **If issues found:**
   - Log the specific errors
   - Spawn a fix builder (with worktree isolation) targeting the broken pages
   - Re-validate after fix
   - If unfixable → checkpoint with user before proceeding

5. **If clean:** Continue to next group

**Pages to check:** Derive from the group's phases — if the group built notifications, check `/home/[account]/notifications`. Always check the app root `/home/[account]` as a baseline.

**Skip this step** if the plan has no frontend phases (database-only, service-only plans).

## Step 9: Plan-Level Audit

After **ALL** groups complete, spawn a single auditor for the entire plan.

```
Task({
  description: "Audit full plan implementation",
  subagent_type: "auditor",
  model: "opus",
  team_name: "{plan-name}-impl",
  name: "plan-auditor",
  mode: "bypassPermissions",
  prompt: `Audit the complete implementation of this plan.

Plan folder: $ARGUMENTS
All phases:
{list every phase with number, title, file path, group}

Your first action: invoke the auditor-workflow skill via Skill({ skill: "auditor-workflow" }).

Review ALL phases together — cross-phase regressions, deferred items, plan drift, acceptance criteria, coding convention compliance.

Write your report to: $ARGUMENTS/reviews/implementation/plan-audit.md

IMPORTANT: You are READ-ONLY. Do not modify source code.`
})
```

## Step 10: Triage Auditor Findings

Read the full audit report at `$ARGUMENTS/reviews/implementation/plan-audit.md`.

| Finding Severity | Action |
|-----------------|--------|
| **No issues / Low only** | Log summary, continue to cleanup |
| **Medium** | Auto-spawn builder to fix + validator to verify |
| **High / Critical** | **Checkpoint with user** — present findings and ask for direction |

For Medium fixes: spawn a builder with worktree isolation, merge, validate. Max 3 attempts per finding, then escalate.

## Step 11: Cleanup

1. **Close out ALL tasks** — run `TaskList`, mark everything `completed`. If the TaskCompleted hook blocks first attempt, **retry immediately**.
2. Shutdown all active teammates
3. `TeamDelete()`
4. Stop dev server if started for smoke checks
5. Report summary:

```
## Implementation Complete

**Plan:** $ARGUMENTS
**Groups:** {count} completed
**Phases:** {count} Done

### Smoke Check Results:
| After Group | Pages Checked | Console Errors | Status |
|------------|--------------|----------------|--------|
| {name} | {pages} | {count} | {pass/fail} |

### Audit Results:
| Severity | Count |
|----------|-------|
| Critical | {N} |
| High | {N} |
| Medium | {N} |
| Low | {N} |

### Verification:
- Tests: {pass/fail}
- Typecheck: {pass/fail}
```

---

## Resuming After Context Compact

At 1M context, compaction is rare but possible for very large plans.

1. `TaskList` → find `in_progress` task
2. `TaskGet` → read metadata (which group, what role)
3. Read plan.md Phase Table → reconstruct group progress from phase statuses
4. Check if team exists and has active teammates
5. Resume from the in_progress point

---

## Error Breakout Conditions

STOP and shut down if:
- Validator FAIL repeats 3+ times on the same phase
- Auditor finding fix fails 3+ times
- Phase has Critical blocking issues from plan review
- User requests cancellation

For detailed anti-patterns, teammate lifecycles, and troubleshooting, see [references/team-operations.md](references/team-operations.md).
