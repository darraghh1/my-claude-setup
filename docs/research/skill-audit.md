# Skill Audit — Passive Context vs On-Demand Invocation

**Date:** 2026-02-27
**Rationale:** Vercel's evals (docs/research/vercel-skills-findings.md) showed passive context achieves 100% pass rate vs 53-79% for on-demand skill invocation. This audit categorizes all 27 skills to determine which should have critical patterns extracted into passive context.

---

## Bucket A — Workflow/Procedure (Keep As-Is)

These skills are either **invoked as the agent's first action** (agent body instructs `Skill()` call) or **explicitly user-invoked** (no auto-trigger needed). The Vercel finding doesn't apply — these don't depend on the model deciding to invoke them.

> **Note (2026-02-27):** `skills:` frontmatter does NOT preload skills — it's advisory only. Agents must invoke skills explicitly. The agent body instructions are the enforcement mechanism.

| Skill | Size | Loading Method | Why Keep |
|-------|------|----------------|----------|
| `builder-workflow` | workflow | Invoked by builder as first action via `Skill()` | Agent body instructs explicit invocation |
| `validator-workflow` | workflow | Invoked by validator as first action via `Skill()` | Agent body instructs explicit invocation |
| `auditor-workflow` | workflow | Invoked by auditor as first action via `Skill()` | Agent body instructs explicit invocation |
| `planner-workflow` | workflow | Invoked by planner as first action via `Skill()` | Agent body instructs explicit invocation |
| `code-review` | workflow | Explicitly invoked by validator | Triggered by validator-workflow, not auto-matched |
| `dev` | workflow | User-invoked via `/dev` | Entry point — user triggers explicitly |
| `create-plan` | workflow | User-invoked via `/create-plan` | Has `disable-model-invocation: true` |
| `implement` | workflow | User-invoked via `/implement` | Has `disable-model-invocation: true` |
| `review-plan` | workflow | User-invoked via `/review-plan` | Pipeline step |
| `audit-plan` | workflow | User-invoked via `/audit-plan` | Pipeline step |
| `customize` | workflow | User-invoked via `/customize` | Has `disable-model-invocation: true` |
| `improve-prompt` | workflow | User-invoked via `/improve-prompt` | Utility |
| `cache-audit` | workflow | User-invoked via `/cache-audit` | Diagnostic utility |

**Count:** 13 skills — no changes needed.

---

## Bucket B — Domain Knowledge (Extract Critical Patterns to Passive Context)

These skills contain **framework patterns and conventions** that builders need when writing code. They depend on the model recognizing "I need this" and invoking them — the exact failure mode Vercel measured (56% non-invocation rate). The `/dev` skill's routing table helps but caps at the "explicit instructions" 79% band.

### B1: Vercel Skills (Already Compressed Indexes)

These are already structured as rule indexes with one-liner descriptions. Compression to passive context is straightforward — extract the CRITICAL and HIGH priority rules.

| Skill | Size | Rules | Top Patterns for Extraction |
|-------|------|-------|-----------------------------|
| `vercel-react-best-practices` | 6KB | 57 rules, 8 categories | **CRITICAL:** async-parallel, async-suspense-boundaries, bundle-barrel-imports, bundle-dynamic-imports. **HIGH:** server-cache-react, server-parallel-fetching, server-serialization |
| `vercel-composition-patterns` | 3KB | 8 rules, 4 categories | **HIGH:** architecture-avoid-boolean-props, architecture-compound-components. **MEDIUM:** state-context-interface, patterns-explicit-variants, react19-no-forwardref |
| `vercel-react-native-skills` | 4KB | 34 rules, 8 categories | **CRITICAL:** list-performance-virtualize, list-performance-item-memo. **HIGH:** animation-gpu-properties, navigation-native-navigators, ui-expo-image |

**Compression strategy:** Extract rule names + one-liner descriptions for CRITICAL/HIGH rules. Include `ref:` pointer to full SKILL.md for deeper reading. Target: ~1.5KB total for all three.

