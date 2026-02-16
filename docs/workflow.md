# Planning, Reviewing, and Implementing Workflow

How the planning skills work together as an assembly line — from feature idea to shipped code.

## The Pipeline

```
/create-plan → /review-plan → /audit-plan → /implement → done
                                                      │
                                                      ├── gate: plan review verdict
                                                      ├── gate: flow audit exists
                                                      ├── gate: phase review + skeleton check
                                  │
                                  └── per unblocked phase (parallel, max 2-3):
                                      spawn builder ──→ builder-workflow
                                           │              ├── find reference
                                           │              ├── invoke domain skill
                                           │              ├── TDD → implement → test
                                           │              ├── tests + typecheck
                                           │              └── report completion
                                           │
                                      orchestrator ──→ validator
                                           │              ├── /code-review + auto-fix
                                           │              ├── tests + typecheck
                                           │              └── PASS / FAIL verdict
                                           │
                                      PASS → check unblocked / FAIL → fresh builder

/audit-plan (runs during /create-plan Step 10 for 3+ phase plans)
```

Each skill has hard gates preventing progression until quality is met. Every guardrail exists because skipping it caused hours of rework in real usage.

---

## 1. `/create-plan` — The Architect

**Files:** `SKILL.md` (378 lines) + `references/PLAN-TEMPLATE.md` + `references/PHASE-TEMPLATE.md` + `references/delegation-guide.md`

**What it does:** Creates a complete planning package in a date-prefixed folder (`plans/250214-feature-name/`). Produces:

- `plan.md` — master plan with executive summary, phase table, architecture patterns, security requirements
- `phase-01-slug.md` through `phase-NN-slug.md` — one file per atomic unit of work
- Spawns review sub-agents at the end

### The 11-step workflow

| Step | What Happens | Why It Exists |
|------|-------------|---------------|
| 1. Clarify | `AskUserQuestion` to resolve ambiguity | User experienced 20-phase plans built on wrong assumptions |
| 2. Read templates | Reads PLAN-TEMPLATE.md + PHASE-TEMPLATE.md | Phases without template reading miss required sections |
| 3. Create folder | `plans/{YYMMDD}-{feature}/` with review subfolders | Chronological sorting |
| 4. Task list | `TaskCreate` for every phase + resume check | Tasks survive context compacts; prevents lost progress |
| 5. plan.md | All sections except phase table rows | Missing sections caught during review |
| 6. Design phases | Phase breakdown with "30 small > 5 large" rule | Large phases exceed context window, lose work mid-implementation |
| 7. Read codebase | Glob + Read real files for each phase type | Code blocks from memory don't match real codebase |
| 8. Create phases | Iterative: add row, write file, validate, repeat | Each phase follows PHASE-TEMPLATE exactly |
| 9. Review | Spawn sub-agents in batches of 4 via `/review-plan` | Self-review has blind spots |
| 10. Flow audit | `/audit-plan` for 3+ phases — catches cross-phase issues | Per-phase reviews can't see circular deps or ordering problems |
| 11. Report | Summary with scores and verdict | |

### Key design decisions

- **Phases are atomic** — each should fit in ~1 context window (~15KB). "30 small phases > 5 large phases"
- **TDD is Step 0** in every phase, not an afterthought
- **`skill:` in frontmatter** tells the builder which domain skill to invoke (e.g., `postgres-expert`, `server-action-builder`)
- **Validators run inline** during creation — `validate_no_placeholders.py`, `validate_tdd_tasks.py`, `validate_new_file.py`
- **Templates are canonical** — `/review-plan` reads from `../create-plan/references/` (single source of truth)

---

## 2. `/review-plan` — The Quality Gate

**Files:** `SKILL.md` (304 lines) + `checklist.md` (400 lines) + `delegation.md` + `PLAN-REVIEW-TEMPLATE.md` + `scripts/validate_review.py`

**Templates:** Reads `PLAN-TEMPLATE.md` and `PHASE-TEMPLATE.md` from `../create-plan/references/` (no local copies).

**What it does:** Reviews ONE file per invocation (plan.md OR a single phase). Performs a **two-layer review**:

| Layer | What It Catches | Hit Rate |
|-------|----------------|----------|
| Template compliance | Missing sections, incomplete structure | Catches structural gaps |
| Codebase compliance | Code blocks that won't compile or violate patterns | Catches 100% of real issues (template-only caught 0 of 26 in real usage) |

