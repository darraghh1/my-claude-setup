---
name: implement
description: "Implement phases from a plan. Acts as thin dispatcher: spawns builder agents per phase, validators to verify, handles PASS/FAIL routing. Builders are ephemeral — each phase gets a fresh builder with clean context. Use when ready to implement ('implement the next phase', 'start building', 'run the implementation'). Do NOT use for creating plans (use /create-plan) or reviewing plans (use /review-plan)."
argument-hint: "[plan-folder]"
disable-model-invocation: true
metadata:
  version: 3.0.0
  category: workflow-automation
  tags: [implementation, orchestration, team-dispatch]
---

# Implement Plan

Implement phases from: **$ARGUMENTS/plan.md**

## Architecture

This skill is a **thin dispatcher**. It does NOT read references, extract patterns, or implement code. Builders handle all implementation work via the preloaded `builder-workflow` skill.

| Role | Responsibility |
|------|---------------|
| **Orchestrator (you)** | Find phases, gate checks, spawn/shutdown teammates, route PASS/FAIL |
| **Builder** | Full phase implementation: read phase, find references, invoke skills, code, test, review |
| **Validator** | Verify completed work: files exist, patterns match, tests pass, typecheck passes |

**Builders are ephemeral.** Each phase gets a fresh builder with a clean 200K context. After a phase completes, the builder is shut down and a new one is spawned for the next phase. This prevents context contamination between phases and ensures the `builder-workflow` skill instructions are never compacted away.

---

## Step 1: Read and Review the Plan

1. Read the plan file at `$ARGUMENTS/plan.md`
2. Check if `$ARGUMENTS/reviews/planning/plan.md` exists
3. If no review exists, run `/review-plan $ARGUMENTS` first
4. **Read the review file** at `$ARGUMENTS/reviews/planning/plan.md`
5. **Check the Verdict section:**
   - If `Yes` → proceed to Step 2
   - If `No` → **STOP** and report the Critical Issues to the user

Proceeding with implementation when the plan review verdict is "No" means building on a plan with structural gaps — the user will discover these during implementation when they're more costly to fix.

## Step 2: Check Flow Audit

**1. Count phases** in the Phase Table.

**2. Skip for small plans:** If 1-2 phases, skip to Step 3.

**3. Check if audit exists:** Look for `$ARGUMENTS/reviews/planning/flow-audit.md`.

**4. Run if missing:** For 3+ phases with no audit: `/audit-plan $ARGUMENTS`

**5. Gate logic:**

| Overall Assessment | Behavior |
|--------------------|----------|
| **"Major Restructuring Needed"** | **HARD BLOCK:** STOP. Report issues to user. |
| **"Significant Issues"** | **SOFT BLOCK:** WARN user. Ask whether to proceed or fix. |
| **"Minor Issues"** or **"Coherent"** | **PROCEED.** |

## Step 3: Find Next Pending Phase

Read the Phase Table in plan.md. Find the first phase with status "Pending".

If all phases are done:
1. Remove `~/.cache/claude-statusline/active-plan.json` if it exists
2. Report completion to the user
3. Skip to Step 9 (cleanup)

**Update the statusline sidecar:**

```bash
mkdir -p ~/.cache/claude-statusline && echo '{"plan":"PLAN_NAME","phase":PHASE_NUM,"updated":'$(date +%s)'}' > ~/.cache/claude-statusline/active-plan.json
```

## Step 4: Gate Check the Phase

Before spawning a builder, verify the phase is ready.

**4a: Check for skeleton/placeholder content:**

```bash
echo '{"cwd":"."}' | uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_no_placeholders.py \
  --directory $ARGUMENTS --extension .md
```

If non-zero exit, the phase contains `[To be detailed]` or `TBD`. **STOP** — do not spawn a builder for a skeleton phase.

**4b: Verify the phase review:**

1. Check if `$ARGUMENTS/reviews/planning/phase-{NN}.md` exists
2. If no review exists, run `/review-plan $ARGUMENTS phase {NN}`
3. **Read the review Verdict:**
   - **Ready: Yes** → proceed to Step 5
   - **Ready: No** or Critical/High issues → **FIX the phase first**, re-run review, then proceed

## Step 5: Create Team (First Phase Only)

On the first phase, create the team. Reuse it across phases.

```
TeamCreate({
  team_name: "{plan-name}-impl",
  description: "Implementation team for {plan title}"
})
```

**Spawn the validator (once, reused across phases):**

```
Task({
  description: "Validator teammate",
  subagent_type: "validator",
  model: "sonnet",
  team_name: "{plan-name}-impl",
  name: "validator",
  mode: "bypassPermissions",
  prompt: `You are the validator on the {plan-name}-impl team. Your job is to verify work, not to implement.

