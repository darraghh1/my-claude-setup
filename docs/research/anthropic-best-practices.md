# Anthropic Best Practices

> Consolidated from Anthropic's official documentation and guides (February 2026)
>
> Sources:
>
> - `docs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf` (Anthropic, Feb 2026)
> - Claude Code Skills Documentation (`code.claude.com/docs/skills`)
> - Claude Code Subagents Documentation (`code.claude.com/docs/sub-agents`)
> - Claude Code Agent Teams Documentation (`code.claude.com/docs/agent-teams`)
> - Claude Code Memory Documentation (`code.claude.com/docs/memory`)
> - Claude Code Hooks Documentation (`code.claude.com/docs/en/hooks`)
> - Directive Compliance Framing research

---

## Document Index

This guide is split into focused reference files. Read only the file relevant to your current task.

| File | Sections | Lines | When to Read |
|------|----------|-------|-------------|
| [Skills Guide](./anthropic-skills-guide.md) | 1-18 | ~960 | Building, testing, iterating, or distributing Agent Skills |
| [Claude Code Agents](./anthropic-claude-code-agents.md) | 19-21 | ~250 | Configuring Claude Code skill extensions, subagents, or agent teams |
| [Hooks Reference](./anthropic-hooks-reference.md) | 25 | ~650 | Setting up or debugging lifecycle hooks |
| [Memory & Prompting](./anthropic-memory-and-prompting.md) | 22-24 | ~140 | Writing CLAUDE.md rules, directive framing, docs architecture |
| [Takeaways](./anthropic-takeaways.md) | 26 | ~50 | Quick-reference action checklist |

---

## Quick Navigation

### Building a Skill?

Start with the [Skills Guide](./anthropic-skills-guide.md):
- Section 5: YAML frontmatter (the #1 factor for triggering)
- Section 6: Writing effective instructions
- Section 12: Workflow patterns (5 reusable templates)
- Section 14: MCP tool usage lessons learned
- Section 16: Pre-release checklist

### Configuring Agents?

See [Claude Code Agents](./anthropic-claude-code-agents.md):
- Section 19: Claude Code-specific skill features (frontmatter fields, dynamic injection)
- Section 20: Subagent best practices (custom agents, permission modes, skill preloading)
- Section 21: Agent teams (experimental, multi-instance coordination)

### Setting Up Hooks?

See [Hooks Reference](./anthropic-hooks-reference.md):
- All 14 event types with input/output schemas
- Hook handler types (command, prompt, agent)
- Configuration structure with matcher examples
- 5 design patterns from our actual setup

### Writing CLAUDE.md or Rules?

See [Memory & Prompting](./anthropic-memory-and-prompting.md):
- Section 22: Memory hierarchy, imports, modular rules
- Section 23: Directive compliance framing (welfare-based > imperative)
- Section 24: LLM-optimized documentation principles

### Quick Reference?

See [Takeaways](./anthropic-takeaways.md):
- 33 actionable insights with source attribution
- Covers skills, agents, hooks, memory, and MCP integration
