---
title: "Phase 04: Improve Team Prompt Quality"
description: "Upgrade builder/validator/architect prompt templates with detailed 7-8 element structure"
skill: "n/a"
status: done
dependencies: []
tags: [phase, implementation, workflow-automation, prompt-engineering]
created: 2026-02-14
updated: 2026-02-14
---

# Phase 04: Improve Team Prompt Quality

**Context:** [[plan|Master Plan]] | **Dependencies:** None | **Status:** Pending

---

## Overview

Current builder/validator prompts are minimal templates. Builders guess at patterns, validators miss issues. Upgrade prompts to detailed 7-8 element templates that include task context, skill invocation, reference files, pattern summaries, scope boundaries, test requirements, and communication instructions.

**Goal:** Builder and validator prompts match the quality of `/improve-prompt` output — self-contained, pattern-grounded, with clear success criteria.

---

## Context & Workflow

### How This Phase Fits Into the Project

- **UI Layer:** N/A
- **Server Layer:** N/A
- **Database Layer:** N/A
- **Integrations:** None — modifies `/implement` skill definition

### User Workflow

**Trigger:** `/implement` deploys builder or validator teammate (current flow, improved prompts)

**Steps:**
1. Orchestrator crafts detailed prompt using new template
2. Prompt includes: task context, skill to invoke, reference file path, 3-5 key patterns, scope boundary, test requirement, write-tool warning, communication instructions
3. Builder/validator receives prompt, has all context needed to succeed
4. Work quality improves, rework decreases

**Success Outcome:** Builders produce code matching codebase patterns on first attempt. Validators catch all pattern deviations. Less back-and-forth, fewer fixes needed.

### Problem Being Solved

**Pain Point:** Minimal prompts cause builders to guess at patterns and validators to miss issues. This creates rework loops that waste time and context window.

**Alternative Approach:** Current minimal prompts like "implement task X, use skill Y" without pattern guidance.

---

## Prerequisites & Clarifications

### Questions for User

1. **Architect Teammate:** Should orchestrator spawn an architect for complex phases?
   - **Context:** Task description suggests optional architect for High-risk phases or postgres-expert phases
   - **Assumptions if unanswered:** Optional — only spawn for phases marked High in flow audit or skill: postgres-expert
   - **Impact:** If wrong, over-use architect (slow) or under-use (miss architecture guidance)

2. **Pattern Summary Source:** Should orchestrator extract patterns from reference or use pre-defined list?
   - **Context:** Need 3-5 bullet points of key patterns for builder prompts
   - **Assumptions if unanswered:** Extract from reference file read in Step 6
   - **Impact:** If wrong, patterns might not match actual codebase

### Validation Checklist

- [ ] All questions answered or assumptions approved
- [ ] User reviewed deliverables
- [ ] Dependencies confirmed (none)
- [ ] Environment variables documented (none)
- [ ] Third-party services configured (none)

---

## Requirements

### Functional

Upgrade builder prompt template in `/implement` Step 7c to include 8 elements:
1. Task context (ID + full description)
2. Skill invocation (exact skill name from phase frontmatter)
3. Reference file (exact path from Step 6)
4. Pattern summary (3-5 bullets extracted from reference)
5. Scope boundary ("implement ONLY this task, no improvements")
6. Test requirement ("run tests after implementing, fix before marking complete")
7. Write-tool warning (existing "Read before Write" instruction)
8. Communication ("mark complete via TaskUpdate, message orchestrator if blocked")

Upgrade validator prompt template in `/implement` Step 7d to include 5 elements:
1. Role ("quality gate, verify work not implement")
2. Scope ("ONE task at a time, address ONLY your assigned task")
3. Checks (file existence, pattern compliance vs reference, typecheck, test run)
4. Verdict (PASS or FAIL with specific issues)
5. No scope creep ("no improvements beyond task acceptance criteria")

Add optional architect teammate section:
- Spawn architect for High-risk phases (from flow audit) or skill: postgres-expert
- Architect analyzes requirements, suggests approach
- Orchestrator incorporates approach into builder prompts

### Technical

- Modify `.claude/skills/implement/SKILL.md` Step 7b (teammate spawning section)
- Builder prompt template expanded from 3 lines to ~15 lines
- Validator prompt template expanded from 3 lines to ~10 lines
- Architect section added as optional Step 7a-2
- Version bump: 1.3.0 → 1.4.0

---

## Decision Log

### Architect Teammate: Optional, Not Default (ADR-04-01)

**Date:** 2026-02-14
**Status:** Accepted

**Context:**
Spawning architect for every phase adds overhead. Most phases don't need architecture review — only complex/risky ones benefit.

**Decision:**
Make architect optional. Only spawn for:
- Phases marked "High" risk in flow audit report
- Phases with `skill: postgres-expert` (schema design benefits from architecture review)

**Consequences:**
- **Positive:** No overhead for simple phases
- **Negative:** Orchestrator must check conditions before spawning
- **Neutral:** Matches task description specification

