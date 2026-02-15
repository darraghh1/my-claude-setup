---
title: "Phase 05: Teams Instead of Sub-Agents"
description: "Complete rewrite of /implement Step 7 to use TeamCreate/SendMessage/teammates instead of Task tool fire-and-forget"
skill: "n/a"
status: done
dependencies: ["phase-01", "phase-02", "phase-03", "phase-04"]
tags: [phase, implementation, workflow-automation, team-coordination, architecture]
created: 2026-02-14
updated: 2026-02-14
---

# Phase 05: Teams Instead of Sub-Agents

**Context:** [[plan|Master Plan]] | **Dependencies:** P01, P02, P03, P04 | **Status:** Pending

---

## Overview

The current `/implement` uses Task tool with `run_in_background: true` to spawn ad-hoc sub-agents. Each is a one-shot fire-and-forget — no persistent identity, no message passing, no shared task list visibility. The orchestrator fills its context window with implementation details instead of staying lean.

**Goal:** Replace Step 7 with team-based orchestration. Orchestrator uses TeamCreate to spawn persistent named teammates (builders, validators). Communication via SendMessage. Orchestrator stays lean as team lead, not monolithic implementer.

---

## Context & Workflow

### How This Phase Fits Into the Project

- **UI Layer:** N/A
- **Server Layer:** N/A
- **Database Layer:** N/A
- **Integrations:** None — modifies `/implement` skill definition

### User Workflow

**Trigger:** `/implement` ready to implement phase with 3+ tasks

**Steps (NEW FLOW):**
1. Orchestrator creates team via TeamCreate
2. Spawns named teammates: `builder-1`, `builder-2`, `builder-3`, `validator`
3. Creates tasks via TaskCreate (self-contained descriptions)
4. Assigns tasks to teammates via TaskUpdate with `owner: "builder-1"`
5. Teammates mark completed via TaskUpdate
6. Orchestrator receives completion messages via SendMessage (automatic delivery)
7. Orchestrator checks TaskList for unblocked work, assigns next batch
8. After all tasks complete and code review passes, orchestrator sends shutdown_request to all
9. TeamDelete to clean up

**Success Outcome:** Orchestrator context stays under 20KB. Teammates reusable across tasks. Multi-phase mode possible (stretch goal).

### Problem Being Solved

**Pain Point:** Orchestrator context blowout from holding all implementation details. Fire-and-forget sub-agents can't be reused. No multi-phase capability.

**Alternative Approach:** Current sub-agent pattern with Task tool.

---

## Prerequisites & Clarifications

### Questions for User

1. **Multi-Phase Mode:** Should orchestrator loop after completing one phase to start the next?
   - **Context:** Task description mentions multi-phase as stretch goal (see ADR-05-02 for decision)
   - **Assumptions if unanswered:** Gate behind "if user requests multi-phase mode" — start conservatively
   - **Impact:** If enabled by default, might cause unexpected behavior

2. **Max Teammates:** Should there be a limit on team size?
   - **Context:** Task says max 3 builders + 1 validator = 4 max
   - **Assumptions if unanswered:** Hard limit of 3 builders, 1 validator
   - **Impact:** If wrong, too many teammates cause coordination overhead

3. **Direct Mode Threshold:** Keep 1-2 task threshold for direct mode?
   - **Context:** Task says direct mode for 1-2 tasks, team mode for 3+
   - **Assumptions if unanswered:** Yes, keep threshold
   - **Impact:** If wrong, overhead for tiny phases or complexity for simple ones

### Validation Checklist

- [ ] All questions answered or assumptions approved
- [ ] User reviewed deliverables
- [ ] Dependencies confirmed (P01-P04 complete)
- [ ] Environment variables documented (none)
- [ ] Third-party services configured (none)

---

## Requirements

### Functional

**Complete rewrite of `/implement` Step 7:**

