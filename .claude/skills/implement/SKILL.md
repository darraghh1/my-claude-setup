---
name: implement
description: "Execute phases from a plan. Spawns ephemeral builder/validator agents per phase, handles gate checks, PASS/FAIL routing, and batch concurrency."
argument-hint: "[plan-folder]"
disable-model-invocation: true
metadata:
  version: 3.0.0
---

# Implement Plan

Implement phases from: **$ARGUMENTS/plan.md**

## Architecture

This skill is a **thin dispatcher**. It does NOT read references, extract patterns, or implement code. Builders handle all implementation work via the preloaded `builder-workflow` skill.

| Role | Responsibility |
|------|---------------|
| **Orchestrator (you)** | Find phases, gate checks, spawn/shutdown teammates, route PASS/FAIL |
| **Builder** | Phase implementation: read phase, find references, invoke skills, code, test, typecheck. Does NOT review its own code. |
| **Validator** | Independent review: runs `/code-review` (reference-grounded, with auto-fix), then typecheck + tests. Reports PASS/FAIL. |

**Builders and validators are ephemeral.** Each phase gets a fresh builder with a clean 200K context. When a builder completes, a fresh validator is spawned for that phase's review. After the review cycle completes (PASS or FAIL resolution), both are shut down. This prevents context contamination between phases, ensures skill instructions are never compacted away, and eliminates the single-validator bottleneck when multiple builders run in parallel.

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

**3. Check if audit exists:** Look for `$ARGUMENTS/reviews/planning/flow-audit.md`. This should already exist from `/create-plan` (Step 10).

**4. If missing:** STOP and tell the user to run `/audit-plan $ARGUMENTS` first. The orchestrator should not run the audit itself — it consumes too much context for a thin dispatcher.

**5. Gate logic:**

| Overall Assessment | Behavior |
|--------------------|----------|
| **"Major Restructuring Needed"** | **HARD BLOCK:** STOP. Report issues to user. |
| **"Significant Issues"** | **SOFT BLOCK:** WARN user. Ask whether to proceed or fix. |
| **"Minor Issues"** or **"Coherent"** | **PROCEED.** |

## Step 3: Find Unblocked Phases

**3a: Check for existing tasks (compact recovery):**

Run `TaskList` first. If tasks already exist from a previous session or before a context compact:
1. Read existing tasks with `TaskGet` for each task ID
2. If any task is `in_progress` — that's where you were interrupted. Resume from that phase's current state (check if a builder/validator is active)
3. Do NOT recreate the task list — resume with existing tasks

**3b: Read the Phase Table:**

Read the Phase Table in plan.md. Collect all phases with status "Pending".

If all phases are done:
1. Remove the plan's sidecar: `rm -f ~/.cache/claude-statusline/plans/PLAN_NAME.json`
2. Report completion to the user
3. Skip to Step 9 (cleanup)

**3c: Create orchestrator tasks (first run only):**

If no tasks exist yet, create one task per pending phase:

```
TaskCreate({
  subject: "Phase {NN} — {phase title}",
  description: "Gate check → build → validate → mark done\nPhase: $ARGUMENTS/phase-{NN}-{slug}.md",
  activeForm: "Implementing Phase {NN}"
})
```

Then set up dependencies with `TaskUpdate` using `addBlockedBy` to mirror each phase's `dependencies` frontmatter. For example, if Phase 03 depends on Phase 01:

```
TaskUpdate({ taskId: "3", addBlockedBy: ["1"] })
```

Tasks survive context compacts and give the user progress visibility. Without them, the orchestrator loses track of which phases are in flight after a compact.

**3d: Determine which pending phases are unblocked:**

For each pending phase, read its frontmatter `dependencies` field:
- `dependencies: []` (empty) → **unblocked** — no prerequisites
- `dependencies: [Phase 01, Phase 03]` → check the Phase Table for each listed dependency
  - All dependencies have status "Done" → **unblocked**
  - Any dependency is not "Done" → **blocked** — skip for now

Collect all unblocked phases. These are the candidates for gate-checking (Step 4) and builder spawning (Step 6).

**Update the statusline sidecar:**

After identifying unblocked phases, write a per-plan sidecar file using the lowest-numbered unblocked phase so the statusline displays current progress. Each plan gets its own file — multiple agents on different plans won't overwrite each other:

