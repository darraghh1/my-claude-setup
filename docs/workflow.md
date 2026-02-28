# Planning, Reviewing, and Implementing Workflow

How the planning skills work together as an assembly line — from feature idea to shipped code.

## The Pipeline

```
/create-plan → /audit-plan → /review-plan → /implement → done
                                                │
                                                ├── gate: plan review + flow audit
                                                │
                                                └── for each group (sequential):
                                                    │
                                                    ├── build phases (parallel where deps allow, max 2):
                                                    │   spawn builder (worktree) ──→ builder-workflow
                                                    │        │                        ├── find reference
                                                    │        │                        ├── invoke domain skill
                                                    │        │                        ├── TDD → implement → test
                                                    │        │                        ├── commit to worktree branch
                                                    │        │                        └── report completion
                                                    │        │
                                                    │   orchestrator merges worktree branch → validator
                                                    │        │              ├── validator-workflow
                                                    │        │              ├── /code-review + auto-fix
                                                    │        │              ├── tests + typecheck + E2E/DB
                                                    │        │              └── PASS / FAIL verdict
                                                    │        │
                                                    │   PASS → next phase / FAIL → revert merge, fresh builder (worktree)
                                                    │
                                                    ├── all group phases done → spawn auditor
                                                    │   auditor ──→ auditor-workflow
                                                    │        ├── cross-phase regressions
                                                    │        ├── deferred items check
                                                    │        ├── tests + typecheck
                                                    │        ├── plan vs reality
                                                    │        └── severity-rated report
                                                    │
                                                    └── orchestrator triages:
                                                        ├── Clean/Low → continue to next group
                                                        ├── Medium → auto-fix (builder + validator)
                                                        └── High/Critical → ask user

/audit-plan (runs during /create-plan Step 6 for 3+ phase plans, BEFORE per-phase reviews)
```

Each skill has hard gates preventing progression until quality is met. Every guardrail exists because skipping it caused hours of rework in real usage.

---

## 1. `/create-plan` — The Orchestrator

**Files:** `SKILL.md` (~450 lines) + `references/PLAN-TEMPLATE.md` + `references/PHASE-TEMPLATE.md` + `references/delegation-guide.md`

**What it does:** Acts as a **thin dispatcher** that clarifies requirements with the user, spawns an Explore agent to ground the plan in code reality, then spawns an ephemeral planner agent for plan/phase creation, and finally validators for review. The orchestrator does NOT read templates, explore the codebase, or create files — the exploration agent and planner handle their respective work.

### Architecture

| Role | Responsibility |
|------|---------------|
| **Orchestrator** | Clarify requirements with user, spawn/shutdown planner + validators, relay checkpoints for user approval, route review feedback |
| **Planner** (ephemeral) | Read templates, explore codebase references, create plan.md + all phase files, self-validate. Reports at two checkpoints for user course-correction. |
| **Validator** (ephemeral) | Run `/review-plan` against one file (plan.md or single phase). Reports template score + codebase compliance. |

### The 10-step workflow

| Step | What Happens | Why It Exists |
|------|-------------|---------------|
| 1. Clarify | `AskUserQuestion` to resolve ambiguity | User experienced 20-phase plans built on wrong assumptions |
| 2. Create team | `TeamCreate` for planner + validators | Enables message routing between agents |
| 2.5. Codebase exploration | Spawn Explore agent (haiku) to produce grounding summary | Separates "what does the code look like" from "is this feasible" — prevents plans built on assumptions |
| 3. Spawn planner | Fresh ephemeral agent with 200K context, invokes `planner-workflow` skill as first action + exploration summary | Planner reads templates, creates all artifacts grounded in code reality |
| 4. User checkpoint — plan review | Orchestrator relays planner's plan summary for user approval | Catches wrong assumptions before phases are written |
| 5. User checkpoint — phases complete | Orchestrator relays completion summary | User verifies phase breakdown before review |
| 6. Flow audit | `/audit-plan` for 3+ phases — catches structural/design issues | Structural issues invalidate all per-phase review work; bail out early on broken plans |
| 7. Spawn validators | Batches of max 4 concurrent, each runs `/review-plan` on one file | Self-review has blind spots; one file per agent prevents superficial reviews |
| 8. Handle verdicts | Route PASS/FAIL back to planner for fixes | Ensures all issues are resolved |
| 9. Cleanup | Shutdown planner + validators, delete team, report summary | |