- **Step 7a: Determine Execution Mode**
  - Count tasks from Step 5
  - 1-2 tasks → Direct mode (skip to 7e)
  - 3+ tasks → Team mode (continue to 7b)

- **Step 7b: Create Team**
  - TeamCreate with name `{plan-name}-impl`
  - Description: "Implementation team for {plan title}"

- **Step 7c: Spawn Named Teammates**
  - Spawn builders: `builder-1`, `builder-2`, `builder-3` (max 3)
  - Spawn validator: `validator` (max 1)
  - Each uses Task tool with `team_name` parameter to join team
  - Use detailed prompts from Phase 04

- **Step 7d: Task-Based Coordination**
  - Tasks already created in Step 5
  - Assign tasks via TaskUpdate with `owner: "builder-1"`
  - Max 3 builders active at once
  - Teammates mark complete via TaskUpdate
  - Orchestrator receives messages via SendMessage (automatic)
  - Check TaskList for unblocked work, assign next batch

- **Step 7e: Builder Lifecycle**
  - Builder receives initial prompt with skill/reference/patterns
  - Reads assigned task via TaskGet
  - Implements, marks complete
  - Sends completion message via SendMessage
  - Goes idle — orchestrator can assign next task or shutdown
  - Builders REUSABLE across tasks

- **Step 7f: Validator Lifecycle**
  - Single validator handles ALL validation
  - Orchestrator assigns validation tasks as builders complete
  - Validator checks code, runs typecheck/tests
  - Reports PASS/FAIL
  - If FAIL with Critical, validator creates fix task
  - Orchestrator assigns fix to idle builder

- **Step 7g: Shutdown**
  - After all tasks complete and code review passes:
    - Send shutdown_request to all teammates via SendMessage
    - Wait for shutdown acknowledgment
    - Call TeamDelete to clean up

- **Step 7h: Direct Mode (1-2 Tasks)**
  - Keep existing direct mode from current Step 7e
  - No team overhead for tiny phases

### Technical

- Modify `.claude/skills/implement/SKILL.md` Step 7 completely
- Remove references to `run_in_background: true` and TaskOutput polling
- Add TeamCreate, SendMessage, TeamDelete tool usage
- Context window target: orchestrator stays under 20KB
- Version bump: 1.4.0 → 2.0.0 (MAJOR — breaking changes to Step 7 architecture)

---

## Decision Log

### Major Version Bump Justified (ADR-05-01)

**Date:** 2026-02-14
**Status:** Accepted

**Context:**
Step 7 is being completely rewritten. Structure changes from sub-agent spawning to team coordination. API surface changes (Step 7 substeps completely different).

**Decision:**
Version 1.4.0 → 2.0.0. This is a breaking change even though existing plans should still work (backward compatibility maintained).

**Consequences:**
- **Positive:** Signals major architectural shift
- **Negative:** Might alarm users expecting semver stability
- **Neutral:** Justified by scope of changes

### Start Conservatively on Multi-Phase (ADR-05-02)

**Date:** 2026-02-14
**Status:** Accepted

**Context:**
With teams, orchestrator could potentially loop: finish phase N → update status → find phase N+1 → assign to existing teammates. But this is untested and might have edge cases.

**Decision:**
Document the multi-phase flow but gate it behind "if user requests multi-phase mode." Default to one phase per team instance.

**Consequences:**
- **Positive:** Safe rollout, no unexpected behavior
- **Negative:** Doesn't unlock full multi-phase potential immediately
- **Neutral:** Can enable in future phases after validation

---

## Implementation Steps

### Step 0: Test Definition (TDD)

**Purpose:** Define acceptance tests before writing implementation code.

This phase modifies skill documentation, not application code. Validation is via manual integration testing (see Step 4 for full test plan).

#### 0.1: Manual Integration Test Plan

