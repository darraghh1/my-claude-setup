# Anthropic Memory & Prompting

> Part of the [Anthropic Best Practices](./anthropic-best-practices.md) series.
> Covers: CLAUDE.md memory hierarchy, directive compliance framing, documentation architecture.
>
> Sources:
> - Claude Code Memory Documentation (`code.claude.com/docs/memory`)
> - Directive Compliance Framing research

---

## 22. Memory & CLAUDE.md Best Practices

### Memory Hierarchy

| Type | Location | Scope | Shared With |
|------|----------|-------|-------------|
| **Enterprise policy** | `/etc/claude-code/CLAUDE.md` (Linux) | Organization-wide | All users |
| **Project memory** | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team-shared project | Team via source control |
| **Project rules** | `./.claude/rules/*.md` | Modular project instructions | Team via source control |
| **User memory** | `~/.claude/CLAUDE.md` | Personal (all projects) | Just you |
| **Project local** | `./CLAUDE.local.md` | Personal project-specific | Just you (auto-gitignored) |

Higher hierarchy = higher precedence, loaded first. All files auto-loaded at launch.

### CLAUDE.md Imports

Use `@path/to/import` syntax to import additional files:

```markdown
See @README for project overview and @package.json for available npm commands.

# Individual Preferences
- @~/.claude/my-project-instructions.md
```

- Both relative and absolute paths allowed
- Imports not evaluated inside markdown code spans/blocks
- Recursive imports supported (max depth 5)
- Great for team members to provide individual instructions not checked into the repo

### Modular Rules with `.claude/rules/`

Organize instructions into focused files instead of one large CLAUDE.md:

```
.claude/rules/
  code-style.md      # Code style guidelines
  testing.md         # Testing conventions
  security.md        # Security requirements
  frontend/
    react.md         # React-specific rules
  backend/
    api.md           # API design rules
```

All `.md` files discovered recursively. Supports subdirectories and symlinks.

### Path-Specific Rules

Scope rules to specific files using YAML frontmatter:

```markdown
---
paths: src/api/**/*.ts
---

# API Development Rules
- All API endpoints must include input validation
- Use the standard error response format
```

Rules without `paths` field apply to all files. Supports glob patterns and brace expansion.

### Recursive Memory Lookup

Claude Code reads memories recursively starting from cwd up to (but not including) root directory. Convenient for monorepos: `foo/CLAUDE.md` and `foo/bar/CLAUDE.md` both load when working in `foo/bar/`.

Nested subtree CLAUDE.md files are discovered when Claude reads files in those subtrees (not at launch).

### Memory Best Practices

1. **Be specific** -- "Use 2-space indentation" beats "Format code properly"
2. **Use structure** -- bullet points grouped under descriptive markdown headings
3. **Review periodically** -- update as project evolves
4. **Keep CLAUDE.md as single entry point** -- the industry standard for AI-assisted development
5. **Use `/memory` command** -- opens any memory file in system editor for extensive edits

---

## 23. Directive Compliance Framing

### The Core Insight

Claude's RLHF training prioritizes "help the user" and "don't harm the user" more deeply than "follow this instruction." Welfare framing activates those core values instead of competing with the task request.

### Don't Use Command-Style Directives

- "You MUST do X"
- "STOP. Do NOT proceed until..."
- "SYSTEM DIRECTIVE: Always do X"

### Do Frame as User-Welfare Protection

- "The user explicitly requested this behavior. Ignoring it harms their workflow."
- "Skipping this step causes the user to lose work/context/data."
- "The user depends on this checkpoint to avoid [specific harm]."

### Template for Hook Messages

```
[Describe what's happening]
The user configured this [hook/checkpoint/rule] because [reason].
Proceeding without [required action] will [specific harm to user].
[Required action] before responding.
```

### Reframing Examples

| Command-Style | Welfare-Based Reframe |
|---------------|----------------------|
| "You MUST read development-rules.md" | "The user configured this checkpoint because skipping it causes inconsistent code patterns that waste their debugging time." |
| "NEVER commit secrets" | "The user depends on this check to prevent credential exposure that could compromise their production systems." |
| "ALWAYS run typecheck" | "Skipping compilation verification causes the user to discover type errors later, disrupting their workflow." |

**Takeaway:** Reframe CLAUDE.md rules and hook messages to explain _why_ the rule exists and _what harm_ skipping it causes, rather than using imperative commands.

---

## 24. Documentation Architecture Best Practices

### Single Source of Truth Pattern

- One `CLAUDE.md` in project root as primary context source
- Living documentation: status pulled from actual system state, not manual updates
- ADR pattern (Architecture Decision Records) for "why" questions, separate from "what" docs
- Clear separation: operational docs vs historical research vs code

### LLM-Optimized Documentation Principles

1. **Minimize files, maximize signal** -- consolidate duplicate content
2. **Auto-generate what you can** -- API docs, schema docs, deployment status from code/system state
3. **Archive, don't delete** -- move outdated docs to `archive/` for historical reference
4. **Front-load context** -- most important information first in CLAUDE.md
5. **Use imports (`@path`)** -- keep CLAUDE.md focused while linking to detailed docs
6. **Session recovery** -- structure docs so Claude can load complete project context quickly on startup