### The codebase compliance layer

For each code block in a phase, the reviewer:

1. Classifies the phase type (schema, service, server action, component)
2. Globs for a real reference file of that type in the codebase
3. Reads the reference as ground truth
4. Compares each code block against it
5. Flags deviations with severity (Critical/High/Medium/Low)

### 12 codebase checks (from checklist.md)

1. Naming conventions (singular `schema/`, `Action` suffix, kebab-case components)
2. Server Action pattern (`'use server'` + Zod + `getSession()`)
3. Account resolution (slug to ID lookup, permission RPC)
4. Import patterns (`server-only`, path aliases, correct sources)
5. TypeScript compliance (interfaces, factory pattern, type guards)
6. Service factory patterns (private class + exported factory)
7. Export patterns (no server actions in barrel exports)
8. Error handling (generic external, detailed internal)
9. CLAUDE.md rules (no doc creation, `revalidatePath`, directives)
10. SQL safety (`IF EXISTS`, RLS enabled, no `USING(true)`)
11. Test infrastructure (correct paths, `it.todo()`, happy-dom, mocks)
12. Consistency (status match, naming across steps)

### Auto-fix

Critical, High, and Medium issues are fixed directly in the phase file. The review file gets "(Auto-fixed)" annotations. Only genuine scope changes or ADR contradictions are deferred.

### Review format validation

After writing, `scripts/validate_review.py` checks the review file structure (required sections, table format, forbidden patterns). This deterministic check catches format issues that prose instructions miss.

### Delegation model

When `/create-plan` spawns review agents, the `delegation.md` enforces:

- Max 4 concurrent agents (more causes context blowout)
- One file per agent (multiple files produce superficial reviews)
- Explicit skill invocation in the prompt (vague prompts cause agents to skip the skill)

---

## 3. `/implement` — The Thin Dispatcher

**Files:** `SKILL.md` (277 lines) + `references/team-operations.md` (156 lines)

**What it does:** Acts as a thin dispatcher that spawns ephemeral builders and validators per phase and routes PASS/FAIL verdicts. It does NOT read references, extract patterns, or implement code — builders handle implementation via the preloaded `builder-workflow` skill, and the validator handles independent code review.

### Architecture

| Role | Responsibility | Context Budget |
|------|---------------|----------------|
| **Orchestrator** (you) | Find phases, gate checks, spawn/shutdown teammates, route verdicts | Stays lean — only plan.md + teammate messages |
| **Builder** (ephemeral) | Full phase implementation via `builder-workflow` skill | Fresh 200K per phase — never compacted |
| **Validator** (ephemeral) | Independent code review via `/code-review`, then tests + typecheck | Fresh 200K per phase — eliminates bottleneck |

### The 9-step workflow

```
Step 1: Read plan.md + check plan review verdict
        ↓ (blocks if verdict is "No")
Step 2: Check flow audit exists (created by /create-plan)
        ↓ (blocks if "Major Restructuring Needed")
Step 3: Find unblocked phases + create orchestrator task list
        - TaskList check (compact recovery)
        - TaskCreate per pending phase with dependency mirroring
        - Check dependencies frontmatter for unblocked phases
        ↓
Step 4: Gate check each unblocked phase (mark task in_progress):
        - validate_no_placeholders.py
        - /review-plan phase review verdict
        ↓ (blocks if skeleton content or Critical issues)
Step 5: Create team (first phase only)
        - TeamCreate
        ↓
Step 6: Spawn builders for unblocked phases (parallel, max 2-3)
        - Fresh builder per phase with clean 200K context
        - Minimal prompt: phase file path + plan folder
        - builder-workflow skill handles the rest
        ↓
Step 7: Wait for builder completions → spawn fresh validator per phase
        ↓
Step 8: Handle verdict:
        - PASS → update plan.md + task (completed), shutdown builder + validator, wait for others
        - FAIL → shutdown builder + validator, spawn fresh builder with fix instructions
        - When all active builders done → back to Step 3 (re-scan)
        ↓
Step 9: Cleanup (all done or error breakout)
        - Shutdown all teammates
        - TeamDelete
```

### Why builders and validators are ephemeral