**Test scenarios** (detailed in Step 4):
1. Create 5-task test phase
2. Verify team creation (TeamCreate called, directories exist)
3. Verify teammate spawning (3 builders + 1 validator with correct names)
4. Verify message passing (builders send, orchestrator receives automatically)
5. Verify task assignment and completion (TaskUpdate with owner)
6. Verify validator flow (PASS/FAIL verdicts, fix task creation)
7. Verify shutdown (shutdown_request → acknowledgment → TeamDelete)
8. Test direct mode (1-2 tasks, no team created)
9. Measure orchestrator context window size

#### 0.2: Success Criteria

- [ ] All 10 manual test scenarios in Step 4 pass
- [ ] Orchestrator context < 20KB after 5-task phase
- [ ] No regressions on existing plans

#### 0.3: Run Tests

Manual execution via `/implement` on test phase (Step 4).

---

### Step 1: Rewrite /implement Step 7 — Team Lead Orchestration

**File:** `.claude/skills/implement/SKILL.md`

**Actions:**
1. Read `.claude/skills/implement/SKILL.md` to understand current Step 7 structure
2. Use Edit tool to replace the entire Step 7 section (lines ~166-399) with new team-based orchestration content below

#### New Step 7 Structure:

```markdown
### Step 7: Implement (Team Lead Orchestration)

**You are the team lead. You deploy builder teammates to execute tasks, monitor their progress, and spawn validators to verify their work.** This enables parallel execution of independent tasks while keeping your context lean.

---

#### 7a: Determine Execution Mode

Count the pending tasks from Step 5:

| Task Count | Mode | Why |
|------------|------|-----|
| **1-2 tasks** | **Direct mode** — implement yourself (skip to 7h) | Team coordination overhead exceeds benefit for tiny phases |
| **3+ tasks** | **Team mode** — deploy builder teammates (continue to 7b) | Parallel execution saves time; builder context stays focused |

---

#### 7b: Create Team

For team mode (3+ tasks), create the implementation team:

```
TeamCreate({
  team_name: "{plan-name}-impl",
  description: "Implementation team for {plan title from plan.md}"
})
```

This creates:
- Team file at `~/.claude/teams/{plan-name}-impl/`
- Shared task list at `~/.claude/tasks/{plan-name}-impl/`

All teammates will join this team and share the task list.

---

#### 7c: Spawn Named Teammates

Spawn persistent builder and validator teammates.

**Builder teammates (max 3):**

For each builder (up to 3), spawn with unique name:

```
Task({
  description: "Builder teammate {N}",
  subagent_type: "builder",
  model: "opus",
  team_name: "{plan-name}-impl",  // NOTE: team_name and name are illustrative — verify Task tool API for actual team joining mechanism
  name: "builder-{N}",
  prompt: `[Use detailed 8-element template from Phase 04]

You are builder-{N} on the {plan-name}-impl team.

**Your workflow:**
1. Check TaskList to see available tasks
2. When orchestrator assigns you a task via TaskUpdate, read it with TaskGet
3. Invoke the skill: {skill-name from phase frontmatter}
4. Implement following patterns from reference: {reference-path}
5. Run tests if applicable
6. Mark complete via TaskUpdate
7. Send completion message to orchestrator via SendMessage
8. Go idle — orchestrator will assign next task or send shutdown

**Key Patterns (from reference {reference-path}):**
{3-5 bullet points extracted in Step 6}

**Scope:** Implement ONLY assigned task. No improvements, refactoring, or documentation.
**Tests:** Run after implementing. Fix all failures before marking complete.
**Write Tool:** Read existing files before using Write. Prefer Edit.
**Communication:** SendMessage to "team-lead" when complete or blocked.`
})
```

> **NOTE:** The `team_name` and `name` parameters shown above are illustrative. During implementation, verify the Task tool API documentation for the correct mechanism to join teammates to a team.

Spawn 1-3 builders depending on task count and parallelism potential.

**Validator teammate (single):**

```
Task({
  description: "Validator teammate",
  subagent_type: "validator",
  model: "sonnet",
  team_name: "{plan-name}-impl",
  name: "validator",
  prompt: `[Use detailed 5-element template from Phase 04]

You are the validator on the {plan-name}-impl team.

**Your workflow:**
1. Check TaskList to see validation tasks assigned to you
2. When orchestrator assigns validation, read task with TaskGet
3. Verify:
   - Files from task description were created/modified
   - Code matches patterns from reference: {reference-path}
   - No console.log, no \`any\` types, server-only imports present
   - Run typecheck: npm run typecheck
   - Run tests: npm test
4. Verdict:
   - PASS: Mark task completed via TaskUpdate with PASS note
   - FAIL: Create fix task via TaskCreate with specific issues
5. Send verdict to orchestrator via SendMessage
6. Go idle

**Checks:** File existence, pattern compliance, code quality, typecheck, tests.
**Verdict:** PASS or FAIL. If FAIL, create fix task with file:line references.
**Scope:** Validate ONLY assigned task. No improvements beyond acceptance criteria.`
})
```

---

#### 7d: Task Assignment and Coordination

Tasks were already created in Step 5. Now assign them to teammates.

**1. Initial batch (up to 3 builders):**

Identify first 3 unblocked tasks (no `blockedBy` dependencies). Assign each to a builder:

```
TaskUpdate({
  taskId: "X",
  owner: "builder-1"
})