**Alternatives Considered:**
1. **Always spawn architect:** Rejected — overhead for simple phases
2. **Never spawn architect:** Rejected — misses value for complex phases

---

## Implementation Steps

### Step 0: Test Definition (TDD)

This phase modifies skill definition markdown. Validation is manual integration testing.

**Manual Test Plan:**
1. Create test phase with 3+ builder tasks
2. Run `/implement`, observe builder prompts
3. Verify 8 elements present in builder prompts
4. Verify 5 elements present in validator prompts
5. Verify builders produce correct patterns on first attempt

**No automated tests.**

---

### Step 1: Upgrade Builder Prompt Template

**File:** `.claude/skills/implement/SKILL.md`

#### 1.1: Replace Builder Prompt in Step 7c

Current template (minimal):
```markdown
You are a builder agent. Read and execute the task below.
Task ID: [taskId]
Skill: [skill-name]
Reference: [reference-path]
```

New template (detailed):
```markdown
You are a builder agent assigned to implement a single task from the current phase.

**1. Task Context**
- Task ID: [taskId] — use TaskGet to read full details
- Task subject: [subject from TaskCreate]
- Full description: [self-contained description from Step 5]

**2. Skill to Invoke**
- Skill: [skill-name] from phase frontmatter `skill:` field
- Invoke this skill FIRST before writing any code
- The skill provides project-specific patterns and validation

**3. Reference File**
- Path: [reference-file-path from Step 6]
- This is your ground truth for code patterns
- Read it before implementing to understand conventions

**4. Key Patterns (from Reference)**
Patterns list populated from Step 7b pattern extraction (3-5 bullet points):
- [Pattern 1, e.g., "Server actions use `enhanceAction` wrapper"]
- [Pattern 2, e.g., "Services use private class + factory function"]
- [Pattern 3, e.g., "Imports: `import 'server-only'` at top"]
- [Pattern 4, e.g., "After mutations: `revalidatePath('/home/[account]/...')`"]
- [Pattern 5, e.g., "File naming: `server-actions.ts`, exports suffixed with `Action`"]

**5. Scope Boundary**
Implement ONLY this task. Do not:
- Add improvements not specified in task description
- Refactor adjacent code
- Create documentation files
- Modify unrelated features

**6. Test Requirement**
If this task has tests:
- Run them after implementation: `npm test`
- If tests fail (including tests from previous phases), fix before marking complete
- Do not leave broken tests for later

**7. Write Tool Warning**
IMPORTANT: Before using Write tool on any existing file, you MUST Read it first or the write will silently fail. Prefer Edit for modifying existing files.

**8. Communication**
- When done: mark task completed via TaskUpdate
- If blocked: send message to orchestrator explaining blocker using SendMessage
- Do not proceed if dependencies are missing
```

#### 1.2: Add Pattern Extraction Logic

In Step 7b (Identify Skill and Reference), append after the reference Glob table (after line 192):

```markdown
**After reading the reference file:**

Extract 3-5 key patterns to include in builder prompts. Look for:
- Function signatures (e.g., Server Action auth pattern)
- Import conventions (e.g., `import 'server-only'`, path aliases)
- Naming patterns (e.g., file names, export suffixes)
- Error handling (e.g., try/catch structure, error responses)
- Post-operation hooks (e.g., `revalidatePath` after mutations)

These patterns will be inserted into builder prompts in Step 7c.
```

---

### Step 2: Upgrade Validator Prompt Template

**File:** `.claude/skills/implement/SKILL.md`

#### 2.1: Replace Validator Prompt in Step 7d

Current template (minimal):
```markdown
Validate task [taskId]. Use TaskGet to read details.

Key checks: files created, patterns followed, no console.log, typecheck, tests.
```

New template (detailed):
```markdown
You are the quality gate for this implementation. Your job is to verify work, not to implement.

**1. Role**
- Verify that the builder's work meets acceptance criteria (located in "Verifiable Acceptance Criteria" section of phase file)
- Check code quality, pattern compliance, and test results
- Report PASS or FAIL with specific findings

**2. Scope**
- You are assigned ONE task at a time by the orchestrator
- Address ONLY your assigned task — do not review other code or tasks
- Task ID: [taskId] — use TaskGet to read full details

**3. Checks to Perform**
a. File existence: all files listed in task were created/modified
b. Pattern compliance: code matches reference file patterns at [reference-path]
c. Code quality:
   - No `console.log` or `console.error` (use proper logger)
   - No `any` types (use proper types or `unknown`)
   - Server files have `import 'server-only'`
   - No hardcoded secrets
d. Type checking: run `npm run typecheck` (if .ts/.tsx changed)
e. Test results: run `npm test` (if test files changed or affected)

**4. Verdict**
- PASS: Mark task completed via TaskUpdate with PASS verdict in description
- FAIL: Create fix task via TaskCreate with specific issues listed
  - Include file:line references
  - Cite which pattern from reference was violated
  - Specify exact fix needed

**5. No Scope Creep**
Do not suggest improvements beyond task acceptance criteria. The builder implemented what was requested — validate that, nothing more.
```