Each phase gets a fresh builder and validator, each with a clean 200K context window. After the review cycle completes (PASS or FAIL resolution), both are shut down. This prevents:

- **Context contamination** — bad patterns from phase 2 don't bleed into phase 3
- **Skill instruction compaction** — the `builder-workflow` skill is always fully loaded
- **Stale reference data** — each builder reads fresh references for its phase type
- **Validator bottleneck** — parallel builders each get their own validator instead of queuing for a single persistent one

### What the orchestrator does NOT do

| Old Architecture | Current Architecture |
|------------------|---------------------|
| Orchestrator reads reference files | Builder reads references (Step 3 of builder-workflow) |
| Orchestrator assigns step-level tasks | Builder creates its own task list (Step 4 of builder-workflow) |
| Orchestrator invokes domain skills | Builder invokes domain skills (Step 3 of builder-workflow) |
| Builder runs /code-review (self-review) | Validator runs /code-review (independent review) |
| Orchestrator validates code | Validator handles all review and verification |
| Builders persist across phases | Both builders and validators are ephemeral — fresh per phase |

### Hard gates that block implementation

- Plan review verdict is "No" → STOP
- Flow audit says "Major Restructuring Needed" → STOP
- Phase has placeholder content (`[To be detailed]`, `TBD`) → STOP
- Phase review has Critical/High issues → FIX phase first
- Validator FAIL repeats 3+ times on same phase → STOP, report to user

---

## 4. `/builder-workflow` — The Builder's Playbook

**Files:** `SKILL.md` (192 lines) — preloaded into builder agents via `skills: [builder-workflow]` in agent config

**What it does:** Teaches builders how to handle an entire phase end-to-end. Not user-invocable — it activates automatically when a builder is spawned.

### The 7-step workflow

| Step | What Happens | Why It Exists |
|------|-------------|---------------|
| 1. Read phase | Extract requirements, steps, acceptance criteria | Missing requirements = wrong code |
| 2. Pre-flight tests | `pnpm test` (skip for phase 01) | Catches broken tests from previous phases |
| 3. Find reference + skill | Glob for reference file, invoke domain skill | Ground truth for patterns — not guessing |
| 4. Create task list | `TaskCreate` for each implementation step | Tasks survive context compacts within a phase |
| 5. Implement | TDD (Step 0) first, then remaining steps | Untested code ships bugs |
| 6. Final verification | `pnpm test` + `pnpm run typecheck` | Both must pass before reporting |
| 7. Report completion | `SendMessage` to orchestrator | Triggers independent validator review |

### Domain skill mapping

| Phase Focus | Skill | Reference Pattern |
|-------------|-------|-------------------|
| Database, migrations, RLS | `postgres-expert` | `supabase/migrations/*.sql` |
| Server actions, API | `server-action-builder` | `app/home/[account]/**/*server-actions*.ts` |
| React forms | `react-form-builder` | `app/home/[account]/**/_components/*.tsx` |
| E2E tests | `playwright-e2e` | `e2e/tests/**/*.spec.ts` |
| React components, pages | `vercel-react-best-practices` | `app/home/[account]/**/_components/*.tsx` |
| Service layer | `service-builder` | `app/home/[account]/**/*service*.ts` |

### Context compact recovery

If a builder's context is compacted mid-phase (rare with fresh 200K windows):

1. `TaskList` → find the `in_progress` or first `pending` task
2. `TaskGet` → read the self-contained description
3. Continue from that task — don't restart the phase

---

## 5. `/code-review` — The Final Gate

**Files:** `SKILL.md` (278 lines) + `checklist.md` (451 lines) + `delegation.md` + `references/CODE-REVIEW-TEMPLATE.md` + `scripts/validate_review.py`

**What it does:** Called by the validator (independent review after each phase) to review actual code against codebase reference files, security requirements, and the phase's acceptance criteria. The builder never reviews its own code — this separation catches blind spots that self-review misses.

### Dynamic context injection

The skill automatically injects recent git activity when loaded:

```markdown
!`git log --oneline -10`         → recent commits
!`git diff --name-only HEAD~5`   → recently changed files
```

This helps the reviewer identify which files were modified without needing to ask.

### The 8-step workflow

