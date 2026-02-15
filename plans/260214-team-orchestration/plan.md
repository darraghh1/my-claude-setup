---
title: "Team Orchestration Pipeline Refactor"
description: "Upgrade planning/implementation pipeline with flow audit gates, team coordination, improved prompts, test failure handling, and comprehensive review item acceptance"
status: pending
priority: P1
tags: [architecture, planning, workflow-automation, team-coordination]
created: 2026-02-14
updated: 2026-02-14
---

# Team Orchestration Pipeline Refactor

## Executive Summary

**The Mission:** Transform the planning → review → implement → code-review pipeline from a sub-agent fire-and-forget model to a coordinated team orchestration model with comprehensive quality gates.

**The Big Shift:** Moving from anonymous sub-agents spawned via Task tool to persistent named teammates with message passing, shared task lists, and multi-phase potential. The orchestrator stays lean as a team lead, not a monolithic implementer carrying all context.

**Primary Deliverables:**

1. **Quality Gates:** Flow audit integration before implementation, comprehensive review item acceptance (all severities)
2. **Team Coordination:** Persistent named teammates (builders, validators) with message passing instead of fire-and-forget sub-agents
3. **Reliability:** Pre-flight test checks, detailed prompt templates, stop-and-fix on failures

---

## Phasing Strategy (Roadmap)

We follow a **Progressive Complexity** strategy. Start with the smallest self-contained changes (flow audit gate, review item acceptance) to build confidence, then tackle test failure handling and prompt quality, finishing with the largest architectural shift (team model).

### Phase Constraints

- **Size:** 10-15KB max per phase document
- **Scope:** Single implementation session target
- **Dependencies:** Explicit in phase header
- **Review gate:** Code review via `/code-review` skill before marking DONE

### Phase File Naming

- Pattern: `phase-NN-descriptive-slug.md`
- Example: `phase-01-integrate-flow-audit-gate.md`, `phase-05-teams-orchestration.md`
- No sub-phases (no 01a, 01b) - flat sequential numbering only

### Phase Table

| Phase  | Title                                         | Focus                    | Status    |
| :----- | :-------------------------------------------- | :----------------------- | :-------- |
| **01** | [Integrate Flow Audit Gate](./phase-01-integrate-flow-audit-gate.md) | Issue 1: Audit check | Done |
| **02** | [Accept All Valid Review Items](./phase-02-accept-all-review-items.md) | Issue 5: Review items | Done |
| **03** | [Stop-and-Fix on Test Failures](./phase-03-stop-fix-test-failures.md) | Issue 4: Test gates | Done |
| **04** | [Improve Team Prompt Quality](./phase-04-improve-team-prompts.md) | Issue 3: Prompts | Done |
| **05** | [Teams Instead of Sub-Agents](./phase-05-teams-orchestration.md) | Issue 2: Team model | Done |

---

## Architectural North Star

**Purpose:** Define the immutable patterns that every phase must follow.

### 1. Skill Definition Fidelity

- **Core Principle:** Skill YAML frontmatter and markdown instructions are the API contract. Breaking changes require version bumps.
- **Enforcement:** Changes must preserve backward compatibility with existing plans. Test with a 2-3 phase plan before declaring complete.

### 2. Team Coordination Patterns

- **Core Principle:** Orchestrators stay lean by delegating to specialists. Builders implement, validators verify, team leads coordinate.
- **Enforcement:** Context window for orchestrator should remain under 20KB even after coordinating multiple phases. If exceeding, the pattern is wrong.

### 3. Grounded in Actual Codebase

- **Core Principle:** Code blocks in phases must match actual codebase patterns, not memory or generic examples.
- **Enforcement:** Read reference implementations before writing phase content. Cite reference files when describing patterns.

---

## Project Framework Alignment

This refactor modifies the planning/implementation framework itself. The patterns being changed ARE the project's framework conventions for workflow automation.

### Skill Modification Priority

1. **First:** Preserve existing plan compatibility — plans created before this refactor should still work
2. **Second:** Minimal breaking changes — version bumps required if skill API changes
3. **Third:** New features opt-in — teams mode, multi-phase mode start as optional

### File Modification Rules

| File Type | Pattern |
|-----------|---------|
| Skill Definition | YAML frontmatter + Markdown sections with `## Step N:` headers |
| Delegation Docs | Prompt templates with explicit skill invocation commands |
| Agent Definitions | YAML frontmatter + tool restrictions + role description |
| Workflow Docs | Markdown with mermaid diagrams showing full pipeline flow |

---

## Global Decision Log (Project ADRs)

**Purpose:** Record decisions that bind the entire project lifecycle.

### Use Teams for Multi-Task Phases (ADR-G-01)

**Status:** Accepted

**Context:** The current sub-agent pattern (Task tool with `run_in_background: true`) has no persistent identity, no message passing, and causes the orchestrator to hold all implementation context. Context window blowout is the primary failure mode for phases with 5+ tasks.