### Key design decisions

- **Thin dispatcher** — orchestrator stays lean (only messages + plan.md), all heavy lifting in planner with fresh 200K context
- **Two user checkpoints** — plan summary reviewed before writing phases, phase completion reviewed before spawning validators
- **Ephemeral planner** — fresh context prevents skill compaction and context contamination
- **Phases are atomic** — each should fit in ~1 context window (~15KB). "30 small phases > 5 large phases"
- **TDD is Step 0** in every phase, not an afterthought
- **`skill:` in frontmatter** tells the builder which domain skill to invoke (e.g., `postgres-expert`, `server-action-builder`)
- **Validators run inline** during creation — `validate_no_placeholders.py`, `validate_tdd_tasks.py`, `validate_new_file.py`
- **Templates are canonical** — `/review-plan` reads from `../create-plan/references/` (single source of truth)

---

## 2. `/review-plan` — The Quality Gate

**Files:** `SKILL.md` (346 lines) + `checklist.md` (400 lines) + `delegation.md` + `PLAN-REVIEW-TEMPLATE.md` + `scripts/validate_review.py`

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

**Files:** `SKILL.md` (~510 lines) + `references/team-operations.md`

**What it does:** Acts as a thin dispatcher that processes phases in **groups** — connected phases that build the same feature area. For each group: spawns ephemeral builders (in isolated git worktrees) and validators per phase, then an auditor for cross-phase analysis. It does NOT read references, extract patterns, or implement code — builders, validators, and auditors handle their respective work via workflow skills (invoked as their first action).

### Architecture

| Role | Responsibility | Context Budget |
|------|---------------|----------------|
| **Orchestrator** (you) | Parse groups, gate checks, spawn/shutdown agents, route verdicts, triage auditor findings, track cross-group state | Stays lean — only plan.md + teammate messages |
| **Builder** (ephemeral) | Full phase implementation via `builder-workflow` skill in isolated git worktree. Commits to worktree branch; orchestrator merges before validation. | Fresh 200K per phase — never compacted |
| **Validator** (ephemeral) | Independent code review via `/code-review`, then tests + typecheck | Fresh 200K per phase — eliminates bottleneck |
| **Auditor** (ephemeral) | Group-level audit via `auditor-workflow` — cross-phase regressions, deferred items, plan drift | Fresh 200K per group — runs alone after all phases pass |

### Processing model

```
for each group (sequential):
  1. Gate check all phases in group
  2. Build phases (parallel where deps allow, max 2)
  3. Validate each phase (PASS/FAIL routing)
  4. When all group phases PASS → spawn auditor
  5. Orchestrator reads auditor report and triages:
     - Clean/Low → log deviations, continue to next group
     - Medium → auto-spawn builder + validator to fix
     - High/Critical → checkpoint with user, then fix
  6. Track deviation summary for next group's auditor
```

### The 10-step workflow

```
Step 1: Read plan.md + check plan review verdict
        ↓ (blocks if verdict is "No")
Step 2: Check flow audit exists (created by /create-plan)
        ↓ (blocks if "Unusable" or "Major Restructuring Needed")
Step 3: Parse groups from Phase Table + Group Summary
        - Build execution plan: group order, phase dependencies
        - TaskCreate per phase with group + dependency metadata
        ↓
Step 4: Gate check each phase in current group:
        - validate_no_placeholders.py
        - /review-plan phase review verdict
        ↓ (blocks if skeleton content or Critical issues)
Step 5: Create team (first group only)
        - TeamCreate, reused across all groups
        ↓
Step 6: Spawn builders for unblocked phases (parallel, max 2)
        - Fresh builder per phase in isolated git worktree
        - Minimal prompt: phase file path + plan folder + domain skill
        - builder-workflow skill handles the rest
        ↓
Step 7: Wait for builder completions:
        7a: Merge worktree branch into main tree
        7b: Spawn fresh validator per phase (on main tree)
        7c: Wait for all validator verdicts in batch
        ↓
Step 8: Handle verdict:
        - PASS → update plan.md + task (completed), shutdown builder + validator
        - FAIL → git revert merge, shutdown builder + validator, spawn fresh builder (worktree) with fix instructions
        - When all group phases PASS → spawn auditor (runs alone)
        ↓
Step 9: Triage auditor findings:
        - Clean/Low → log deviation summary, continue to next group
        - Medium → auto-spawn builder + validator to fix (no user input)
        - High/Critical → checkpoint with user, present findings, ask for direction
        - Pass deviation summary to next group's auditor
        ↓ (loop back to Step 4 for next group)
Step 10: Cleanup (all groups done or error breakout)
         - Shutdown all teammates
         - TeamDelete
```

