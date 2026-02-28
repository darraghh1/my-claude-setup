---
name: create-plan
description: "Create phased implementation plans for new features or projects. Spawns an ephemeral planner agent for plan/phase creation, then validators for review. Interactive checkpoints let the user course-correct during planning."
argument-hint: "[feature-name] [description]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Task, Skill, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion, TeamCreate, TeamDelete, SendMessage
metadata:
  version: 2.0.0
---

# Create Complete Plan

Create a complete plan with phases for: **$ARGUMENTS**

## Current Plans

Existing plans in the repository (avoid naming conflicts):

!`ls plans/ 2>/dev/null || echo "(no plans directory yet)"`

## Architecture

This skill is a **thin dispatcher**. It does NOT read codebase references, extract patterns, or create phase files. The planner handles all planning work via the `planner-workflow` skill (invoked as its first action).

| Role | Responsibility |
|------|---------------|
| **Orchestrator (you)** | Clarify requirements with user, spawn/shutdown planner + validators, relay checkpoints, route PASS/FAIL |
| **Planner** | Plan creation: read templates, explore codebase, create plan.md + phase files, self-validate. Does NOT review its own plan. |
| **Validator** | Independent review: runs `/review-plan` against one file (plan.md or single phase). Reports template score + codebase compliance. |

**The planner is ephemeral.** It gets a fresh 200K context, creates the plan artifacts, and shuts down when done. This prevents context contamination and ensures skill instructions are never compacted away.

---

## Step 1: Clarify Requirements

The user has experienced 20-phase plans built on wrong assumptions — hours of work discarded because a 30-second question wasn't asked upfront. Clarification prevents this waste.

Read the task description above. If anything is ambiguous or underspecified, use `AskUserQuestion` to clarify before proceeding.

**Questions to ask if not clear from the description:**

1. **Problem:** What specific problem are we solving? What pain point does this address?
2. **Scope:** Is this a small feature, medium enhancement, or major system?
3. **Users:** Who uses this feature? (specific roles, account types)
4. **Integrations:** Does this connect to external services or APIs?
5. **Data:** What data does this create, read, update, or delete?
6. **UI:** Where does this appear in the app? New page, existing page, component?

If the description says "add voice commands" but doesn't specify which commands, ASK. If it says "improve performance" but doesn't specify what's slow, ASK. The user prefers a brief clarification dialogue over assumptions that lead to rework.

## Step 2: Create Team (First Run Only)

Create the team for this planning session. Reuse it if resuming.

```
TeamCreate({
  team_name: "{feature-name}-planning",
  description: "Planning team for {feature description}"
})
```

## Step 2.5: Codebase Exploration (Technical Discovery)

Before the planner estimates complexity, spawn an Explore agent to read the actual codebase areas relevant to the feature. This separates "what does the code actually look like" from "is this technically feasible" — preventing plans built on assumptions instead of code reality.

```
Task({
  description: "Explore codebase for {feature}",
  subagent_type: "Explore",
  model: "haiku",
  prompt: `Explore the codebase to produce a grounding summary for planning a new feature: {feature description}

Produce a concise summary covering:
1. **Affected Files/Modules** — which files and directories will likely need changes
2. **Existing Patterns** — naming conventions, file structure, import patterns in those areas
3. **Reusable Components** — services, components, utilities that already exist and can be leveraged
4. **Integration Points** — where the new feature connects to existing code (routes, services, database tables)
5. **Potential Conflicts** — areas of complexity, recent changes that might complicate implementation

Keep the summary under 2000 words. Focus on facts from the code, not assumptions.`
})
```

Pass the exploration summary to the planner in Step 3 as context. This grounds the plan in code reality.

## Step 3: Spawn Planner

Spawn a fresh planner with the requirements from Step 1 and the exploration summary from Step 2.5. The planner's agent config instructs it to invoke `planner-workflow` as its first action.

```
Task({
  description: "Create plan for {feature}",
  subagent_type: "planner",
  model: "opus",
  team_name: "{feature-name}-planning",
  name: "planner-1",
  mode: "bypassPermissions",
  prompt: `Create a plan for: {feature description}

Requirements:
{requirements from Step 1 — include all clarified answers}

Codebase Exploration Summary:
{summary from Step 2.5 — paste the full exploration output here}

Plan folder: plans/{YYMMDD}-{feature-name}

