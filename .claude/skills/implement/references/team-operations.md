# Team Operations Reference

Supplementary material for the `/implement` skill. This file covers teammate lifecycles, anti-pattern prevention, context compact recovery, file writing rules, and troubleshooting.

---

## Builder Teammate Lifecycle

**Builders are ephemeral.** Each phase gets a fresh builder with a clean 200K context. After a phase completes, the builder is shut down and a new one is spawned for the next phase. This prevents context contamination between phases and ensures the `builder-workflow` skill instructions are never compacted away.

Each builder follows this flow:

1. **Spawned by orchestrator** with a minimal prompt: phase file path + plan folder
2. **builder-workflow skill activates** — preloaded via the `skills:` field in builder agent config
3. **Read phase** — extract requirements, steps, acceptance criteria
4. **Pre-flight test check** — verify previous phases haven't left broken tests
5. **Find reference + invoke domain skill** — ground truth for patterns
6. **Create internal task list** — `TaskCreate` for each step, prefixed with `[Step]`. Required for context compact recovery
7. **Implement with TDD** — Step 0 first, then remaining steps sequentially. Mark each `[Step]` task `in_progress`/`completed`
8. **Final verification** — `pnpm test` + `pnpm run typecheck`
9. **Report completion** to orchestrator via SendMessage (do NOT run `/code-review` — the validator handles that independently)
10. **Shut down** when orchestrator sends shutdown_request

**Builders do NOT receive step-level tasks from the orchestrator.** The builder handles the entire phase end-to-end using its preloaded `builder-workflow` skill. The orchestrator's only job is to spawn the builder with the right phase file.

## Validator Teammate Lifecycle

**Validators are ephemeral, like builders.** Each phase gets a fresh validator spawned on-demand when its builder reports completion. Each validator is named to match its builder (`validator-1` for `builder-1`, etc.). Max 2 validators active at a time (one per builder in a batch), respecting the 4-agent total cap.

The validator follows this flow:

1. **Spawned on-demand** by the orchestrator in Step 7 when a builder reports completion
2. **Run comprehensive code review:**
   - Invoke `/code-review [phase-file-path]` — this forks a sub-agent that does reference-grounded analysis, severity-rated findings, and auto-fixes Critical/High/Medium issues
   - The code review writes a review artifact to `{plan-folder}/reviews/code/phase-{NN}.md`
3. **Run verification (only if auto-fixes were applied):**
   - If code review auto-fixed any files → run `pnpm run typecheck` + `pnpm test` to confirm fixes are clean
   - If code review found zero issues → **skip verification** (builder already passed tests + typecheck, no files changed)
4. **Report verdict** via SendMessage to orchestrator:
   - **PASS:** Code review passed, no unfixed issues, verification passed or skipped
   - **FAIL:** Specific issues with file:line references, pattern violated, exact fix needed
5. **Shut down** — orchestrator sends shutdown_request after processing the verdict

## Orchestrator Responsibilities

The orchestrator is a **thin dispatcher**. It does NOT read references, extract patterns, or implement code.

| Orchestrator Does | Orchestrator Does NOT |
|-------------------|----------------------|
| Read plan.md and find pending phases | Read reference files or extract patterns |
| Create/update tasks for phase tracking | Implement any code |
| Gate-check phases (skeleton check, review check) | Assign step-level tasks to builders |
| Spawn/shutdown builders per phase | Run `/code-review` directly |
| Spawn validators per phase for independent review | Validate code directly |
| Route PASS/FAIL verdicts | Invoke domain skills (builders do this) |
| Update phase status in plan.md + task list | |

## Patterns That Prevent User-Reported Failures

The user experienced each of these failures. Understanding the harm helps you avoid them:

| Pattern to Avoid | Harm When Ignored |
|------------------|-------------------|
| Orchestrator reading references | Consumes orchestrator context with content builders need instead |
| Orchestrator managing step-level tasks | Creates single point of failure; builders lose autonomy |
| Reusing builders across phases | Context contamination; builder-workflow instructions get compacted |
| Skipping the phase review gate | Phase has wrong patterns, builder implements wrong code |
| Skipping validator after builder | Pattern violations ship undetected |
| Reusing a single validator across parallel builders | Validation serializes — last phase waits 15-20 min for its review |
| Builder skipping reference file read | Builder guesses at patterns, code doesn't match codebase |
| Builder skipping TDD (Step 0) | Untested code, bugs discovered later |
| Builder running `/code-review` on its own code | Self-review blind spots — the author cannot objectively review their own work |
| Forgetting to update phase status | Plan becomes stale, next session confused about progress |
| Skipping TaskCreate for phase tracking | Orchestrator loses progress after context compact; no user-visible spinners |
| More than 2 builders per batch | Context pressure on orchestrator from concurrent messages |
| More than 4 total active agents (builders + validators) | Session crash, orchestrator overwhelmed |
| Spawning new builders mid-batch ("filling open slots") | Ratchet effect — agent count only goes up, never stabilises |
| Ignoring test failures from previous phases | Broken tests pile up, eventually blocking the entire plan |
| Skipping TeamDelete after completion | Stale team directories clutter filesystem |
| Polling TaskOutput instead of waiting for messages | Wastes context; teammates send messages automatically |
| Orchestrator spawning builder without phase file path | Builder has no target; builder-workflow skill can't activate properly |

