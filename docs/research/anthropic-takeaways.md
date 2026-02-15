# Anthropic Consolidated Takeaways

> Part of the [Anthropic Best Practices](./anthropic-best-practices.md) series.
> Quick-reference action table across all topics.

---

## Consolidated Takeaways for DigitalMastery

| # | Insight | Action | Source |
|---|---------|--------|--------|
| 1 | Description field is the #1 factor for skill triggering | Audit all skill descriptions against `[What] + [When] + [Capabilities]` formula | PDF |
| 2 | Progressive disclosure saves tokens | Move detailed docs from SKILL.md to `references/` | PDF |
| 3 | Negative triggers prevent overtriggering | Add "Do NOT use for..." to overlapping skills | PDF |
| 4 | Validation scripts beat language instructions | Use `scripts/` for critical checks, not prose | PDF |
| 5 | Keep SKILL.md under 500 lines | Audit current skills for bloat | Claude Code Docs |
| 6 | `disable-model-invocation: true` for dangerous skills | Apply to deploy, commit, and destructive workflow skills | Claude Code Docs |
| 7 | `allowed-tools` restricts tool access | Use on read-only skills (review, research) | Both |
| 8 | Subagents: one task, limited tools | Design focused agents that excel at one thing | Subagents Docs |
| 9 | Preload skills into subagents | Use `skills` field to inject domain knowledge at startup | Subagents Docs |
| 10 | Agent teams for parallel research | Use for competing hypotheses, multi-angle review | Teams Docs |
| 11 | Welfare-framing > command directives | Reframe CLAUDE.md rules to explain harm of non-compliance | Directive Research |
| 12 | `.claude/rules/` with path-specific rules | Scope rules to file patterns for targeted guidance | Memory Docs |
| 13 | CLAUDE.md imports with `@path` | Link to detailed docs without bloating main file | Memory Docs |
| 14 | Performance encouragement in user prompt > system prompt | "Take your time", "Quality over speed" | PDF |
| 15 | In-context learning workflow | Perfect a workflow in conversation first, then codify as skill | PDF |
| 16 | Dynamic context injection (`` !`command` ``) | Pre-populate skill content with live data (git, gh, etc.) | Claude Code Docs |
| 17 | "ultrathink" keyword | Enable extended thinking in skills that need deep analysis | Claude Code Docs |
| 18 | Test with 10-20 queries for trigger accuracy | Build should-trigger + should-NOT-trigger test suites | PDF |
| 19 | Organization-level deployment | Deploy skills workspace-wide with automatic updates | PDF + Docs |
| 20 | Single source of truth documentation | Keep CLAUDE.md as primary entry point, use imports for detail | Documentation Research |
| 21 | Claude tries to shell out MCP tools via Bash | Show explicit CORRECT (direct tool call) vs WRONG (`claude mcp call`) examples | MCP Testing |
| 22 | Skills alone don't create habits | Put habitual tool nudges in `.claude/rules/`, workflow guidance in skills | MCP Testing |
| 23 | MCP tools can flood context with large payloads | Document output sizes and targeted alternatives for every large-output tool | MCP Testing |
| 24 | MCP tools have coverage gaps | Test edge cases, document fallback paths (what to do when tool returns "not found") | MCP Testing |
| 25 | Claude defaults to sequential MCP calls | Explicitly mark independent tools as parallelizable in skill instructions | MCP Testing |
| 26 | PreToolUse `updatedInput` can silently rewrite tool args | Use to add safety flags (`--bail`), fix paths, or enforce conventions before execution | Hooks Docs |
| 27 | Stop hook needs `stop_hook_active` guard | Without it, Stop -> block -> respond -> Stop creates infinite loops | Hooks Docs |
| 28 | `additionalContext` is injected as `<system-reminder>` | Claude sees it but won't explicitly reference it -- frame as guidance, not commands | Hooks Docs |
| 29 | Async hooks (`"async": true`) can't block | Use sync hooks for quality gates, async for telemetry/logging -- zero latency impact | Hooks Docs |
| 30 | PostToolUse `updatedMCPToolOutput` replaces MCP responses | Redact sensitive data or trim large outputs before Claude processes them (MCP tools only) | Hooks Docs |
| 31 | Welfare framing in hook block messages | Hook reasons that explain *harm of skipping* are followed more reliably than imperative commands | Hooks + Directive Research |
| 32 | SubagentStart `additionalContext` injects rules into subagents | Subagents don't inherit CLAUDE.md -- use this hook to inject project conventions | Hooks Docs |
| 33 | TeammateIdle + TaskCompleted are team quality gates | Block with exit code 2 to prevent premature idling or incomplete task completion | Hooks Docs |