| Step | What Happens | Why It Exists |
|------|-------------|---------------|
| 1. Read phase | Extract implementation steps + acceptance criteria | Knows what was supposed to be built |
| 2. Identify files | List all files created/modified in the phase | Scope of review |
| 3. Find references | Glob for real codebase files of each type | Ground truth for patterns — not memory |
| 4. Completeness | Verify every phase step was implemented | Catches missed requirements |
| 5. Code quality | Compare against reference + checklist (451 lines) | Catches pattern deviations at file:line level |
| 6. Write review | Read CODE-REVIEW-TEMPLATE.md, follow exact format | Consistent format across phases |
| 6b. Validate | Run `scripts/validate_review.py` | Deterministic format check |
| 7. Auto-fix | Fix Critical/High issues directly in source files | Review that doesn't fix is half the job |
| 8. Report | Verdict + issue counts + auto-fixed items | Feeds back to builder's completion report |

### The checklist (451 lines, 15+ categories)

- **Part 1 — Completeness:** TDD check, each implementation step verified, frontend test requirements
- **Part 2 — Code Quality:** TypeScript standards (11 checks), React/Next.js compliance (12 checks), React forms (detailed sub-checks), project architecture, database security & RLS, server actions & API routes, import patterns, Zod schemas, testing standards, E2E testing, Vercel performance patterns

For React/Next.js code, the reviewer loads `/vercel-react-best-practices` (57 performance rules) and checks against Critical, High, and Medium priority rules.

### Auto-fix

Critical and High issues are fixed directly in source files. The review file gets "(Auto-fixed)" annotations. Only genuine business logic changes or ADR contradictions are deferred.

Output goes to `reviews/code/phase-NN.md` (separate from planning reviews in `reviews/planning/`).

---

## 6. `/audit-plan` — The Holistic Check

**Files:** `SKILL.md` (318 lines)

**Different from `/review-plan`:** This is a **flow audit**, not a template check. It analyzes the plan as a whole:

| `/review-plan` | `/audit-plan` |
|----------------|---------------|
| One file at a time | All phases together |
| Template compliance + code patterns | Dependencies + data flow + ordering |
| "Does this phase have all sections?" | "Do these phases connect coherently?" |
| Run during creation | Run before implementing (3+ phases) |

### What it catches

- Circular dependencies between phases
- Missing/unnecessary dependency declarations
- Data flow inconsistencies (phases disagree on table names, patterns)
- Ordering issues (consumer runs before producer)
- Stale artifacts (deprecated files, mismatched statuses, broken links)
- "Done" phases whose deliverables don't exist in the codebase
- "Done" phases without passing code reviews

### Integration with /implement

The `/create-plan` skill runs `/audit-plan` as Step 10 for plans with 3+ phases. The `/implement` orchestrator then gate-checks that the audit exists (Step 2) — if missing, it stops and asks the user to run the audit first. Results gate implementation:

| Assessment | Behavior |
|-----------|----------|
| "Major Restructuring Needed" | Hard block — STOP |
| "Significant Issues" | Soft block — warn user, ask whether to proceed |
| "Minor Issues" or "Coherent" | Proceed |

---

## End-to-End Example

```
User: "/create-plan add notes feature"
  ├─ Clarify → AskUserQuestion
  ├─ Read templates (PLAN-TEMPLATE.md, PHASE-TEMPLATE.md)
  ├─ Read codebase references (server-actions.ts, service.ts, etc.)
  ├─ Write plan.md + phase-01.md through phase-05.md
  ├─ Run validators (no placeholders, TDD ordering, files exist)
  └─ Spawn review agents in batches of 4
      └─ Each agent calls: /review-plan plans/250214-notes phase NN
          ├─ Template compliance (12/12 sections?)
          ├─ Codebase compliance (code blocks match real patterns?)
          └─ Auto-fix Critical/High/Medium issues in phase files

User: "/implement plans/250214-notes"
  ├─ Check plan review verdict → must be "Yes"
  ├─ Check flow audit exists (created by /create-plan Step 10)
  │
  ├─ Scan: Phases 1-3 unblocked (dependencies: []), Phase 4 blocked by Phase 1
  │   ├─ Gate check each: no placeholders, phase reviews pass
  │   ├─ TeamCreate + spawn validator (once)
  │   ├─ Spawn builders in parallel (builder-1, builder-2, builder-3)
  │   │   ├─ builder-1: Phase 1 → /postgres-expert → TDD → verify → "done"
  │   │   ├─ builder-2: Phase 2 → /service-builder → TDD → verify → "done"
  │   │   └─ builder-3: Phase 3 → /server-action-builder → TDD → verify → "done"
  │   ├─ As each completes → validator reviews → PASS → update plan.md → shutdown builder
  │   └─ All 3 done → re-scan for newly unblocked phases
  │
  ├─ Scan: Phase 4 now unblocked (Phase 1 done), Phase 5 still blocked
  │   ├─ Gate check: passes
  │   ├─ Spawn builder-1 for Phase 4
  │   ├─ Validator: /code-review → verify → PASS
  │   ├─ Update plan.md: Phase 4 → Done
  │   └─ Shutdown builder
  │
  ├─ ... (repeat: scan → gate → spawn → review → next)
  │
  └─ All phases Done → shutdown validator → TeamDelete → cleanup
```

