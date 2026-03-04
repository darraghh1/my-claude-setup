# Claude Code Setup Review

**Date:** 2026-03-03
**Reviewer:** Claude Opus 4.6
**Scope:** Full configuration layer — hooks, skills, agents, rules, MCP servers, pipeline architecture

---

## Executive Summary

This is a production-grade Claude Code configuration layer built around a phased implementation pipeline (`/create-plan` → `/audit-plan` → `/review-plan` → `/implement`). The architecture is sophisticated and well-reasoned: thin dispatchers, ephemeral workers with fresh 200K context, worktree isolation for parallel builders, group-based auditing with deviation chaining, and reference-grounded reviews.

The setup's primary risk isn't architectural — it's **observability**. The system could degrade silently (hooks stop catching issues, logs fill disk, MCP servers die unnoticed) without any alerting mechanism.

### Component Inventory

| Component | Count | Notes |
|-----------|-------|-------|
| Hooks | 9 event types, 12 individual hooks | Python 3.11+, uv, zero dependencies |
| Skills | 27 | 4 pipeline, 4 workflow, 6 domain, 5 MCP wrapper, 8 utility |
| Agents | 9 | 4 team (ephemeral), 5 specialist (ad-hoc) |
| Rules | 16 | 5 always-loaded, 11 path-scoped or manually read |
| MCP Servers | 5 | Playwright, Context7, Tavily, Sequential Thinking, Draw.io |

---

## What to Leave Alone

These are load-bearing walls. They work well and shouldn't be modified without strong justification.

### 1. Thin Dispatcher Pattern

The orchestrator reads `plan.md`, spawns agents, routes messages, triages findings. It never reads reference files, never writes code, never runs reviews. This keeps it within context budget even for 15+ phase plans.

**Why it works:** The dispatcher's context window stays lean. All heavy lifting happens in ephemeral workers with fresh 200K-token windows. If the dispatcher did the work itself, it would hit compaction on large plans.

### 2. Ephemeral Workers with Fresh Context

Spawning a fresh agent per phase prevents the single biggest failure mode in long-running AI sessions: context compaction eating skill instructions. Each builder, validator, and auditor starts clean.

**Why it works:** A builder that implements Phase 12 has the same quality of instructions as the builder that implemented Phase 01. No degradation over time.

### 3. Audit-Before-Review Ordering

Running structural flow audit before per-phase reviews catches design-level issues (circular dependencies, wrong ordering) that would invalidate all review work. The bail-out on "Unusable" saves real tokens and time.

**Why it works:** Reviewing 15 phases when the dependency graph is circular is wasted work. Catching this at the structural level first (minutes, one agent) saves the cost of spawning 15+ validators.

### 4. Deviation Chaining Between Groups

Passing the previous group's deviation summary to the next group's auditor prevents compounding drift — where each group is locally correct but the system gradually diverges from the plan.

**Why it works:** Without this, you could have Group A's naming conventions, Group B's slightly different naming conventions, and Group C's third variant — all individually reviewed and approved, but collectively inconsistent.

### 5. `domain-patterns.md` as Passive Context

Based on Vercel's finding: 100% compliance with passive context vs 53-79% with on-demand skill invocation. Having compressed critical patterns always loaded means agents have a safety net even if they fail to invoke the full domain skill.

**Why it works:** Agents sometimes skip skill invocation (context pressure, compaction, oversight). The passive patterns catch the most critical violations regardless.

### 6. Config-Driven Hooks

`blocked-commands.json`, `project-checks.json`, and `quality-check-excludes.json` mean adapting to a new project requires editing JSON, not rewriting Python.

**Why it works:** Hooks are shared infrastructure. Project-specific rules change; the hook logic shouldn't have to.

### 7. Task Tracking for Compact Recovery

When compaction hits mid-phase, the agent resumes from its `in_progress` task with a self-contained description. Tasks survive compaction because they're stored externally.

**Why it works:** Without this, a compaction event mid-implementation means restarting from scratch. With it, the agent picks up exactly where it left off.