### Concurrency limits

| Constraint | Limit | Why |
|-----------|-------|-----|
| Builders per batch | Max 2 | Context pressure from parallel completions |
| Validators per batch | Max 2 (one per builder) | Each builder gets one validator |
| **Total active agents** | **Max 4** | Orchestrator context budget |
| Auditor | Runs alone | No builders/validators active during audit |
| Batch overlap | **None** | Wait for current batch to fully complete before spawning next |

### Why builders, validators, and auditors are ephemeral

Each phase gets a fresh builder (in an isolated git worktree) and validator, each with a clean 200K context window. After the review cycle completes (PASS or FAIL resolution), both are shut down. After all group phases pass, an auditor gets a fresh context for cross-phase analysis. This prevents:

- **Context contamination** — bad patterns from phase 2 don't bleed into phase 3
- **Skill instruction compaction** — the `builder-workflow` skill is always fully loaded
- **Stale reference data** — each builder reads fresh references for its phase type
- **Validator bottleneck** — parallel builders each get their own validator instead of queuing for a single persistent one
- **Drift snowballing** — group auditors catch issues incrementally rather than after 20 phases
- **File corruption from parallel builds** — worktree isolation means two builders can't step on the same files; the orchestrator merges sequentially

### Cross-group deviation tracking

Each auditor receives a summary of previous groups' deviations in its spawn prompt. This creates a chain of awareness — if the "auth-system" group had naming inconsistencies, the "dashboard-ui" auditor specifically checks whether dashboard phases compound that drift.

### What the orchestrator does NOT do

| Old Architecture | Current Architecture |
|------------------|---------------------|
| Orchestrator reads reference files | Builder reads references (Step 3 of builder-workflow) |
| Orchestrator assigns step-level tasks | Builder creates its own task list (Step 4 of builder-workflow) |
| Orchestrator invokes domain skills | Builder invokes domain skills (Step 3 of builder-workflow) |
| Builder runs /code-review (self-review) | Validator runs /code-review (independent review) |
| Orchestrator validates code | Validator handles all review and verification |
| Builders persist across phases | All agents are ephemeral — fresh per phase/group |
| Builders share the working directory | Builders run in isolated git worktrees — orchestrator merges branches |
| No group auditing | Auditor reviews cross-phase issues per group |

### Hard gates that block implementation

- Flow audit says "Unusable" or "Major Restructuring Needed" → STOP
- Plan review verdict is "No" → STOP
- Phase has placeholder content (`[To be detailed]`, `TBD`) → STOP
- Phase review has Critical/High issues → FIX phase first
- Validator FAIL repeats 3+ times on same phase → STOP, report to user

---

## 4. `/builder-workflow` — The Builder's Playbook

**Files:** `SKILL.md` (~220 lines) — invoked by builder agents as their first action via `Skill({ skill: "builder-workflow" })`

**What it does:** Teaches builders how to handle an entire phase end-to-end in an isolated git worktree. Not user-invocable — builders invoke it explicitly as Step 1 of their agent instructions.

### The 9-step workflow