---

## Quality Layers

Quality checks execute in this order during each phase:

| Layer | When | What | Runs On |
|-------|------|------|---------|
| 1. PostToolUse hook | Every Write/Edit | `typescript_validator.py` catches TS issues at write time | Builder + Validator |
| 2. Builder verification | After implementation | `pnpm test` + `pnpm run typecheck` | Builder |
| 3. Validator `/code-review` | After builder reports done | 451-line checklist, reference-grounded, auto-fix (independent agent) | Validator |
| 4. Validator verification | After code review auto-fixes | `pnpm test` + `pnpm run typecheck` | Validator |

---

## Key Design Principles

### Thin dispatcher + smart workers

The orchestrator's context budget stays lean — it only holds plan.md and teammate messages. All heavy lifting (reading references, invoking skills, implementing, reviewing) happens in builders with fresh 200K context windows. This prevents the orchestrator from hitting context limits on large plans.

### Ephemeral builders and validators

Both builders and validators are spawned fresh per phase and shut down after the review cycle completes. This prevents context contamination between phases, ensures skill instructions are always fully loaded (never compacted), and eliminates the single-validator bottleneck when multiple builders run in parallel.

### Reviews folder separation

`reviews/planning/` holds template + codebase compliance reviews from `/review-plan`. `reviews/code/` holds post-implementation reviews from `/code-review`. This means you can re-review a phase after fixing issues without losing the original review.

### Task descriptions as survival mechanism

Builder task descriptions must be self-contained with file paths, function signatures, and acceptance criteria — because after a context compact, `TaskGet` on the in-progress task is ALL you have.

Bad: `"Create the dropdown component"`
Good: `"Create app/home/[account]/roles/_components/change-role-dropdown.tsx. Props: { membershipId, accountSlug }. Fetch roles via listRolesAction, filter by hierarchy_level. Use @/components/ui Select, Badge."`

### The "30 small > 5 large" rule

Reflects a fundamental constraint of AI-assisted development: each phase must fit in one context window. A 25-phase plan sounds excessive to humans, but for Claude it means each phase gets full attention without losing context mid-implementation.

### Codebase grounding over static checklists

Both `/review-plan` and `/code-review` read actual files from the codebase before flagging issues. This prevents flagging things that are correct in this specific codebase, and catches violations that a static checklist might miss.

### Single source of truth for templates

`PLAN-TEMPLATE.md` and `PHASE-TEMPLATE.md` live in `/create-plan/references/` only. The `/review-plan` skill reads from there via relative path. One update, one location.

---

## Skill Comparison

| Aspect | create-plan | review-plan | audit-plan | implement | builder-workflow | code-review |
|--------|-------------|-------------|------------|-----------|-----------------|-------------|
| Lines | 362 | 304 | 318 | 261 | 192 | 278 |
| Supporting files | 3 | 4 | 0 | 1 | 0 | 4 |
| Validators used | 3 | 3 | 1 | 1 | 0 | 1 |
| Auto-fix | No | Yes (Crit/High/Med) | No | No (builders do it) | No (validator does it) | Yes (Crit/High) |
| Execution model | Single agent | Single agent (forked) | Single agent (forked) | Thin dispatcher + team | Preloaded into builder | Single agent (forked) |
| Model | Sonnet | Sonnet | Sonnet | Opus (orchestrator) | Opus (builder) | Sonnet |
| User-invocable | Yes | Yes | Yes | Yes | No | Yes |