### 8. Builder Worktree Isolation

Each builder works in a separate git worktree with its own branch. `git revert` on FAIL provides clean rollback. Parallel builders can't corrupt each other's files.

**Why it works:** True parallelism requires isolation. Without worktrees, two builders editing the same file would create merge conflicts or silent overwrites.

---

## What to Change

### 1. Stop/SessionEnd Hook Overlap

**Issue:** Both `stop.py` and `session_end.py` fire at session end and both play the Clippy completion sound. Double notification on every session close.

**Recommendation:** Consolidate into one hook, or have `session_end.py` handle only end-reason logging and skip the notification (let `stop.py` own sound alerts).

**Effort:** Low (15 minutes)
**Impact:** Minor quality-of-life improvement

### 2. TeammateIdle and TaskCompleted Hooks — Currently Inert

**Issue:** Both exit 0 with a stderr warning. They log but never block. If they're not going to enforce anything, they add 10-second timeout windows to every task completion and idle event for no enforcement value.

**Recommendation:** Either:
- Make them blocking (exit 2) when a teammate has `in_progress` tasks — the original intent of a gate
- Remove them and rely on message-based coordination, which already handles this

**Effort:** Low (30 minutes)
**Impact:** Reduces hook overhead on every teammate event, or adds real enforcement

### 3. CLAUDE.md Is Still a Template

**Issue:** The project's own `CLAUDE.md` has `<!-- CUSTOMIZE -->` markers and empty sections (Commands, Architecture, Monorepo, Verification). This is the file that every session loads first. For the setup project itself, it should be concrete.