### B2: Builder Skills (Full Code Examples — Extract Anti-Patterns + Structure Only)

These skills contain **complete code examples** that are their primary value. Compressing to one-liners would lose the patterns. Extract only: (a) the anti-pattern/harm table, (b) the file structure template, (c) the 3-5 most critical rules. Keep full SKILL.md as deep reference.

| Skill | Size | Top Patterns for Extraction |
|-------|------|-----------------------------|
| `postgres-expert` | 5KB | Anti-patterns: missing RLS, USING(true), missing account_id, missing FK indexes. Key rules: use existing helpers (has_role_on_account, has_permission), idempotent migrations (IF NOT EXISTS), CREATE INDEX CONCURRENTLY |
| `server-action-builder` | 7KB | Anti-patterns: no auth check, no Zod validation, business logic in action, missing revalidatePath. File structure: `_lib/schema/` + `_lib/server/`. Key pattern: auth → validate → service → revalidate |
| `service-builder` | 12KB | Anti-patterns: service imports createClient(), business logic in adapter, duplicated logic across interfaces. Key pattern: factory function + private class + injected client. Rule: `import 'server-only'` |
| `react-form-builder` | 9KB | Anti-patterns: missing useTransition, missing isRedirectError, external UI components. Key pattern: useForm + zodResolver + startTransition + toast.promise. Imports: always from `@/components/ui/` |
| `playwright-e2e` | 4KB | Anti-patterns: waitForTimeout, brittle CSS selectors, shared state. Key pattern: goto → waitForLoadState → interact → assert. Use data-testid + ARIA roles |

**Compression strategy:** For each skill, extract: harm table (what breaks), file structure, 3-5 critical rules as bullet points. Target: ~3KB total for all five.

### B3: Web Design Guidelines (Special Case — Fetch-Based)

| Skill | Size | Notes |
|-------|------|-------|
| `web-design-guidelines` | 1KB | Fetches guidelines from GitHub at runtime. No static content to compress. Keep as-is — it's a review tool, not a knowledge base. |

**Compression strategy:** None needed. This skill is a procedure (fetch → review → report), not knowledge.

---

## Bucket C — MCP Usage (Keep, Already Dual-Covered)

These skills explain how to use MCP servers correctly. They're already covered by `rules/mcp-tools.md` (passive context). The skills provide supplementary depth but aren't critical for correct behavior.

| Skill | Size | Passive Coverage |
|-------|------|-----------------|
| `context7-mcp` | ~1KB | `mcp-tools.md` covers resolve-first, max 3 calls, common library IDs |
| `tavily-mcp` | ~1KB | `mcp-tools.md` covers search-first, research sparingly, map before crawl |
| `playwright-mcp` | ~1KB | `mcp-tools.md` covers snapshot-before-interact, prefer snapshot over screenshot |
| `sequential-thinking-mcp` | ~1KB | `mcp-tools.md` covers when to use, isRevision, branchFromThought |
| `drawio-mcp` | ~1KB | `mcp-tools.md` covers session management |

**Count:** 5 skills — no changes needed. Already dual-covered.

---

## Summary

| Bucket | Count | Action |
|--------|-------|--------|
| A — Workflow | 13 | No changes |
| B — Domain Knowledge | 9 | Extract critical patterns to `rules/domain-patterns.md` |
| C — MCP Usage | 5 | No changes (already covered by mcp-tools.md) |
| **Total** | **27** | **9 skills contribute to passive context extraction** |

### Extraction Targets for `rules/domain-patterns.md`

| Source | Estimated Compressed Size | Content Type |
|--------|--------------------------|--------------|
| 3 Vercel skills | ~1.5KB | Rule index (name + one-liner) |
| 5 Builder skills | ~3.0KB | Anti-pattern tables + file structures + key rules |
| Retrieval instruction | ~0.1KB | "Prefer retrieval-led reasoning" header |
| Ref pointers | ~0.4KB | `ref:` links to full SKILL.md files |
| **Total** | **~5.0KB** | Well under 8KB target |