| Step | What Happens | Why It Exists |
|------|-------------|---------------|
| 0. Load project rules | Read `coding-style.md` + `patterns.md` | Teammates don't inherit all parent rules — file-scoped rules must be read explicitly |
| 1. Read phase | Extract requirements, steps, acceptance criteria | Missing requirements = wrong code |
| 2. Pre-flight tests | `pnpm test` (skip for phase 01) | Catches broken tests from previous phases |
| 3. Find reference + skill | Glob for reference file, invoke domain skill | Ground truth for patterns — not guessing |
| 4. Create task list | `TaskCreate` for each implementation step | Tasks survive context compacts within a phase |
| 5. Implement | TDD (Step 0) first, then remaining steps | Untested code ships bugs |
| 6. Final verification | `pnpm test` + `pnpm run typecheck` + conditional `pnpm test:e2e` / `pnpm test:db` | All must pass before reporting |
| 7. Commit changes | `git add -A && git commit` in worktree branch | Uncommitted worktree changes can't be merged — the commit IS the handoff to the orchestrator |
| 8. Report completion | `SendMessage` to orchestrator | Triggers worktree merge + independent validator review |

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

## 5. `/validator-workflow` — The Validator's Playbook

**Files:** `SKILL.md` (~155 lines) — invoked by validator agents as their first action via `Skill({ skill: "validator-workflow" })`

**What it does:** Teaches validators how to handle validation end-to-end. Not user-invocable — validators invoke it explicitly as Step 1 of their agent instructions.

### The 7-step workflow

| Step | What Happens | Why It Exists |
|------|-------------|---------------|
| 0. Load project rules | Read `coding-style.md` + `patterns.md` | These rules inform what gets flagged during review |
| 1. Read phase | Extract `skill:` field, acceptance criteria, files modified | Determines which extra tests to run |
| 2. Run /code-review | Invoke `/code-review` skill (reference-grounded, auto-fix) | Builder never reviews its own code |
| 3. Run verification | `pnpm test` + `pnpm run typecheck` + conditional E2E/DB | Catches issues from auto-fixes and phase-type-specific regressions |
| 4. Determine verdict | PASS/FAIL based on review + verification | Clear signal to orchestrator |
| 5. Report to orchestrator | `SendMessage` with verdict + E2E/DB status | Orchestrator routes next action |
| 6. Go idle | Wait for next assignment or shutdown | Ephemeral lifecycle |

### Conditional testing by phase type

The phase's `skill:` frontmatter field routes to additional test commands:

| Phase Skill | Extra Test | Command |
|-------------|-----------|---------|
| Frontend skills (`react-form-builder`, `vercel-react-best-practices`, etc.) | E2E tests | `pnpm test:e2e` (scoped to feature) |
| `postgres-expert` | DB tests | `pnpm test:db` |
| Backend skills (`server-action-builder`, `service-builder`) | Unit tests sufficient | — |

E2E tests are scoped by extracting keywords from the phase title and globbing for matching spec files. Commands that don't exist are skipped gracefully.

---

## 6. `/code-review` — The Final Gate

**Files:** `SKILL.md` (317 lines) + `checklist.md` (451 lines) + `delegation.md` + `references/CODE-REVIEW-TEMPLATE.md` + `scripts/validate_review.py`

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

## 7. `/audit-plan` — The Structural Gate

**Files:** `SKILL.md` (340 lines)

**Different from `/review-plan`:** This is a **structural design audit**, not a template check. It analyzes the plan as a whole and runs BEFORE per-phase reviews:

| `/audit-plan` | `/review-plan` |
|----------------|---------------|
| All phases together | One file at a time |
| Dependencies + data flow + ordering | Template compliance + code patterns |
| "Do these phases connect coherently?" | "Does this phase have all sections?" |
| Runs FIRST (before reviews) | Runs AFTER audit passes |
| Tolerates rough edges (unreviewed phases) | Strict on template compliance + codebase patterns |

### What it catches

- Circular dependencies between phases
- Missing/unnecessary dependency declarations
- Data flow inconsistencies (phases disagree on table names, patterns)
- Ordering issues (consumer runs before producer)
- Stale artifacts (deprecated files, mismatched statuses, broken links)
- Fundamentally broken plans (bail-out with "Unusable" verdict)

### Bail-out mechanism

