# Team Operations Reference

Supplementary material for the `/implement` skill. Covers teammate lifecycles, anti-pattern prevention, compact recovery, and troubleshooting.

---

## Builder Teammate Lifecycle (1M Context — One Builder Per Group)

**Builders persist across a group.** One builder handles all phases in a group sequentially, accumulating context. This means the builder that implements the database schema already knows the table structure when it builds the service layer. After the group completes, the builder is shut down.

Each builder follows this flow:

1. **Spawned by orchestrator** with a targeted briefing: all phase file paths, cross-phase context, architectural decisions
2. **builder-workflow skill invoked** — builder's first action is `Skill({ skill: "builder-workflow" })`
3. **For each phase in the group:**
   a. Read phase — extract requirements, steps, acceptance criteria
   b. Pre-flight test check — verify previous phases haven't left broken tests
   c. Find reference + invoke domain skill — ground truth for patterns
   d. Create internal task list — `TaskCreate` for each step, prefixed with `[Step]`
   e. Implement with TDD — Step 0 first, then remaining steps
   f. Final verification — `pnpm test` + `pnpm run typecheck`
   g. Commit changes — `git add -A && git commit -m "feat(phase-{NN}): {title}"`
   h. Report phase completion to orchestrator via SendMessage
   i. Wait for orchestrator to confirm merge + validation passed
   j. Continue to next phase (builder retains all context from earlier phases)
4. **Shutdown** when all phases in the group are done

**Builders do NOT run `/code-review`** — the validator handles that independently.

## Validator Teammate Lifecycle

**Validators are ephemeral.** One fresh validator per phase, spawned after each builder phase completion + merge. The validator runs on the main tree (not worktree) to verify the integrated result.

1. **Spawned on-demand** by the orchestrator after merging a builder's phase commit
2. **Run `/code-review`** — reference-grounded analysis with auto-fix for Critical/High/Medium
3. **Run verification** (only if auto-fixes were applied) — `pnpm run typecheck` + `pnpm test`
4. **Report verdict** — PASS or FAIL with specific file:line references and fixes needed
5. **Shutdown** — orchestrator sends shutdown_request

## Auditor Lifecycle (Plan-Level)

**One auditor for the entire plan.** Spawned after ALL groups complete. Reviews all phases together for cross-phase regressions, deferred items, and plan drift. Write audit report to `$ARGUMENTS/reviews/implementation/plan-audit.md`.

## Orchestrator Responsibilities (Fat Orchestrator)

The orchestrator is **informed and directive**. It reads the full plan, understands every phase, and writes targeted builder briefings with cross-phase context.

| Orchestrator Does | Orchestrator Does NOT |
|-------------------|----------------------|
| Read full plan + all phase files | Implement any code |
| Write targeted builder briefings with cross-phase context | Run `/code-review` directly |
| Gate-check phases (skeleton check, review check) | Invoke domain skills (builders do this) |
| Spawn/shutdown builders per group | Assign step-level tasks to builders |
| Spawn validators per phase for independent review | Validate code directly |
| Merge worktree branches and handle conflicts | |
| Run Playwright smoke checks between groups | |
| Route PASS/FAIL verdicts | |
| Update phase status in plan.md | |
| Spawn plan-level auditor and triage findings | |

## Anti-Patterns

| Pattern to Avoid | Harm When Ignored |
|------------------|-------------------|
| Skipping the full plan read | Orchestrator writes vague builder prompts, builder discovers context slowly |
| One builder per phase (old pattern) | Wastes context — the builder that built the schema should build the service |
| Skipping Playwright smoke check | Frontend wireup failures reach the user; pages stop loading |
| Skipping validator after builder | Pattern violations ship undetected |
| Builder running `/code-review` on its own code | Self-review blind spots |
| Per-group auditing (old pattern) | Auditor can't see cross-group regressions |
| More than 6 total active agents | Session instability, orchestrator overwhelmed |
| Ignoring test failures from previous phases | Broken tests pile up |
| Skipping TeamDelete after completion | Stale team directories clutter filesystem |

## Quality Layers

1. **Global PostToolUse hook** — catches CLAUDE.md violations at write time (lightweight regex checks)
2. **Builder self-verification** — `pnpm test` + `pnpm run typecheck` after each phase
3. **Validator's `/code-review`** — comprehensive, reference-grounded review with auto-fix
4. **Validator verification** (conditional) — only if code review auto-fixed files
5. **Playwright smoke check** — frontend wireup verification between groups
6. **Plan-level audit** — cross-phase regressions, deferred items, plan drift

## File Writing Rules

The Write tool **silently fails** if you haven't Read the file first.

- **Before overwriting any existing file:** Read it first, then Write
- **For modifying existing files:** prefer Edit over Write
- **In all spawn prompts:** include "IMPORTANT: Before using Write on any existing file, you MUST Read it first."

## Troubleshooting

### Builder Reports Multiple Phase Completions at Once

**Cause:** Builder implemented multiple phases without waiting for merge/validation between them.

**Fix:** Builder spawn prompt must instruct: "Report after EACH phase and wait for confirmation before continuing."

### Playwright Smoke Check Fails

**Cause:** Frontend wireup broken — missing imports, broken server components, or hydration errors.

**Fix:** Check console errors from `browser_console_messages`. Spawn a fix builder targeting the specific broken pages. Common issues: missing `'use client'` directive, broken import paths after refactoring, stale `revalidatePath` calls.

### Validator FAIL Loops

**Cause:** Builder produces code that repeatedly fails validation.

**Fix:** After 3 FAIL cycles, stop and report to user. The phase likely has structural issues needing human judgment.

### Context Compact Recovery

At 1M context, compaction is rare. If it happens:

1. `TaskList` → find `in_progress` task
2. `TaskGet` → read metadata for group and role context
3. Read plan.md Phase Table for broader progress
4. Check if team exists and has active teammates
5. Resume from the in_progress point