Your first action: invoke the planner-workflow skill via Skill({ skill: "planner-workflow" }). It teaches you how to:
1. Read plan and phase templates from $CLAUDE_PROJECT_DIR/.claude/skills/create-plan/references/
2. Explore codebase for reference patterns
3. Create plan.md scaffold
4. Report checkpoint 1 to team-lead (plan summary for user review)
5. Wait for feedback, then create all phase files
6. Report checkpoint 2 to team-lead (completion summary)

GROUPING (critical for implementation auditing):
- Connected phases that build the same feature/component MUST share a group: name
- Set group: in each phase's frontmatter (e.g., group: "auth-system")
- Include a Group Summary table in plan.md showing groups, their phases, and descriptions
- Order groups so dependencies flow top-to-bottom (group A before group B if B needs A)
- Single-phase groups are valid for standalone work
- Groups define audit boundaries — after all phases in a group complete, an auditor reviews them together

IMPORTANT: Before using Write on existing files, Read first or it silently fails. Prefer Edit for modifications.`
})
```

## Step 4: User Checkpoint — Plan Review

When the planner reports checkpoint 1 (plan.md summary with proposed phase breakdown):

1. **Show the user** the plan summary — executive summary, phase breakdown, architecture decisions
2. **Ask for approval/feedback** using `AskUserQuestion`:
   - Approve: proceed to phase creation
   - Changes needed: specify what to adjust

3. **Route the response:**
   - **If approved:** Message the planner to continue with phases
     ```
     SendMessage({
       type: "message",
       recipient: "planner-1",
       content: "Plan approved. Proceed with creating all phase files.",
       summary: "Plan approved — create phases"
     })
     ```
   - **If changes needed:** Message the planner with specific feedback
     ```
     SendMessage({
       type: "message",
       recipient: "planner-1",
       content: "User feedback:\n{specific changes requested}\n\nRevise plan.md and re-send checkpoint 1.",
       summary: "Revision requested on plan"
     })
     ```
   - Wait for the revised checkpoint, then repeat this step

## Step 5: User Checkpoint — Phases Complete

When the planner reports checkpoint 2 (all phases created and self-validated):

1. **Show the user** the full phase breakdown — titles, skills, dependencies, validation results
2. **Ask for approval/feedback:**
   - Approve: proceed to reviews
   - Changes needed: message planner with feedback, wait for revised checkpoint

3. **Route the response:**
   - **If approved:** Continue to Step 6 (spawn validators)
   - **If changes needed:** Message planner with feedback, loop until approved

## Step 6: Flow Audit (3+ Phases)

For plans with 3 or more phases, run a **structural flow audit** BEFORE per-phase reviews. This catches design-level issues (circular dependencies, wrong ordering, incoherent data flow) that would invalidate all review work if discovered later.

**Skip this step** for 1-2 phase plans (too small for flow issues).

```
/audit-plan plans/{YYMMDD}-{feature-name}
```