TaskUpdate({
  taskId: "Y",
  owner: "builder-2"
})

TaskUpdate({
  taskId: "Z",
  owner: "builder-3"
})
```

**2. Wait for completion messages:**

Teammates send messages via SendMessage when complete. Messages are automatically delivered to you. Do NOT manually poll — wait for messages.

**3. After each builder completes:**

a. Check the task status via TaskList
b. If builder reported completion, assign validation to validator:

```
TaskCreate({
  subject: "Validate task X",
  description: "Validate that task X was implemented correctly. Check files, patterns, tests.",
  owner: "validator"
})
```

c. Check TaskList for newly unblocked tasks
d. Assign next unblocked task to the now-idle builder

**4. If validator reports FAIL:**

a. Validator creates fix task via TaskCreate
b. Assign fix task to an idle builder
c. Wait for fix completion
d. Re-validate the fixed task (assign new validation to validator)
e. Orchestrator assigns next validation task only after fix is PASSED (sequential validation queue)

**5. Repeat until all tasks complete:**

- Monitor TaskList for progress
- Assign new tasks as they unblock
- Deploy validators after each builder completion
- Handle FAIL verdicts with fix tasks

---

#### 7e: Builder Teammate Lifecycle

Each builder follows this flow:

1. **Receive initial prompt** with skill, reference, patterns from orchestrator
2. **Read assigned task** via TaskGet (orchestrator assigns via TaskUpdate)
3. **Implement** following skill guidance and reference patterns
4. **Run tests** if task involves code with tests
5. **Mark complete** via TaskUpdate when done
6. **Send message** to orchestrator: "Task X complete. Files: [list]. Tests: passing."
7. **Go idle** — orchestrator will assign next task or send shutdown

**Builders are REUSABLE.** After completing task X, the same builder can be assigned task Y. This is the key advantage over fire-and-forget sub-agents.

---

#### 7f: Validator Teammate Lifecycle

The validator follows this flow:

1. **Receive validation task** assigned by orchestrator after builder completes
2. **Read task** via TaskGet to see what was implemented
3. **Verify work:**
   - Files listed in task exist
   - Code matches reference patterns
   - No quality issues (console.log, any types, missing server-only)
   - Typecheck passes: `npm run typecheck`
   - Tests pass: `npm test`
4. **Report verdict:**
   - PASS: TaskUpdate with PASS note, send message to orchestrator
   - FAIL: TaskCreate with fix task listing specific issues, send message
5. **Go idle** — wait for next validation assignment

**Single validator handles ALL validations.** Unlike builders (which run in parallel), validator runs sequentially to provide consistent quality gate.

---

#### 7g: Shutdown and Cleanup

After all tasks complete and code review passes (Step 8):

1. **Send shutdown requests** to all teammates:

```
SendMessage({
  type: "shutdown_request",
  recipient: "builder-1",
  content: "All tasks complete. Shutting down the team. Thanks for your work!"
})