---

### Step 3: Add Optional Architect Teammate

**File:** `.claude/skills/implement/SKILL.md`

#### 3.1: Insert Step 7c (Optional Architect)

Between current Step 7b (Identify Skill and Reference) and current Step 7c (Deploy Builders).

**Note:** This will renumber existing 7c → 7d, existing 7d → 7e, existing 7e → 7f, existing 7f → 7g.

New Step 7c:

```markdown
#### 7c: Spawn Architect (Optional, High-Risk Phases Only)

**Skip this step unless:**
- Flow audit report marked this phase as "High" risk, OR
- Phase frontmatter has `skill: postgres-expert`

**For High-risk or schema design phases:**

1. **Read flow audit report** at `$ARGUMENTS/reviews/planning/flow-audit.md`
2. **Check phase risk level** in "Risk Assessment (Pending Phases)" section
3. **If High risk OR postgres-expert:**

   Spawn architect teammate:

   ```
   Task({
     description: "Architecture review for phase [NN]",
     subagent_type: "architect",
     model: "opus",
     team_name: "{plan-name}-impl",
     name: "architect",
     prompt: `You are an architect teammate. Review the phase requirements and suggest an implementation approach.

     **Phase file:** $ARGUMENTS/phase-{NN}-*.md
     **Reference file:** [reference-path from Step 6]

     Read the phase file's Requirements section. Analyze:
     1. Data model (tables, relationships, RLS)
     2. API surface (server actions, services)
     3. Integration points (upstream/downstream dependencies)
     4. Risk factors (complexity, new patterns, external services)

     Suggest:
     - Recommended implementation order
     - Key pattern decisions
     - Risk mitigations
     - Common pitfalls to avoid

     Send your analysis to the orchestrator via SendMessage.`
   })
   ```

4. **Wait for architect response** via automatic message delivery
5. **Incorporate approach into builder prompts** in Step 7c (add architect's recommendations to "Key Patterns" section)

**Why this is optional:** Most phases don't need architecture review. Only complex/risky phases benefit from upfront design analysis.
```

---

### Step 4: Bump Version

**File:** `.claude/skills/implement/SKILL.md`

- [ ] Change `version: 1.0.0` to `version: 1.1.0`

---

### Step 5: Manual Integration Test

#### 5.1: Test Builder Prompt Quality

- [ ] Create 3-task test phase
- [ ] Run `/implement`, deploy builders
- [ ] Inspect builder prompts for 8 elements
- [ ] Verify pattern extraction happened
- [ ] Verify builders produce correct code on first attempt

#### 5.2: Test Validator Prompt Quality

- [ ] Deploy validator after builder
- [ ] Inspect validator prompt for 5 elements
- [ ] Verify validator catches pattern violations
- [ ] Verify validator reports specific file:line issues

#### 5.3: Test Architect (Optional)

- [ ] Create High-risk test phase OR postgres-expert phase
- [ ] Run `/implement`
- [ ] Verify architect spawned
- [ ] Verify architect analysis incorporated into builder prompts

#### 5.4: Cleanup

- [ ] Delete test phases
- [ ] Confirm no regressions

---

## Verifiable Acceptance Criteria

**Critical Path:**

- [ ] Builder prompt template has all 8 elements
- [ ] Validator prompt template has all 5 elements
- [ ] Pattern extraction logic added to Step 7b
- [ ] Architect spawning logic added as Step 7a-2 (optional)
- [ ] Version bumped to 1.4.0

**Quality Gates:**

- [ ] Manual test shows builder prompts contain patterns from reference
- [ ] Builders produce correct code on first attempt (less rework)
- [ ] Validators catch all pattern deviations

**Integration:**

- [ ] Architect analysis incorporated into builder prompts when spawned
- [ ] Prompts self-contained (no missing context)

---

## Quality Assurance

### Review Checklist

- [ ] **Code Review Gate:**
  - [ ] Run `/code-review plans/260214-team-orchestration/phase-04-improve-team-prompts.md`
  - [ ] Files: `.claude/skills/implement/SKILL.md`
  - [ ] Critical findings addressed
  - [ ] Phase approved

---

## Dependencies

### Upstream (Required Before Starting)

- `/implement` skill defines builder/validator spawning (Steps 7c, 7d)
- Reference file read happens in Step 6

### Downstream (Will Use This Phase)

- All `/implement` invocations that spawn builders/validators

---

## Completion Gate

### Sign-off

- [ ] All acceptance criteria met
- [ ] Manual integration tests passing
- [ ] Code review passed
- [ ] Existing plans still work
- [ ] Phase marked DONE in plan.md
- [ ] Committed: `feat(workflow): upgrade team prompt templates`

---

**Previous:** [[phase-03-stop-fix-test-failures|Phase 03: Stop-and-Fix on Test Failures]]
**Next:** [[phase-05-teams-orchestration|Phase 05: Teams Instead of Sub-Agents]]