## Resuming After Context Compact

### For the Orchestrator

If context was compacted mid-implementation:

1. **Run `TaskList`** — find your tasks and their status
2. **Find the `in_progress` task** — that's the phase you were working on
3. **Run `TaskGet {id}`** on that task to read full details
4. **Read plan.md** — get the Phase Table for broader context
5. **Check if a team exists:** read `~/.claude/teams/{plan-name}-impl/config.json`
   - If team exists, teammates are still active — send messages to coordinate
   - If no team, re-create it (Step 5) — validators are spawned on-demand in Step 7
6. **Check builder status** — if a builder is active for the current phase, wait for its completion message
7. **If no builder is active** — spawn a fresh builder for the current pending phase
8. **Continue the dispatch loop** from that phase

The task list is the orchestrator's primary source of truth for progress. Plan.md's Phase Table is secondary context.

### For Builders

If a builder's context is compacted mid-phase (rare, since builders are ephemeral with clean contexts):

1. `TaskList` → find the `in_progress` or first `pending` task
2. `TaskGet` on that task → read the self-contained description
3. Continue from that task — don't restart the phase
4. The task list is the builder's source of truth, not memory

## File Writing Rules (Critical for Teammates)

The Write tool **silently fails** if you haven't Read the file first. This has caused agents to generate entire documents that were never saved — wasting tokens and requiring relaunches.

**Before overwriting any existing file:**
1. **Read** the file first (even if you plan to replace all content)
2. **Then Write** the new content

**For modifying existing files, prefer Edit over Write** — Edit doesn't require a prior Read and makes targeted changes safely.

**When spawning teammates via Task tool**, always include this instruction in the prompt:
> "IMPORTANT: Before using the Write tool on any existing file, you MUST Read it first or the write will silently fail. Prefer Edit for modifying existing files."

## Troubleshooting

### Builder Produces Non-Compliant Code

**Cause:** Builder didn't follow its preloaded `builder-workflow` skill — skipped the reference file read or domain skill invocation.

**Fix:** The builder-workflow skill handles this automatically. If it's still happening, check that the builder agent config (`.claude/agents/team/builder.md`) has `skills: [builder-workflow]` in frontmatter.

### Context Compact Loses Orchestrator Progress

**Cause:** Orchestrator didn't update the Phase Table in plan.md after a phase completed.

**Fix:** Always update the Phase Table status to "Done" before shutting down the builder. On recovery, read plan.md to find the first "Pending" phase.

### Phase Review Blocks Implementation

**Cause:** Phase has Critical/High codebase compliance issues from `/review-plan`.

**Fix:** Fix the issues in the phase file first (gate check in Step 4). Fixing the plan costs 2 minutes; fixing the implementation costs 30. Re-run the review to verify fixes before spawning a builder.

### Validator FAIL Loops

**Cause:** Builder produces code that repeatedly fails validation.

**Fix:** After 3 FAIL cycles on the same phase, stop and report to the user. The phase likely has structural issues that need human judgment. Shut down the team cleanly.

### Stale Team Directories After Implementation

**Cause:** Orchestrator forgot to send `shutdown_request` to teammates and call `TeamDelete`.

**Fix:** Always follow the cleanup sequence: send `shutdown_request` to each teammate, wait for approval, then call `TeamDelete`. Check `~/.claude/teams/` for stale directories.

## Quality Layers

Quality checks execute in this order during a phase:

1. **Global PostToolUse hook** (`post_tool_use.py`) — catches common CLAUDE.md violations at write time (console.log, `any` types, missing server-only, secrets, admin client). Runs on all agents via settings.json — lightweight regex checks, non-blocking warnings.
2. **Builder self-verification** — `pnpm test` + `pnpm run typecheck` after all steps complete (builder confirms its own work compiles and tests pass)
3. **Validator's `/code-review`** — comprehensive, reference-grounded review with auto-fix (independent agent, fresh perspective, catches blind spots)
4. **Validator verification** (conditional) — `pnpm run typecheck` + `pnpm test` only if code review auto-fixed files (skipped when no changes — builder's verification still holds)

The key principle: **the builder never reviews its own code**. Layers 1-2 are self-verification (does it compile? do tests pass?). Layers 3-4 are independent review (does it follow patterns? is it correct?).

Note: The agent-specific `typescript_validator.py` PostToolUse hook was removed from builder/validator/tdd-guide/security-reviewer agents. It was a project-customisation template with all checks commented out — running on every Write/Edit for zero benefit. The global `post_tool_use.py` hook covers the important checks. When deploying to a specific project, customise `typescript_validator.py` and re-enable if needed.