SendMessage({
  type: "shutdown_request",
  recipient: "builder-2",
  content: "All tasks complete. Shutting down the team. Thanks for your work!"
})

[repeat for all builders and validator]
```

2. **Wait for acknowledgment:**

Teammates respond with shutdown_response. They will exit after acknowledging.

3. **Delete team:**

```
TeamDelete()
```

This removes:
- Team directory at `~/.claude/teams/{plan-name}-impl/`
- Task directory at `~/.claude/tasks/{plan-name}-impl/`

---

#### 7h: Direct Mode (Small Phases)

For phases with 1-2 tasks, implement directly without deploying teammates.

**[Keep existing Step 7e content from current skill file]**

Load the skill, implement tasks yourself, mark complete.

---

#### 7i: Multi-Phase Mode (Stretch Goal — Optional)

**Skip this section unless user explicitly requests multi-phase mode.**

With teams, the orchestrator can potentially loop after finishing phase N:

1. Update phase N status to "Done"
2. Check for phase N+1 in plan.md
3. If exists and not blocked, continue with existing teammates:
   - Read phase N+1
   - Create tasks for phase N+1
   - Assign to existing builders (reuse team)
   - Repeat workflow

**CAUTION:** This is untested. Start with single-phase mode. Enable multi-phase after validation.

---

### Context Window Savings

**Current model (sub-agents):**
- Orchestrator context: ~60KB (holds all implementation details)
- Sub-agent context: ephemeral (discarded after TaskOutput read)

**New model (teams):**
- Orchestrator context: ~15KB (coordination messages only)
- Builder context: ~20KB each (task details + skill + reference)
- Validator context: ~10KB (checklist + file reads)

**Savings:** Orchestrator stays lean, can coordinate more work without context pressure.
```

---

### Step 2: Update Anti-Patterns Table

**File:** `.claude/skills/implement/SKILL.md`

**Location:** In the "Patterns That Prevent User-Reported Failures" section (after Step 9)

**Actions:**
1. Read `.claude/skills/implement/SKILL.md` to locate the anti-patterns table
2. Add these rows to the existing table:

| More than 3 concurrent teammates | Context pressure on team lead, loses track of task states |
| Skipping TeamDelete after completion | Leaves stale team directories, clutters filesystem |
| Polling TaskOutput instead of waiting for messages | Wastes context on output blobs, misses automatic message delivery |

---

### Step 3: Bump Version to 2.0.0

**File:** `.claude/skills/implement/SKILL.md`

- [ ] Change `version: 1.4.0` to `version: 2.0.0`
- [ ] MAJOR version because Step 7 is completely rewritten

---

### Step 4: Manual Integration Test

#### 4.1: Create 5-Task Test Phase

- [ ] Create test phase with 5 tasks (mix of parallel and sequential)
- [ ] Mark dependencies appropriately

#### 4.2: Test Team Creation

- [ ] Run `/implement plans/test-teams/`
- [ ] Verify TeamCreate called
- [ ] Verify team directory created at `~/.claude/teams/test-teams-impl/`
- [ ] Verify task directory created

#### 4.3: Test Teammate Spawning

- [ ] Verify 3 builders spawned with names `builder-1`, `builder-2`, `builder-3`
- [ ] Verify 1 validator spawned with name `validator`
- [ ] Verify all joined team (check team config file)

#### 4.4: Test Task Assignment

- [ ] Verify orchestrator assigns first 3 tasks to builders
- [ ] Verify TaskUpdate with `owner` field
- [ ] Verify tasks appear in shared task list

#### 4.5: Test Message Passing