If the plan is fundamentally broken (circular deps, no coherent execution order, >50% missing dependencies), the audit bails out immediately with an "Unusable" verdict instead of completing the full analysis. This saves the user from waiting through a full audit of a plan that needs to be thrown out and rewritten.

### Integration with /create-plan and /implement

The `/create-plan` skill runs `/audit-plan` as **Step 6** for plans with 3+ phases — BEFORE spawning review validators. This prevents wasting time reviewing phases that have structural design issues. The `/implement` orchestrator then gate-checks that the audit exists (Step 2) — if missing, it stops and asks the user to run the audit first. Results gate both reviews and implementation:

| Assessment | Behavior |
|-----------|----------|
| "Unusable" | Hard block — plan needs restructuring |
| "Major Restructuring Needed" | Hard block — STOP |
| "Significant Issues" | Soft block — warn user, ask whether to proceed |
| "Minor Issues" or "Coherent" | Proceed |

---

## 8. Group Auditing — The Incremental Post-Mortem

**Files:** `auditor-workflow/SKILL.md` (~383 lines, invoked by auditor as first action) + `agents/team/auditor.md`

**What it does:** After each group of connected phases completes the build/validate cycle, an auditor reviews the group for problems that per-phase reviews structurally cannot catch. This happens incrementally — audit after each group, not after the whole plan — so drift is caught early while it's still cheap to fix.

### How it differs from other review steps

| Step | When | Scope | Focus |
|------|------|-------|-------|
| `/audit-plan` | Before reviews (structural gate) | All phases together | Dependencies, data flow, ordering |
| `/review-plan` | After audit passes | One file at a time | Template + codebase compliance |
| `/code-review` | During implementation | One phase's files | Code quality, security, patterns |
| **Group audit** | **After each group completes** | **Connected phases** | Cross-phase regressions, deferred items, plan drift |

### What the auditor checks

| Step | What Happens | Why It Exists |
|------|-------------|---------------|
| 1. Read group | Build inventory of group's phases with acceptance criteria | Baseline for comparison |
| 2. Collect reviews | Read `reviews/code/phase-*.md` for group phases | Aggregate quality data |
| 3. Deferred items | Check each deferred item against current code | #1 source of quality debt — no pipeline step checks these |
| 4. Cross-phase impact | Find shared files, check git history, verify no overwrites | Per-phase reviews can't see inter-phase regressions |
| 5. Verification | Run `pnpm test` + `pnpm run typecheck` | Don't trust stale results |
| 6. Plan vs implementation | Verify acceptance criteria, scope comparison, ADR compliance | "Did we build what we planned?" |
| 7. Previous groups | Check if this group compounds earlier deviations | Prevents drift from snowballing |
| 8. Write report | Structured audit at `reviews/implementation/group-{name}-audit.md` | Persistent record |
| 9. Report to orchestrator | Severity-rated findings via SendMessage | Orchestrator triages |

### How the orchestrator triages

| Finding Severity | Orchestrator Action |
|-----------------|---------------------|
| **No issues / Low** | Log deviation summary, continue to next group |
| **Medium** | Auto-spawn builder to fix + validator to verify. No user input. |
| **High / Critical** | Checkpoint with user. Present findings, ask for direction. |

### Cross-group deviation tracking

Each auditor receives a summary of previous groups' deviations in its spawn prompt. This creates a chain of awareness — if the "auth-system" group had naming inconsistencies, the "dashboard-ui" auditor specifically checks whether dashboard phases compound that drift.

### Output location

`{plan-folder}/reviews/implementation/group-{name}-audit.md` — one report per group. Lives alongside planning reviews (`reviews/planning/`) and code reviews (`reviews/code/`).

---

## End-to-End Example