**Your Workflow:**
1. When orchestrator sends you a validation assignment, read the phase file cited
2. Verify:
   a. Files listed in the phase's Implementation Steps were created/modified
   b. Code matches codebase patterns (find a reference file, compare)
   c. Code quality: no console.log, no any types, server files have import 'server-only'
   d. Run typecheck: pnpm run typecheck
   e. Run FULL test suite: pnpm test — report FAIL if any test fails
3. Report verdict via SendMessage to team-lead

**Verdict:**
- PASS: SendMessage with "PASS" and brief summary
- FAIL: SendMessage with "FAIL" and specific issues:
  - File:line references
  - Which pattern was violated
  - Exact fix needed

**Scope:** Validate ONLY what was assigned. Do not suggest improvements.

IMPORTANT: Before using the Write tool on any existing file, you MUST Read it first or the write will silently fail.`
})
```

## Step 6: Spawn Builder for Current Phase

Spawn a fresh builder. The `builder-workflow` skill is preloaded via the builder agent's `skills:` field — the builder already knows how to handle a full phase.

```
Task({
  description: "Implement phase {NN}",
  subagent_type: "builder",
  model: "opus",
  team_name: "{plan-name}-impl",
  name: "builder-1",
  mode: "bypassPermissions",
  prompt: `Implement the phase at: $ARGUMENTS/phase-{NN}-{slug}.md
Plan folder: $ARGUMENTS

Follow your preloaded builder-workflow skill. It teaches you how to:
1. Read the phase and extract requirements
2. Find reference files and invoke domain skills
3. Implement with TDD (Step 0 first)
4. Run tests and typecheck
5. Run /code-review and fix issues
6. Report completion to team-lead

IMPORTANT: Before using the Write tool on any existing file, you MUST Read it first or the write will silently fail.`
})
```

**For independent phases** (no dependency between them), spawn multiple builders in parallel:

```
Task({ ..., name: "builder-1", prompt: "Implement phase 3..." })
Task({ ..., name: "builder-2", prompt: "Implement phase 4..." })
```

Each builder gets a fresh context and works independently.

## Step 7: Wait and Route

Wait for the builder's completion message (automatic delivery — do NOT poll).

When builder reports done:

1. **Send validation assignment to validator:**

```
SendMessage({
  type: "message",
  recipient: "validator",
  content: "Validate phase {NN}. Phase file: $ARGUMENTS/phase-{NN}-{slug}.md. Check files, patterns, tests, typecheck.",
  summary: "Validate phase NN"
})
```

2. **Wait for validator verdict.**

## Step 8: Handle Verdict

**PASS:**
1. Update phase YAML frontmatter: `status: done`
2. Update Phase Table in plan.md: status → "Done"
3. Shutdown the builder: `SendMessage({ type: "shutdown_request", recipient: "builder-1" })`
4. Proceed to next phase (back to Step 3)

**FAIL:**
1. Shutdown the current builder (its context may be polluted with bad patterns)
2. Spawn a **fresh builder** with the validator's fix instructions:

```
Task({
  description: "Fix phase {NN} issues",
  subagent_type: "builder",
  model: "opus",
  team_name: "{plan-name}-impl",
  name: "builder-1",
  mode: "bypassPermissions",
  prompt: `Fix the issues found by the validator in phase $ARGUMENTS/phase-{NN}-{slug}.md:

[paste validator's FAIL details here]

After fixing:
1. Run pnpm test — all must pass
2. Run pnpm run typecheck — no errors
3. Report completion to team-lead`
})
```

3. Wait for fix builder → re-validate → repeat until PASS

## Step 9: Cleanup

When all phases are done OR an error breakout condition is met:

1. **Shutdown all teammates:**

```
SendMessage({ type: "shutdown_request", recipient: "builder-1" })
SendMessage({ type: "shutdown_request", recipient: "validator" })
```

2. **Delete team:** `TeamDelete()`

3. **Remove statusline sidecar:**

```bash
rm -f ~/.cache/claude-statusline/active-plan.json
```

**Error breakout conditions** — STOP and shut down if:
- Validator FAIL repeats 3+ times on the same phase
- Tests can't be fixed (cascading failures)
- Phase has Critical blocking issues from plan review
- User intervention is clearly needed

Do not proceed to the next phase when blocked. Shut down and let the user decide.

---

## Reference Material

For anti-pattern prevention, context compact recovery, and troubleshooting, see [references/team-operations.md](references/team-operations.md).