- [ ] Verify builders send completion messages
- [ ] Verify orchestrator receives messages automatically
- [ ] Verify orchestrator doesn't poll TaskOutput

#### 4.6: Test Validator Flow

- [ ] Verify orchestrator assigns validation after builder completes
- [ ] Verify validator checks code
- [ ] Verify validator creates fix task on FAIL
- [ ] Verify fix task assigned to idle builder

#### 4.7: Test Shutdown

- [ ] After all tasks complete, verify shutdown_request sent to all
- [ ] Verify teammates acknowledge and exit
- [ ] Verify TeamDelete called
- [ ] Verify team/task directories removed

#### 4.8: Test Direct Mode (1-2 Tasks)

- [ ] Create 2-task test phase
- [ ] Verify direct mode triggered (no team created)
- [ ] Verify orchestrator implements tasks directly

#### 4.9: Measure Context Window

- [ ] Check orchestrator context size after 5-task phase using conversation turn size in logs or token counter
- [ ] Target: under 20KB
- [ ] Compare to current model (likely 60KB+)

#### 4.10: Cleanup

- [ ] Delete test phases
- [ ] Confirm no regressions on existing plans

---

## Verifiable Acceptance Criteria

**Critical Path:**

- [ ] Step 7 completely rewritten with substeps 7a-7i
- [ ] TeamCreate/SendMessage/TeamDelete used instead of Task/TaskOutput
- [ ] Max 3 builders + 1 validator spawned
- [ ] Message passing works (builders send, orchestrator receives)
- [ ] Teammates reusable across tasks
- [ ] Shutdown flow complete
- [ ] Direct mode preserved for 1-2 task phases
- [ ] Version bumped to 2.0.0

**Quality Gates:**

- [ ] Orchestrator context under 20KB after 5-task phase
- [ ] Manual integration test passes all 10 scenarios
- [ ] Existing plans still work (backward compatibility)
- [ ] No context window blowout

**Integration:**

- [ ] Teams tool integration works
- [ ] Task list shared across teammates
- [ ] Code review still works after team implementation

---

## Quality Assurance

### Review Checklist

- [ ] **Code Review Gate:**
  - [ ] Run `/code-review plans/260214-team-orchestration/phase-05-teams-orchestration.md`
  - [ ] Files: `.claude/skills/implement/SKILL.md`
  - [ ] Critical findings addressed
  - [ ] Phase approved

---

## Dependencies

### Upstream (Required Before Starting)

- Phase 01 (audit gate) complete
- Phase 02 (review items) complete
- Phase 03 (test failures) complete
- Phase 04 (prompt quality) complete — needed for detailed teammate prompts

### Downstream (Will Use This Phase)

- All `/implement` invocations with 3+ task phases

---

## Completion Gate

### Sign-off

- [ ] All acceptance criteria met
- [ ] Manual integration tests passing (all 10 scenarios)
- [ ] Context window savings verified (under 20KB)
- [ ] Code review passed
- [ ] Existing plans still work
- [ ] Phase marked DONE in plan.md
- [ ] Committed: `feat(workflow)!: teams instead of sub-agents (BREAKING)`

---

## Notes

### Technical Considerations

- Teammates go idle after each turn — normal, not an error
- Message delivery is automatic — don't poll
- Shared task list enables visibility across team
- Multi-phase mode documented but gated until validated

### Known Limitations

- No support for more than 3 builders (hard limit)
- No dynamic team sizing (fixed at spawn time)
- Multi-phase mode untested (stretch goal)
- Shutdown requires manual acknowledgment (no forced termination)

### Future Enhancements

- Dynamic team sizing based on task count
- Auto-resume if teammate crashes
- Multi-phase mode validation and enablement
- Team performance metrics (tasks/hour, PASS rate)

---

**Previous:** [[phase-04-improve-team-prompts|Phase 04: Improve Team Prompt Quality]]
**Next:** None — final phase
