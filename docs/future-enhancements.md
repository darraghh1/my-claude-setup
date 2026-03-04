# Future Enhancements

Items identified in the [setup review (2026-03-03)](./setup-review-2026-03-03.md) that require larger investment or further investigation before actioning.

---

## Larger Investments

### 1. `/amend-plan` Skill — Incremental Re-Planning

**Problem:** When implementation reveals that a plan needs mid-course corrections (new phase, scope change, phase split), there's no formal workflow. Users must manually edit phase files or create an entirely new plan.

**Proposed Solution:** A `/amend-plan` skill that:
- Reads current plan state (done/pending/in-progress phases)
- Supports add, split, remove, and reorder operations on phases
- Re-runs flow audit on the amended plan
- Updates Phase Table and Group Summary in plan.md
- Preserves existing review artifacts for unchanged phases

**Effort:** Half a day
**Dependencies:** None — builds on existing plan infrastructure

---

### 2. `/pipeline-stats` Skill — Pipeline Health Metrics

**Problem:** No visibility into pipeline health: first-pass success rate, common failure categories, domain skill failure rates, average retry counts.

**Proposed Solution:** A `/pipeline-stats` skill that reads review artifacts across plans:
- Parse `reviews/code/` and `reviews/implementation/` directories
- Calculate per-skill failure rates (e.g., "server-action-builder phases fail 40% due to missing revalidatePath")
- Track average retries per phase
- Identify common audit findings
- Output a summary report

**Effort:** 2-3 hours
**Dependencies:** Requires accumulated review artifacts from real pipeline runs

---

### 3. Rule/Skill Content Deconfliction Audit

**Problem:** Rules and domain skills cover overlapping territory:
- `forms.md` (rule) ↔ `react-form-builder` (skill)
- `testing.md` (rule) ↔ `playwright-e2e` (skill)
- `database.md` (rule) ↔ `postgres-expert` (skill)

If they diverge, agents get conflicting instructions.

**Proposed Solution:**
- Audit each rule/skill pair for contradictions
- Make rules explicitly defer to skills for detailed patterns
- Rules provide the minimum viable subset (passive safety net)
- Skills provide the authoritative reference (on-demand detail)

**Effort:** 2-3 hours
**Dependencies:** None

---

## Items Requiring Investigation

### 4. PostToolUse Hook Merge

**Problem:** `post_tool_use.py` and `typescript_validator.py` both fire on every Write/Edit to TypeScript files. Each independently reads stdin, parses JSON, and checks the file. Redundant I/O on every write.

**Why not actioned now:** These hooks have been carefully separated with clear ownership boundaries (checks 3, 6, 7 explicitly moved). Merging them risks reintroducing duplicate warnings or breaking the config-driven check architecture. Needs a test suite first (being built separately) to validate the merge safely.

**Approach when ready:**
- Option A: Merge into single hook (single stdin parse, single file read, combined checks)
- Option B: Have primary hook write structured data to temp file for validator to read
- Test with the hook test suite before deploying

**Effort:** 1-2 hours (after test suite exists)

---

### 5. Test Sonnet Validators

**Problem:** Validators use Opus, which is expensive. Their work is largely mechanical: pattern matching against reference files, running commands, reporting pass/fail. Sonnet might suffice.

**How to test:**
1. Pick a completed plan with 3-5 phases
2. Re-run validation on those phases using Sonnet validators
3. Compare verdict quality (same PASS/FAIL decisions? Same issue detection?)
4. If verdicts are equally reliable, switch `team/validator.md` model from `opus` to `sonnet`

**Risk:** Sonnet may miss subtle pattern violations that Opus catches. Monitor for a few plans before committing.

**Effort:** 1-2 hours of hands-on testing across real plans

---

### 6. Sequential Thinking MCP Evaluation

**Problem:** Claude Opus has native extended thinking. Sequential Thinking MCP adds structured step-by-step reasoning with `isRevision` and `branchFromThought`, but may duplicate native capabilities.

**How to evaluate:**
1. Grep `hooks.jsonl` for `mcp__sequential-thinking__` calls
2. Count frequency over last 30 days
3. If rarely used (<5 calls/month), consider removing
4. If frequently used, check if the branching/revision features are actually leveraged

**Command:**
```bash
grep -c "sequential-thinking" .claude/hooks/logs/hooks.jsonl
```

**Effort:** 15 minutes to evaluate, 5 minutes to remove if warranted

---

### 7. MCP Wrapper Skill Consolidation

**Problem:** Five wrapper skills (`context7-mcp`, `tavily-mcp`, `playwright-mcp`, `drawio-mcp`, `sequential-thinking-mcp`) essentially document how to call MCP tools. The `mcp-tools.md` rule already provides this as passive context.

**Decision criteria:**
- If a wrapper skill contains **logic beyond documentation** (multi-step workflows, error handling, retry logic) → keep it
- If it's **purely documentation** → it duplicates `mcp-tools.md` and can be removed

**Approach:** Review each wrapper skill's SKILL.md. If it only contains "use these tools like this," the rule already handles it. Remove and update `mcp-tools.md` if needed.

**Effort:** 1 hour

---

### 8. Builder `bypassPermissions` and Hook Interaction

**Problem:** Builders run with `bypassPermissions` mode. Need to verify that `PreToolUse` hook's `blocked-commands.json` still applies. If `bypassPermissions` skips hooks, the security gate is bypassed.

**How to verify:**
1. Spawn a builder in a test worktree
2. Have it attempt a blocked command (e.g., `git push --force`)
3. Check if the PreToolUse hook fires and blocks it

**Risk:** If hooks don't fire for `bypassPermissions` agents, destructive commands could execute unchecked. Worktree isolation limits blast radius but doesn't eliminate risk.

**Effort:** 30 minutes to test

---

### 9. Pre-Flight Test Scoping

**Problem:** Builder pre-flight (Phase 02+) runs the full test suite. On large projects this adds minutes to every builder spawn.

**Proposed Solution:** Use Vitest's `--related` flag:
```bash
pnpm test --related {files-from-previous-phases}
```

**Where to change:** `builder-workflow/SKILL.md` Step 3 (pre-flight check)

**Risk:** `--related` may miss indirect test dependencies. Start by running both full and scoped in parallel and comparing results.

**Effort:** 30 minutes to update skill, needs validation on real project

---

### 10. Draw.io MCP Evaluation

**Problem:** Draw.io MCP runs a Node process per session for diagramming — a niche use case.

**How to evaluate:** Same as Sequential Thinking — grep `hooks.jsonl` for usage frequency.

**Effort:** 15 minutes

---

## Items Confirmed Not Issues

### Auditor Model Inconsistency

**Original concern:** MEMORY.md says "Opus auditor" but agent definition might say Sonnet.

**Resolution:** `auditor.md` line 21 confirms `model: opus`. MEMORY.md is correct. The explore agent misread it. **No action needed.**

---

*Last updated: 2026-03-03*
