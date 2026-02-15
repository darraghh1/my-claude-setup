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
6. **Create internal task list** — survive context compacts within the phase
7. **Implement with TDD** — Step 0 first, then remaining steps sequentially
8. **Final verification** — `pnpm test` + `pnpm run typecheck`
9. **Run `/code-review`** — fix Critical/High/Medium issues
10. **Report completion** to orchestrator via SendMessage
11. **Shut down** when orchestrator sends shutdown_request

**Builders do NOT receive step-level tasks from the orchestrator.** The builder handles the entire phase end-to-end using its preloaded `builder-workflow` skill. The orchestrator's only job is to spawn the builder with the right phase file.

## Validator Teammate Lifecycle

**The validator is persistent across phases.** Unlike builders (which are ephemeral per-phase), a single validator is spawned once and reused for all phase validations.

The validator follows this flow:

1. **Spawned once** by the orchestrator during the first phase
2. **Receives validation assignment** from orchestrator after a builder reports completion
3. **Verify work:**
   a. Files listed in the phase's Implementation Steps were created/modified
   b. Code matches codebase patterns (find a reference file, compare)
   c. Code quality: no console.log, no `any` types, server files have `import 'server-only'`
   d. Run typecheck: `pnpm run typecheck`
   e. Run full test suite: `pnpm test` — report FAIL if any test fails
4. **Report verdict** via SendMessage to orchestrator:
   - **PASS:** Brief summary of what was verified
   - **FAIL:** Specific issues with file:line references, pattern violated, exact fix needed
5. **Go idle** — wait for next validation assignment (next phase)

## Orchestrator Responsibilities

The orchestrator is a **thin dispatcher**. It does NOT read references, extract patterns, or implement code.

| Orchestrator Does | Orchestrator Does NOT |
|-------------------|----------------------|
| Read plan.md and find pending phases | Read reference files or extract patterns |
| Gate-check phases (skeleton check, review check) | Implement any code |
| Spawn/shutdown builders per phase | Assign step-level tasks to builders |
| Send validation assignments to validator | Validate code directly |
| Route PASS/FAIL verdicts | Run `/code-review` (builders do this) |
| Update phase status in plan.md | Invoke domain skills (builders do this) |

## Patterns That Prevent User-Reported Failures

The user experienced each of these failures. Understanding the harm helps you avoid them:

| Pattern to Avoid | Harm When Ignored |
|------------------|-------------------|
| Orchestrator reading references | Consumes orchestrator context with content builders need instead |
| Orchestrator managing step-level tasks | Creates single point of failure; builders lose autonomy |
| Reusing builders across phases | Context contamination; builder-workflow instructions get compacted |
| Skipping the phase review gate | Phase has wrong patterns, builder implements wrong code |
| Skipping validator after builder | Pattern violations ship undetected |
| Builder skipping reference file read | Builder guesses at patterns, code doesn't match codebase |
| Builder skipping TDD (Step 0) | Untested code, bugs discovered later |
| Builder self-reviewing instead of `/code-review` | Blind spots missed |
| Forgetting to update phase status | Plan becomes stale, next session confused about progress |
| More than 2-3 builders at once | Context pressure on orchestrator from concurrent messages |
| Ignoring test failures from previous phases | Broken tests pile up, eventually blocking the entire plan |
| Skipping TeamDelete after completion | Stale team directories clutter filesystem |
| Polling TaskOutput instead of waiting for messages | Wastes context; teammates send messages automatically |
| Orchestrator spawning builder without phase file path | Builder has no target; builder-workflow skill can't activate properly |

## Resuming After Context Compact

### For the Orchestrator

If context was compacted mid-implementation:

1. **Read plan.md** — find the Phase Table, identify the first "Pending" phase
2. **Check if a team exists:** read `~/.claude/teams/{plan-name}-impl/config.json`
   - If team exists, teammates are still active — send messages to coordinate
   - If no team, re-create it and re-spawn the validator
3. **Check builder status** — if a builder is active for the current phase, wait for its completion message
4. **If no builder is active** — spawn a fresh builder for the current pending phase
5. **Continue the dispatch loop** from that phase

The plan.md Phase Table is the orchestrator's source of truth for progress.

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

1. **PostToolUse hook** (`typescript_validator.py`) — catches issues at write time (fastest feedback, runs on builder)
2. **Builder's `/code-review`** — comprehensive review after all steps complete (runs within builder context)
3. **Validator teammate** — independent verification after builder reports done (catches pattern deviations the builder missed)