**Decision:** For phases with 3+ tasks, use `TeamCreate` to spawn persistent named teammates. Orchestrator communicates via `SendMessage`, teammates share a task list, and builders can be reused across multiple tasks.

**Consequences:**
- **Positive:** Orchestrator context stays lean, parallel execution preserved, multi-phase potential unlocked
- **Negative:** More complex coordination code, new failure modes (idle teammates, message delivery)
- **Neutral:** Requires updating `/implement` skill with substantial new logic

### Accept All Review Items, Not Just Critical (ADR-G-02)

**Status:** Accepted

**Context:** The current `/implement` Step 8 only fixes Critical issues from code review. Medium/Low items are presented as "suggestions" but effectively ignored. This creates a disconnect between review skills (which say "fix these") and the implementation pipeline (which discards them).

**Decision:** Process ALL severity levels. Critical/High block immediately, Medium/Low are fixed unless clearly hallucinated or purely cosmetic.

**Consequences:**
- **Positive:** Review findings have teeth, quality improves, phases aren't revisited for "suggestions"
- **Negative:** Slightly longer review cycles, need to distinguish valid Medium items from hallucinations
- **Neutral:** Aligns review skills with implementation pipeline expectations

### Integrate Flow Audit as Mandatory Gate (ADR-G-03)

**Status:** Accepted

**Context:** `/audit-plan` runs independently and is optional. Plans with circular dependencies, wrong phase ordering, or stale artifacts proceed to implementation where the problems are 10x costlier to fix.

**Decision:** `/implement` checks for flow audit before starting. Plans with 3+ phases must have a passing audit. "Major Restructuring Needed" hard blocks, "Significant Issues" soft blocks (user decides).

**Consequences:**
- **Positive:** Structural plan issues caught before implementation, fewer mid-implementation surprises
- **Negative:** Extra step for small plans, but mitigated by skipping audit for 1-2 phase plans
- **Neutral:** Requires `/implement` to read and interpret audit verdict

---

## Security Requirements

This refactor modifies workflow automation, not application code. Security considerations are limited to:

### Skill Execution Sandboxing

- Agent definitions specify `allowed-tools` to prevent unrestricted bash/file access
- Review agents are read-only for source files (can only write to `reviews/` folder)
- Orchestrators have full tool access but follow principle of least privilege when spawning teammates

### Prompt Injection Resistance

- Delegation prompts are templates, not user-controlled strings
- Task descriptions are self-contained and don't execute user-provided code
- Message passing sanitized through `SendMessage` tool (no raw shell execution)

---

## Implementation Standards

### Global Test Strategy

This refactor modifies skill definitions (YAML + markdown) which are not unit testable. Validation is manual:

- **Integration:** Test each phase with actual plan implementation (2-3 phase test plan)
- **Regression:** Verify existing plans still work after skill changes
- **E2E:** Full pipeline test — create plan → audit → review → implement → code-review

### Global Documentation Standard

Update these files as part of implementation (each phase handles its own):

1. `.claude/skills/implement/SKILL.md` — Version bump, updated steps
2. `.claude/skills/audit-plan/SKILL.md` — Version bump if integration changes
3. `.claude/skills/review-plan/SKILL.md` — Version bump, updated auto-fix behavior
4. `.claude/skills/code-review/SKILL.md` — Version bump, updated auto-fix behavior
5. Delegation docs for review skills — Updated main agent responsibilities

> Note: `docs/workflow.md` is NOT updated proactively. Request documentation updates explicitly if needed after implementation.

---

## Success Metrics & Quality Gates

### Project Success Metrics

- **Context Efficiency:** Orchestrator context stays under 20KB after coordinating 3-phase implementation
- **Quality Gate Pass Rate:** 90%+ of phases pass code review on first attempt (up from ~60% currently)
- **Test Failure Isolation:** Zero test failures from previous phases reach current phase implementation

### Global Quality Gates (Pre-Release)

- [ ] Existing plans (created before refactor) still work with updated skills
- [ ] 2-3 phase test plan completes successfully with all new features
- [ ] No regression in review quality (template/codebase scores remain consistent)
- [ ] Workflow documentation updated if explicitly requested by user
- [ ] All modified skills have version numbers bumped

---

## Resources & References

- **Current State Analysis:** Task description in `/create-plan` invocation (this file is the plan for that task)
- **Skill Definitions:** `.claude/skills/implement/`, `.claude/skills/audit-plan/`, `.claude/skills/review-plan/`, `.claude/skills/code-review/`
- **Delegation Guides:** `.claude/skills/review-plan/delegation.md`, `.claude/skills/code-review/delegation.md`, `.claude/skills/create-plan/references/delegation-guide.md`
- **Team Coordination:** `TeamCreate`, `SendMessage`, `TaskUpdate` tool documentation in skill system reminders

---

**Next:** [[phase-01-integrate-flow-audit-gate|Phase 01: Integrate Flow Audit Gate]]