```bash
mkdir -p ~/.cache/claude-statusline/plans && echo '{"plan":"PLAN_NAME","phase":PHASE_NUM,"updated":'$(date +%s)'}' > ~/.cache/claude-statusline/plans/PLAN_NAME.json
```

Where:
- `PLAN_NAME` = the plan folder name (from `$ARGUMENTS`, e.g., `notes` from `plans/notes`)
- `PHASE_NUM` = the current phase number (from the phase's frontmatter `number` field or phase filename)

Example: If implementing phase 3 of the "notes" plan, run:
```bash
mkdir -p ~/.cache/claude-statusline/plans && echo '{"plan":"notes","phase":3,"updated":'$(date +%s)'}' > ~/.cache/claude-statusline/plans/notes.json
```

This makes the statusline display: `notes - Phase 3`

## Step 4: Gate Check Phases

Before spawning builders, gate-check each unblocked phase from Step 3. Mark each phase task as `in_progress` before gate-checking:

```
TaskUpdate({ taskId: "{phase-task-id}", status: "in_progress" })
```

Apply 4a and 4b to each phase individually.

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

**Validators are spawned on-demand per phase** (see Step 7). Unlike builders (spawned here in Step 6), validators are created when a builder reports completion. Each builder in a batch gets its own validator — max 2 validators active at a time, respecting the 4-agent total cap (see Concurrency Limits).

## Concurrency Limits

**Hard cap: 4 total active agents (builders + validators combined).** Exceeding this overwhelms the orchestrator's context with simultaneous completion messages and can crash the session.

| Constraint | Limit | Why |
|-----------|-------|-----|
| Builders per batch | Max 2 | Context pressure from parallel completions |
| Validators per batch | Max 2 (one per active builder) | Each builder gets one validator |
| **Total active agents** | **Max 4** | Orchestrator context budget |
| Batch overlap | **None** | Wait for current batch to fully complete before spawning next |

**Batch processing model:**
1. Spawn up to 2 builders for unblocked phases (a "batch")
2. As each builder completes, spawn its validator (max 2 validators active)
3. Wait for ALL builders AND validators in the current batch to finish
4. Only then loop back to Step 3 to find newly unblocked phases and spawn the next batch
5. Do NOT fill "open slots" mid-batch — the batch completes as a unit

## Step 6: Spawn Builders

Spawn a fresh builder for each unblocked phase that passed gate-checking. **Max 2 builders per batch.** If more than 2 phases are unblocked, pick the first 2 (lowest phase numbers) and queue the rest for the next batch.

**Before spawning, extract the `skill:` field from each phase's YAML frontmatter.** You already read the phase during gate-checking (Step 4) — use that value. If the frontmatter has no `skill:` field, use `none`.

```
// Spawn builders for unblocked phases (max 2 per batch):
Task({
  description: "Implement phase {NN}",
  subagent_type: "builder",
  model: "opus",
  team_name: "{plan-name}-impl",
  name: "builder-1",
  mode: "bypassPermissions",
  prompt: `Implement the phase at: $ARGUMENTS/phase-{NN}-{slug}.md
Plan folder: $ARGUMENTS
Skill: {skill-from-frontmatter}

Follow your preloaded builder-workflow skill. It teaches you how to:
1. Read the phase and extract requirements
2. Invoke the Skill above (if not "none") and find reference files
3. Create internal tasks (TaskCreate) for each step — prefix with [Step]. This is REQUIRED for context compact recovery
4. Implement with TDD (Step 0 first), marking tasks in_progress/completed as you go
5. Run tests and typecheck
6. Report completion to team-lead (do NOT run /code-review — the validator handles that independently)

IMPORTANT: Before using the Write tool on any existing file, you MUST Read it first or the write will silently fail.`
})

// Only if a second phase is unblocked:
Task({
  description: "Implement phase {MM}",
  subagent_type: "builder",
  ...same structure...,
  name: "builder-2",
  prompt: `Implement the phase at: $ARGUMENTS/phase-{MM}-{slug}.md
Skill: {skill-from-frontmatter}
...`
})
```

Each builder gets a fresh context, a unique name (`builder-1`, `builder-2`, etc.), and works independently. The `builder-workflow` skill is preloaded via the builder agent's `skills:` field. The `Skill:` line bridges the orchestrator's knowledge (phase frontmatter) to the builder's skill invocation logic — without it, the builder must discover the skill indirectly from the phase file.

If only one phase is unblocked, spawn a single builder — this is the common case for phases with sequential dependencies.

## Step 7: Wait and Route

Wait for builder completion messages (automatic delivery — do NOT poll). When multiple builders are active, process each completion as it arrives.

When a builder reports done:

1. **Spawn a fresh validator for this phase** (max 2 validators active, one per builder in the batch):

```
Task({
  description: "Validate phase {NN}",
  subagent_type: "validator",
  team_name: "{plan-name}-impl",
  name: "validator-{N}",
  mode: "bypassPermissions",
  prompt: `Validate phase {NN} on the {plan-name}-impl team. Follow the workflow defined in your agent instructions.

Phase file: $ARGUMENTS/phase-{NN}-{slug}.md
Plan folder: $ARGUMENTS

Run /code-review against the phase file, then verify with typecheck + tests. Report PASS/FAIL to team-lead via SendMessage.`
})
```

Each validator gets a unique name matching its builder (`validator-1` for `builder-1`, `validator-2` for `builder-2`, etc.).

2. **Continue processing other builder completions** as they arrive within this batch. If a second builder completes while the first validator is running, spawn the second validator immediately (staying within the 4-agent total cap).

3. **Wait for ALL validator verdicts in this batch before proceeding.** Do NOT spawn new builders while validators are still running. The batch completes as a unit: all builders done → all validators done → then Step 8 → then next batch.

## Step 8: Handle Verdict

**PASS:**
1. Update phase YAML frontmatter: `status: done`
2. Update Phase Table in plan.md: status → "Done"
3. Mark the phase task as completed: `TaskUpdate({ taskId: "{phase-task-id}", status: "completed" })`
4. Shutdown the builder and validator for this phase:
   - `SendMessage({ type: "shutdown_request", recipient: "builder-N" })`
   - `SendMessage({ type: "shutdown_request", recipient: "validator-N" })`
5. If other builders/validators in this batch are still active, continue waiting for their completions (Step 7)
6. **When the entire batch is complete** (all builders done, all validators done, all verdicts processed), loop back to Step 3 — newly completed phases may unblock additional pending phases. Do NOT spawn new builders mid-batch.

**FAIL:**
1. Shutdown the current builder AND validator (both contexts may be stale):
   - `SendMessage({ type: "shutdown_request", recipient: "builder-N" })`
   - `SendMessage({ type: "shutdown_request", recipient: "validator-N" })`
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

3. Wait for fix builder → spawn fresh validator → re-validate → repeat until PASS

## Step 9: Cleanup

When all phases are done OR an error breakout condition is met:

1. **Shutdown all active teammates** (builders and validators still running):

```
// For each active builder-N and validator-N:
SendMessage({ type: "shutdown_request", recipient: "builder-1" })
SendMessage({ type: "shutdown_request", recipient: "validator-1" })
// ... repeat for all active agents
```

2. **Delete team:** `TeamDelete()`

3. **Remove this plan's statusline sidecar:**

```bash
rm -f ~/.cache/claude-statusline/plans/PLAN_NAME.json
```

**Error breakout conditions** — STOP and shut down if:
- Validator FAIL repeats 3+ times on the same phase
- Tests can't be fixed (cascading failures)
- Phase has Critical blocking issues from plan review
- User intervention is clearly needed

Do not proceed to the next phase when blocked. Shut down and let the user decide.

---

## Resuming After Context Compact

If you notice context was compacted or you're unsure of current progress:

1. Run `TaskList` to see all tasks and their status
2. Find the `in_progress` task — that's the phase you were working on
3. Run `TaskGet {id}` on that task to read full details
4. Read plan.md to get the Phase Table for broader context
5. Check if team exists: read `~/.claude/teams/{plan-name}-impl/config.json`
   - If team exists, teammates are still active — coordinate via messages
   - If no team, re-create it (Step 5) — validators are spawned on-demand in Step 7
6. Continue from the in_progress phase — don't restart from Step 1

**Pattern for every work cycle:**
```
TaskList → find in_progress or first pending → TaskGet → continue work → TaskUpdate (completed) → next task
```

Tasks are the orchestrator's source of truth for progress — not memory, not plan.md alone.

---

## Reference Material

For anti-pattern prevention, context compact recovery, and troubleshooting, see [references/team-operations.md](references/team-operations.md).