**Recommendation:** Fill in the template for this project:
- **Commands:** `uv run` for hooks, no build/test commands (it's a config repo)
- **Architecture:** Hooks → Skills → Agents pipeline, symlink deployment
- **Verification:** Hook unit tests (once added)

**Effort:** Low (30 minutes)
**Impact:** Better self-documentation when working on the setup itself

### 4. Auditor Model Inconsistency

**Issue:** `MEMORY.md` says "Opus auditor reviews the group." The agent definition (`auditor.md`) is configured as Sonnet. One source is wrong.

**Recommendation:** Verify which model the auditor actually uses and update the other. Given the auditor does cross-phase analysis with extended reasoning, Opus makes more sense — but Sonnet would be significantly cheaper since it's read-only analysis.

**Effort:** Low (10 minutes)
**Impact:** Prevents confusion when debugging auditor behavior

### 5. PostToolUse Runs Two Hooks Sequentially

**Issue:** `post_tool_use.py` and `typescript_validator.py` both fire on every Write/Edit to TypeScript files. Each independently reads stdin, parses the tool input, and checks the file content. That's redundant I/O on every write operation.

**Recommendation:** Either:
- Merge into one hook (single file read, single pass, all checks)
- Have the primary hook write structured data to a temp file for the validator to read (avoiding redundant stdin parsing)

At 10 seconds timeout each, worst case is 20 seconds of wall clock per write.

**Effort:** Medium (1-2 hours)
**Impact:** Reduces per-write latency, simplifies hook maintenance

---

## What to Add

### 1. Log Rotation / Cleanup

**Issue:** The append-only JSONL log (`hooks.jsonl`) and per-session directories (`data/logs/{session_id}/`) grow unbounded. After months of heavy use, this will accumulate hundreds of session directories and a multi-MB JSONL file.

**Recommendation:** Add a cleanup mechanism:
- Rotate `hooks.jsonl` weekly or when it exceeds 5MB
- Delete session logs older than 30 days
- Could be a `/cleanup` skill, a cron job, or a `SessionStart` hook that checks age

**Effort:** Low (1 hour)
**Impact:** Prevents silent disk usage growth

### 2. Hook Test Suite

**Issue:** Hooks are critical quality gates. If `typescript_validator.py` has a bug that causes it to silently pass all files, an entire quality layer is lost without any indication. There are no visible tests for any hook.

**Recommendation:** Add `tests/` directory with pytest tests for each hook:
- Mock stdin with known-bad inputs (file with `console.log`, file with `: any`, file with hardcoded secret)
- Assert the hook returns correct warnings in `additionalContext`
- Assert blocked commands return `deny` or `ask`
- Run as part of any PR to this repo

**Effort:** Medium (3-4 hours)
**Impact:** High — prevents silent quality gate degradation

### 3. Incremental Re-Planning (`/amend-plan`)

**Issue:** If implementation reveals that a plan needs adjustment (new phase needed, scope change, phase split), there's no formal workflow. Users must manually edit phase files or create an entirely new plan.

**Recommendation:** A `/amend-plan` skill that:
- Reads the current plan state (which phases are done, pending, in-progress)
- Lets the user add, split, remove, or reorder phases
- Re-runs flow audit on the amended plan
- Updates the Phase Table and Group Summary in plan.md
- Preserves existing review artifacts for unchanged phases

**Effort:** High (half a day)
**Impact:** Significant for long plans where mid-course corrections are common

### 4. Pipeline Metrics (`/pipeline-stats`)

**Issue:** RTK tracks token savings, but there's no visibility into pipeline health: first-pass success rate, common failure categories, which domain skills have the highest failure rate, average retry count per phase.

**Recommendation:** A `/pipeline-stats` skill that reads review artifacts (`reviews/code/`, `reviews/implementation/`) across plans and generates a summary:
- "server-action-builder phases fail validation 40% of the time due to missing `revalidatePath`" → skill needs a stronger prompt
- "Group audits find Medium issues 60% of the time" → validator isn't catching enough
- "Average retries per phase: 1.3" → baseline for improvement

**Effort:** Medium (2-3 hours)
**Impact:** Enables data-driven improvement of skills and agents

### 5. MCP Server Health Checks

**Issue:** If Context7 or Tavily goes down, agents fail with cryptic MCP errors. There's no graceful fallback or early detection.

**Recommendation:** Add a lightweight health check to `session_start.py`:
- Ping each MCP server with a trivial request (e.g., Context7: resolve "react", Tavily: search "test")
- If one is down, inject `additionalContext` warning: "Context7 is unavailable — use WebSearch as fallback for documentation queries"
- Non-blocking — don't prevent session start, just warn

**Effort:** Medium (1-2 hours)
**Impact:** Prevents wasted time debugging MCP failures mid-session

### 6. Pre-Flight Test Scoping

**Issue:** Builder pre-flight (Phase 02+) runs the full test suite to verify previous phases didn't break. On a large project, this could take minutes.

**Recommendation:** If the test runner supports it (Vitest does), run only tests related to files from previous phases:
```bash
pnpm test --related {files-from-previous-phases}
```
This makes pre-flight proportional to what changed, not the entire suite.

**Effort:** Low (30 minutes — update builder-workflow skill)
**Impact:** Reduces builder startup time on large projects

---

## Potential Over-Engineering

### 1. Sequential Thinking MCP

Claude Opus has extended thinking built in. The Sequential Thinking MCP adds structured step-by-step reasoning with `isRevision` and `branchFromThought` for explicit reasoning trees — but these features duplicate native capabilities.

**Recommendation:** Monitor actual usage via `hooks.jsonl`. If it's rarely called, consider dropping it and relying on native extended thinking. One fewer background Node process per session.

### 2. MCP Wrapper Skills (5 skills)

`context7-mcp`, `tavily-mcp`, `playwright-mcp`, `drawio-mcp`, `sequential-thinking-mcp` are skills that essentially document how to call MCP tools. But `mcp-tools.md` (always-loaded rule) already provides this as passive context.

**Recommendation:** Keep `mcp-tools.md` as the primary reference. The wrapper skills are only valuable if they contain logic beyond documentation (e.g., multi-step workflows with error handling). If they're purely documentation, they duplicate the rule.

### 3. Five MCP Servers

Tavily overlaps with built-in `WebSearch`/`WebFetch`. Draw.io is niche (diagramming). That's 5 Node processes running in the background per session.

**Recommendation:** Keep Playwright (essential for E2E interaction), Context7 (essential for up-to-date docs), and Tavily (superior to built-in for multi-source research). Evaluate whether Draw.io and Sequential Thinking earn their keep based on actual usage frequency.

---

## Subtle Issues Worth Investigating

### 1. Rule/Skill Content Overlap

`forms.md` (rule) overlaps with `react-form-builder` (skill). `testing.md` overlaps with `playwright-e2e`. `database.md` overlaps with `postgres-expert`. If they diverge (rule says one thing, skill says another), agents get conflicting instructions.

**Recommendation:** Make each rule file explicitly defer to its domain skill for detailed patterns. Audit for contradictions periodically. Rules should contain the minimum viable subset; skills should contain the authoritative reference.

### 2. Validator Model Selection

Validators run `/code-review` + tests + typecheck. This is largely mechanical: pattern matching against reference files, running commands, reporting pass/fail. Sonnet might handle this at lower cost with comparable accuracy, especially since the code-review skill itself is well-structured.

**Recommendation:** Test a few phases with Sonnet validators and compare verdict quality. If verdicts are equally reliable, the cost savings across a 15-phase plan would be significant (each validator is a full agent invocation).

### 3. Builder `bypassPermissions` Mode

Builders run with `bypassPermissions` — they can write anywhere, run any command without prompting. This is necessary for productivity (builders shouldn't prompt 50 times per phase), but it means a misbehaving builder could run destructive commands.

**Recommendation:** Verify that the `PreToolUse` hook's `blocked-commands.json` still applies to agents running in `bypassPermissions` mode. If `bypassPermissions` skips hooks entirely, the security gate is bypassed — and the worktree isolation only protects file-level damage, not command-level damage (e.g., `curl` to external services).

---

## Summary Scorecard

| Area | Rating | Key Strengths | Key Gaps |
|------|--------|---------------|----------|
| **Architecture** | Excellent | Thin dispatcher, ephemeral workers, group auditing, deviation chaining | No incremental re-planning |
| **Quality Gates** | Excellent | 5 layers, reference-grounded, config-driven, auto-fix default | No hook test suite |
| **Hooks** | Very Good | Config-driven, non-blocking logging, security gating | Overlap (stop/session_end), inert gates (idle/completed), no tests, no log rotation |
| **Skills** | Excellent | Clean separation of orchestration, workflow, domain, utility | MCP wrapper skills may be redundant with mcp-tools.md rule |
| **Agents** | Very Good | Clear role separation, worktree isolation, task recovery | Auditor model inconsistency, validators may not need Opus |
| **Rules** | Good | Passive context works well, domain-patterns.md is clever | Content overlap with domain skills needs deconfliction |
| **Observability** | Fair | Logging exists (per-session + global JSONL) | No rotation, no metrics dashboard, no MCP health checks |
| **Resilience** | Very Good | Task recovery, worktree isolation, bail-out gates | No formal re-planning, no mid-pipeline recovery skill |
| **Cost Efficiency** | Good | Ephemeral workers + RTK help | Opus validators, 5 MCP servers, redundant wrapper skills |

---

## Priority Recommendations

### Quick Wins (< 1 hour each)

1. Fix auditor model inconsistency (MEMORY.md vs agent definition)
2. Fill in CLAUDE.md for the setup project itself
3. Consolidate stop.py / session_end.py notification overlap
4. Add log rotation to session_start.py or as a standalone script

### Medium Effort (1-4 hours each)

5. Create hook test suite (pytest, mock stdin, assert warnings)
6. Merge or optimize the two PostToolUse hooks
7. Add MCP server health checks to session_start.py
8. Decide on TeammateIdle/TaskCompleted hooks (enforce or remove)
9. Test Sonnet validators on a real plan

### Larger Investments (half day+)

10. Build `/amend-plan` skill for incremental re-planning
11. Build `/pipeline-stats` skill for pipeline health metrics
12. Audit rule/skill content overlap and deconflict

---

*Report generated by Claude Opus 4.6 — 2026-03-03*