```
User: "/create-plan add notes feature"
  ├─ Clarify → AskUserQuestion
  ├─ Explore codebase (haiku) → grounding summary of affected files, patterns, reusable components
  ├─ Spawn planner agent (Opus, fresh 200K context + exploration summary)
  │   ├─ Read templates (PLAN-TEMPLATE.md, PHASE-TEMPLATE.md)
  │   ├─ Read codebase references (server-actions.ts, service.ts, etc.)
  │   ├─ Write plan.md with Phase Table + Group Summary
  │   ├─ Checkpoint 1 → orchestrator relays to user for review
  │   ├─ User approves → create phase-01.md through phase-05.md
  │   │   Groups: "data-layer" (P01-P02), "api-layer" (P03-P04), "ui-layer" (P05)
  │   ├─ Self-validate each phase (no placeholders, TDD ordering, files exist)
  │   └─ Checkpoint 2 → orchestrator relays completion summary
  ├─ Flow audit (/audit-plan) → structural design checks pass (deps, ordering, data flow)
  ├─ Spawn review agents in batches of 4
  │   └─ Each agent calls: /review-plan plans/250214-notes phase NN
  │       ├─ Template compliance (12/12 sections?)
  │       ├─ Codebase compliance (code blocks match real patterns?)
  │       └─ Auto-fix Critical/High/Medium issues in phase files
  └─ All reviews pass → ready for /implement

User: "/implement plans/250214-notes"
  ├─ Check plan review verdict → must be "Yes"
  ├─ Check flow audit → "Coherent" or "Minor Issues"
  ├─ Parse groups from Phase Table + Group Summary
  │
  ├─ GROUP 1: "data-layer" (P01, P02 — no inter-dependencies)
  │   ├─ Gate check both: no placeholders, phase reviews pass
  │   ├─ TeamCreate (first run only)
  │   ├─ Spawn builders in parallel (max 2, each in isolated worktree)
  │   │   ├─ builder-1 (worktree): Phase 01 → /postgres-expert → TDD → verify → commit → "done"
  │   │   └─ builder-2 (worktree): Phase 02 → /service-builder → TDD → verify → commit → "done"
  │   ├─ As each completes → merge worktree branch → spawn fresh validator → /code-review → PASS
  │   ├─ All group phases done → shutdown builders + validators
  │   ├─ Spawn auditor (Opus, runs alone)
  │   │   ├─ Read both phases + their code reviews
  │   │   ├─ Cross-phase: notes-service.ts touched by P01 migration + P02 service
  │   │   ├─ Run tests + typecheck
  │   │   ├─ Write report → reviews/implementation/group-data-layer-audit.md
  │   │   └─ Verdict: "No Issues" → continue
  │   └─ Shutdown auditor → proceed to next group
  │
  ├─ GROUP 2: "api-layer" (P03, P04 — P04 depends on P03)
  │   ├─ Build P03 first → validate → PASS
  │   ├─ P04 unblocked → build → validate → PASS
  │   ├─ Spawn auditor (receives data-layer deviation summary)
  │   │   ├─ Finding: Medium — missing error handling in action (P03:L42)
  │   │   └─ Report → reviews/implementation/group-api-layer-audit.md
  │   ├─ Orchestrator triages: Medium → auto-fix
  │   │   ├─ Spawn builder with fix instructions → validator → PASS
  │   │   └─ Mark fix task complete
  │   └─ Shutdown auditor → proceed to next group
  │
  ├─ GROUP 3: "ui-layer" (P05 — depends on P03)
  │   ├─ Build P05 → validate → PASS
  │   ├─ Spawn auditor (receives data-layer + api-layer deviations)
  │   │   └─ Verdict: "No Issues"
  │   └─ Shutdown auditor
  │
  └─ All groups done → TeamDelete → cleanup → final summary
```

---

## Quality Layers

Quality checks execute in this order during implementation:

| Layer | When | What | Runs On |
|-------|------|------|---------|
| 1. PostToolUse hook | Every Write/Edit | `typescript_validator.py` catches TS issues at write time | Builder + Validator |
| 2. Builder verification | After implementation | `pnpm test` + `pnpm run typecheck` + conditional `pnpm test:e2e` / `pnpm test:db` | Builder |
| 3. Validator `/code-review` | After builder reports done | 451-line checklist, reference-grounded, auto-fix (independent agent) | Validator |
| 4. Validator verification | After code review auto-fixes | `pnpm test` + `pnpm run typecheck` + conditional `pnpm test:e2e` / `pnpm test:db` | Validator |
| 5. Group audit | After all phases in group pass | Cross-phase regressions, deferred items, plan drift, acceptance criteria | Auditor |