This invokes `/audit-plan` which writes a report to `{plan-folder}/reviews/planning/flow-audit.md`. The audit is intentionally lenient on polish (phases haven't been reviewed yet) but strict on structure.

**Gate logic:**

| Overall Assessment | Behaviour |
|--------------------|----------|
| **"Unusable"** | **HARD BLOCK:** Plan is fundamentally broken. Message planner with issues, wait for restructuring, re-audit |
| **"Major Restructuring Needed"** | **HARD BLOCK:** Message planner with issues, wait for fixes, re-audit |
| **"Significant Issues"** | **SOFT BLOCK:** Show user, ask whether to proceed or fix |
| **"Minor Issues"** or **"Coherent"** | **PROCEED** to Step 7 |

## Step 7: Spawn Validators

After flow audit passes (or is skipped for small plans), spawn review validators to check template compliance and codebase patterns.

Spawn **one validator per file** for thorough reviews. See [references/delegation-guide.md](references/delegation-guide.md) for prompt templates and batching rules.

### Validator Prompt — plan.md

```
Task({
  description: "Review plan.md",
  subagent_type: "general-purpose",
  team_name: "{feature-name}-planning",
  name: "reviewer-plan",
  mode: "bypassPermissions",
  run_in_background: true,
  prompt: `Your FIRST action must be to call the Skill tool with:
- skill: "review-plan"
- args: "plans/{folder-name}"

Do NOT do any other work until you have invoked that skill.

The skill will instruct you to read the PLAN-TEMPLATE.md reference and compare
every section in plan.md against it. Skipping this produces reviews that miss
template gaps, which the user then discovers during implementation.

This is a TEMPLATE COMPLIANCE review — check every section exists and write
pass/fail for each of the 11 required sections.

After the skill completes, report:
1. The review file location (reviews/planning/plan.md)
2. The verdict (Ready/Not Ready)
3. Template score (e.g., "11/11 sections" or "9/11 sections — 2 missing")`
})
```

### Validator Prompt — Phase File

```
Task({
  description: "Review phase {NN}",
  subagent_type: "general-purpose",
  team_name: "{feature-name}-planning",
  name: "reviewer-phase-{NN}",
  mode: "bypassPermissions",
  run_in_background: true,
  prompt: `Your FIRST action must be to call the Skill tool with:
- skill: "review-plan"
- args: "plans/{folder-name} phase {NN}"

Do NOT do any other work until you have invoked that skill.

The skill will instruct you to read the PHASE-TEMPLATE.md reference and compare
every section in the phase against it. Skipping template or codebase checks produces
phases that miss required sections or use wrong patterns — the user then discovers
these during implementation.

Specifically:
1. Compare every section against the template
2. Read a reference implementation from the codebase
3. Verify code blocks against actual codebase patterns
4. Write a review file with template score AND codebase compliance issues

This is a TEMPLATE + CODEBASE COMPLIANCE review. Check every section exists
AND verify code blocks match real codebase patterns.

After the skill completes, report:
1. The review file location (reviews/planning/phase-{NN}.md)
2. The verdict (Ready/Not Ready)
3. Template score (e.g., "12/12 sections")
4. Codebase score (e.g., "3 issues: 1 critical, 2 medium")`
})
```

### Batching Rules

Spawning more than 4 concurrent agents causes context window blowout — results flood back (~5KB each), earlier context gets compressed, and the orchestrator produces unreliable summaries.

1. **Maximum 4 validators at a time** — no exceptions
2. **`run_in_background: true`** on every Task tool call
3. **`TaskOutput` with `block: true`** to wait for completion
4. **Wait for ALL validators in a batch** to complete before spawning the next batch
5. **Summarise each batch** before moving to the next (prevents context bloat)

### Batching Example for 5 Phases (6 Reviews, 2 Batches)

```
Batch 1 (4 agents max):
- reviewer-plan:     args: "plans/{folder}"           → plan.md
- reviewer-phase-01: args: "plans/{folder} phase 01"  → phase-01
- reviewer-phase-02: args: "plans/{folder} phase 02"  → phase-02
- reviewer-phase-03: args: "plans/{folder} phase 03"  → phase-03
→ Wait for completion, then read results

Batch 2 (2 agents):
- reviewer-phase-04: args: "plans/{folder} phase 04"  → phase-04
- reviewer-phase-05: args: "plans/{folder} phase 05"  → phase-05
→ Wait for completion, then read results
```

## Step 8: Handle Review Verdicts

Process each validator's result:

**PASS (Ready: Yes):**
- Note the template score and any minor issues
- Continue to next batch or Step 9

**FAIL (Ready: No or Critical/High issues):**
1. Message the planner with the specific issues:
   ```
   SendMessage({
     type: "message",
     recipient: "planner-1",
     content: "Review feedback for {file}:\n{validator's findings}\n\nFix the issues and confirm when done.",
     summary: "Review feedback for {file}"
   })
   ```
2. Wait for the planner to confirm fixes
3. Re-spawn a validator for the fixed file
4. Repeat until PASS

**Show the user review results** after each batch — template scores, codebase compliance, any issues found and fixed.

## Step 9: Cleanup

When all reviews pass and audit clears (or is skipped for small plans):

1. **Shutdown the planner:**
   ```
   SendMessage({ type: "shutdown_request", recipient: "planner-1" })
   ```

2. **Shutdown all active validators** (any still running from review batches):
   ```
   SendMessage({ type: "shutdown_request", recipient: "reviewer-plan" })
   SendMessage({ type: "shutdown_request", recipient: "reviewer-phase-01" })
   // ... repeat for all active reviewers
   ```

3. **Delete team:** `TeamDelete()`

4. **Report summary to user:**

   1. **Folder location:** `plans/{YYMMDD}-{feature-name}/`
   2. **Files created:**
      - plan.md
      - phase-01-*.md through phase-NN-*.md
      - reviews/planning/ folder with review files
   3. **Review status:**
      - Plan.md: template score (X/11)
      - Each phase: template score (X/12) + codebase score (N issues by severity)
      - Flow audit (3+ phases): overall assessment + Critical/High issue count
   4. **Overall verdict:** Ready/Not Ready for implementation
   5. **Critical issues** (if any) that need addressing before implementation
   6. **Context hygiene:** "Consider running `/compact` before starting `/audit-plan` or `/review-plan` to free up context space."

---

## Concurrency Limits

| Constraint | Limit | Why |
|-----------|-------|-----|
| Planners | 1 | Only one plan is created at a time |
| Validators per batch | Max 4 | Context pressure from parallel results |
| **Total active agents** | **Max 5** | 1 planner + 4 validators (planner may still be active during reviews for fix routing) |
| Batch overlap | **None** | Wait for current batch to fully complete before spawning next |

---

## Resuming After Context Compact

If you notice context was compacted or you're unsure of current progress:

1. Run `TaskList` to see all tasks and their status
2. Find the `in_progress` task — that's where you were
3. Run `TaskGet {id}` on that task to read full details
4. Read plan.md to get the Phase Table for broader context
5. Check if team exists: read `~/.claude/teams/{feature-name}-planning/config.json`
   - If team exists, teammates are still active — coordinate via messages
   - If no team, re-create it (Step 2)
6. Continue from the in_progress step — don't restart from Step 1

**Pattern for every work cycle:**
```
TaskList → find in_progress or first pending → TaskGet → continue work → TaskUpdate (completed) → next task
```

Tasks are the orchestrator's source of truth for progress — not memory, not plan.md alone.

---

## Error Breakout Conditions

STOP and shut down if:
- Flow audit returns "Unusable" and planner cannot restructure
- Validator FAIL repeats 3+ times on the same file
- Planner cannot resolve Critical review issues
- User requests cancellation
- Context window approaching limit with no clear path forward

Do not continue when blocked. Shut down and let the user decide.

---

## Patterns That Prevent User-Reported Failures

The user experienced each of these failures. Understanding the harm helps you avoid them:

| Pattern to Avoid | Harm When Ignored |
|------------------|-------------------|
| Skipping requirements clarification | Wrong plan built on false premises, hours of wasted effort |
| Spawning planner without user checkpoint | User discovers wrong assumptions after all phases are written |
| Writing code blocks without reading codebase | Phases contain wrong patterns, caught late during implementation |
| Large multi-concern phases | Phases exceed context window, work gets lost mid-implementation |
| Self-reviewing the plan | Blind spots missed; `/review-plan` catches template AND codebase deviations |
| Vague delegation prompts | Validators misinterpret and skip skill invocation |
| Folder without date prefix | Folders become unsorted chronologically |
| Skipping TaskList check | Duplicates tasks if resuming after context compact |
| Too many concurrent validators | Context window blowout from result flooding |
| Running reviews before flow audit | Structural issues invalidate all review work — hours wasted on phases that need restructuring |

## Template Locations

- Plan: `references/PLAN-TEMPLATE.md`
- Phase: `references/PHASE-TEMPLATE.md`
- Delegation Guide: `references/delegation-guide.md`

These templates are auto-loaded into the planner's context via the `planner-workflow` skill. The orchestrator references them when spawning validators.

## Troubleshooting

### Planner Not Responding to Messages

**Symptom:** Sent a message to planner-1 but no response.

**Cause:** Planner may be idle (normal — waiting for your message to wake it), or context was compacted.

**Fix:** Idle is normal. Send the message and wait. If no response after the planner processes, check if the planner's context was compacted (the system will notify you). If so, spawn a fresh planner with the current state.

### Validators Skip Skill Invocation

**Symptom:** Review files are superficial, missing template or codebase checks.

**Cause:** Vague delegation prompt that doesn't make skill invocation imperative.

**Fix:** Use the exact prompt templates from Step 6. Include both the imperative command AND explanation of what the review entails.

### Context Window Overflow During Reviews

**Symptom:** Orchestrator loses track of review results or produces garbage summaries.

**Cause:** Too many validators spawned at once, or results not summarised between batches.

**Fix:** Follow batching rules in Step 6 — max 4 concurrent, summarise between batches. Use `run_in_background: true` and `TaskOutput` with `block: true`.