---

## Key Design Principles

### Thin dispatcher + smart workers

The orchestrator's context budget stays lean — it only holds plan.md and teammate messages. All heavy lifting (reading references, invoking skills, implementing, reviewing) happens in builders with fresh 200K context windows. This prevents the orchestrator from hitting context limits on large plans.

### Ephemeral builders, validators, and auditors

All agents are spawned fresh and shut down after their cycle completes — builders per phase, validators per phase, auditors per group. This prevents context contamination, ensures skill instructions are always fully loaded (never compacted), and eliminates bottlenecks when multiple builders run in parallel.

### Reviews folder separation

`reviews/planning/` holds template + codebase compliance reviews from `/review-plan`. `reviews/code/` holds post-implementation reviews from `/code-review`. `reviews/implementation/` holds group audit reports (`group-{name}-audit.md`) written by the auditor after each group completes during `/implement`. This means you can re-review a phase after fixing issues without losing the original review, and the group audits capture the cross-phase holistic view that per-phase reviews miss — catching drift incrementally rather than at the end.

### Task descriptions as survival mechanism

Builder task descriptions must be self-contained with file paths, function signatures, and acceptance criteria — because after a context compact, `TaskGet` on the in-progress task is ALL you have.

Bad: `"Create the dropdown component"`
Good: `"Create app/home/[account]/roles/_components/change-role-dropdown.tsx. Props: { membershipId, accountSlug }. Fetch roles via listRolesAction, filter by hierarchy_level. Use @/components/ui Select, Badge."`

### The "30 small > 5 large" rule

Reflects a fundamental constraint of AI-assisted development: each phase must fit in one context window. A 25-phase plan sounds excessive to humans, but for Claude it means each phase gets full attention without losing context mid-implementation.

### Passive domain context over on-demand invocation

The [Vercel skills evaluation](research/vercel-skills-findings.md) showed that passive context (always loaded) achieves 100% compliance, while on-demand skill invocation maxes out at 53-79% even with explicit instructions. The `domain-patterns.md` rule compresses critical patterns from all 9 domain knowledge skills into ~6.8KB of passive context. It uses `alwaysApply: true` so it loads natively for all agents (including team teammates) — no skill invocation required. Each section has a `ref:` pointer to the full SKILL.md for deep reading when the compressed patterns aren't enough (retrieval-led reasoning).

### Codebase grounding over static checklists

Both `/review-plan` and `/code-review` read actual files from the codebase before flagging issues. This prevents flagging things that are correct in this specific codebase, and catches violations that a static checklist might miss.

### Single source of truth for templates

`PLAN-TEMPLATE.md` and `PHASE-TEMPLATE.md` live in `/create-plan/references/` only. The `/review-plan` skill reads from there via relative path. One update, one location.

---

## Skill Comparison

| Aspect | create-plan | review-plan | audit-plan | implement | builder-workflow | validator-workflow | auditor-workflow | code-review |
|--------|-------------|-------------|------------|-----------|-----------------|-------------------|-----------------|-------------|
| Lines | ~450 | 346 | 364 | ~510 | ~220 | ~155 | ~383 | 317 |
| Supporting files | 3 | 4 | 0 | 1 | 0 | 0 | 0 | 4 |
| Validators used | 3 | 3 | 1 | 1 | 0 | 0 | 0 | 1 |
| Auto-fix | No | Yes (Crit/High/Med) | No | Yes (via builders) | No (validator does it) | Yes (via /code-review) | No (read-only) | Yes (Crit/High) |
| Execution model | Thin dispatcher + planner | Single agent (forked) | Single agent (forked) | Thin dispatcher + team | Invoked by builder (first action) | Invoked by validator (first action) | Invoked by auditor (first action) | Single agent (forked) |
| Model | Opus (planner) | Sonnet | Sonnet | Opus (orchestrator) | Opus (builder) | Opus (validator) | Opus (auditor) | Sonnet |
| User-invocable | Yes | Yes | Yes | Yes | No | No | No | Yes |
