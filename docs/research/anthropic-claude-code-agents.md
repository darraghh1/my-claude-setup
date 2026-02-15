# Anthropic Claude Code Agents

> Part of the [Anthropic Best Practices](./anthropic-best-practices.md) series.
> Covers: Claude Code skill extensions, subagents, and agent teams.
>
> Sources:
> - Claude Code Skills Documentation (`code.claude.com/docs/skills`)
> - Claude Code Subagents Documentation (`code.claude.com/docs/sub-agents`)
> - Claude Code Agent Teams Documentation (`code.claude.com/docs/agent-teams`)

---

## 19. Claude Code-Specific Skill Features

The PDF covers the open Agent Skills standard. Claude Code extends the standard with additional features.

### Additional Frontmatter Fields (Claude Code Only)

| Field | Purpose | Example |
|-------|---------|---------|
| `disable-model-invocation` | Set `true` to prevent Claude from auto-loading. User-only via `/name`. Use for workflows with side effects (deploy, commit). | `disable-model-invocation: true` |
| `user-invocable` | Set `false` to hide from `/` menu. Use for background knowledge Claude should know but users shouldn't invoke directly. | `user-invocable: false` |
| `argument-hint` | Hint shown during autocomplete. | `argument-hint: [issue-number]` |
| `model` | Model to use when skill is active. | `model: haiku` |
| `context` | Set to `fork` to run in a forked subagent context. | `context: fork` |
| `agent` | Which subagent type to use when `context: fork` is set. | `agent: Explore` |
| `hooks` | Hooks scoped to this skill's lifecycle. | See [hooks reference](./anthropic-hooks-reference.md) |

### Invocation Control Matrix

| Frontmatter | You Can Invoke | Claude Can Invoke | When Loaded Into Context |
|-------------|---------------|-------------------|--------------------------|
| (default) | Yes | Yes | Description always in context, full skill loads when invoked |
| `disable-model-invocation: true` | Yes | No | Description NOT in context, full skill loads when you invoke |
| `user-invocable: false` | No | Yes | Description always in context, full skill loads when invoked |

### String Substitutions

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking. If not in content, appended as `ARGUMENTS: <value>` |
| `$ARGUMENTS[N]` or `$N` | Access specific argument by 0-based index |
| `${CLAUDE_SESSION_ID}` | Current session ID (useful for logging, session-specific files) |

### Dynamic Context Injection

The `` !`command` `` syntax runs shell commands before the skill content is sent to Claude. Output replaces the placeholder.

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
allowed-tools: Bash(gh *)
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
```

This is preprocessing -- Claude only sees the final rendered result.

### Extended Thinking in Skills

Include the word "ultrathink" anywhere in skill content to enable extended thinking.

### Skill Context Budget

Default character budget for skill descriptions loaded into context: 15,000 characters. If you have many skills, some may be excluded. Check with `/context` for warnings. Override with `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable.

### Skill Location Priority

| Location | Applies To | Priority |
|----------|-----------|----------|
| Enterprise | All users in organization | Highest |
| Personal (`~/.claude/skills/`) | All your projects | High |
| Project (`.claude/skills/`) | This project only | Medium |
| Plugin | Where plugin is enabled | Lowest |

Same-name skills: higher priority location wins. Plugin skills use `plugin-name:skill-name` namespace (no conflicts).

### Monorepo Auto-Discovery

When editing files in subdirectories, Claude Code auto-discovers skills from nested `.claude/skills/` directories. E.g., editing in `packages/frontend/` also picks up `packages/frontend/.claude/skills/`.

### Tighter Size Guidance (Claude Code Docs)

Keep `SKILL.md` under **500 lines** (tighter than the PDF's 5,000 words). Move detailed reference material to separate files.

---

## 20. Subagents Best Practices

Subagents are specialized AI assistants that handle specific tasks in their own context window.

### Why Use Subagents

- **Preserve context** -- keep exploration/implementation out of main conversation
- **Enforce constraints** -- limit which tools a subagent can use
- **Reuse configurations** -- user-level subagents available in all projects
- **Specialize behavior** -- focused system prompts for specific domains
- **Control costs** -- route tasks to faster, cheaper models like Haiku

### Built-In Subagents

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **Explore** | Haiku (fast) | Read-only | File discovery, code search, codebase exploration |
| **Plan** | Inherits | Read-only | Codebase research for planning (used in plan mode) |
| **general-purpose** | Inherits | All tools | Complex research, multi-step operations, code modifications |

### Custom Subagent Configuration

```markdown
---
name: code-reviewer
description: Expert code review specialist. Use proactively after code changes.
tools: Read, Glob, Grep, Bash
model: sonnet
---

You are a senior code reviewer. When invoked:
1. Run git diff to see recent changes
2. Focus on modified files
3. Begin review immediately
...
```

### Subagent Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier (lowercase letters and hyphens) |
| `description` | Yes | When Claude should delegate to this subagent |
| `tools` | No | Tools the subagent can use (inherits all if omitted) |
| `disallowedTools` | No | Tools to deny (removed from inherited list) |
| `model` | No | `sonnet`, `opus`, `haiku`, or `inherit` (default: `inherit`) |
| `permissionMode` | No | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `skills` | No | Skills to preload into subagent context at startup |
| `hooks` | No | Lifecycle hooks scoped to this subagent |

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Standard permission checking with prompts |
| `acceptEdits` | Auto-accept file edits |
| `dontAsk` | Auto-deny prompts (explicitly allowed tools still work) |
| `bypassPermissions` | Skip all permission checks (use with caution) |
| `plan` | Read-only exploration |

### Subagent Scope Priority

| Location | Scope | Priority |
|----------|-------|----------|
| `--agents` CLI flag | Current session | 1 (highest) |
| `.claude/agents/` | Current project | 2 |
| `~/.claude/agents/` | All your projects | 3 |
| Plugin's `agents/` | Where plugin is enabled | 4 (lowest) |

### Key Design Principles

1. **Design focused subagents** -- each should excel at one specific task
2. **Write detailed descriptions** -- Claude uses this to decide when to delegate
3. **Limit tool access** -- grant only necessary permissions
4. **Check into version control** -- share project subagents with your team
5. **Include "use proactively" in description** -- encourages Claude to delegate without being asked

### When to Use Subagents vs Main Conversation

| Use Main Conversation | Use Subagents |
|----------------------|---------------|
| Frequent back-and-forth or iterative refinement | Task produces verbose output you don't need in main context |
| Multiple phases share significant context | You want to enforce specific tool restrictions |
| Quick, targeted change | Work is self-contained and can return a summary |
| Latency matters (subagents start fresh) | |

### Subagents Cannot Spawn Other Subagents

If workflow requires nested delegation, use skills or chain subagents from the main conversation.

### Preloading Skills into Subagents

```yaml
---
name: api-developer
description: Implement API endpoints following team conventions
skills:
  - api-conventions
  - error-handling-patterns
---

Implement API endpoints. Follow the conventions from the preloaded skills.
```

Full skill content is injected into subagent context (not just made available for invocation). Subagents don't inherit skills from the parent conversation.

---

## 21. Agent Teams Best Practices

Agent teams coordinate multiple Claude Code instances working together. Experimental feature (requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

### Teams vs Subagents

| | Subagents | Agent Teams |
|-|-----------|-------------|
| **Context** | Own context; results return to caller | Own context; fully independent |
| **Communication** | Report back to main agent only | Teammates message each other directly |
| **Coordination** | Main agent manages all work | Shared task list with self-coordination |
| **Best for** | Focused tasks where only result matters | Complex work requiring discussion and collaboration |
| **Token cost** | Lower (results summarized back) | Higher (each teammate is a separate Claude instance) |

### When to Use Teams

- Research and review (multiple angles simultaneously)
- New modules or features (teammates own separate pieces)
- Debugging with competing hypotheses (parallel investigation)
- Cross-layer coordination (frontend, backend, tests each owned separately)

### Team Architecture

| Component | Role |
|-----------|------|
| **Team lead** | Creates team, spawns teammates, coordinates work |
| **Teammates** | Separate Claude Code instances working on assigned tasks |
| **Task list** | Shared work items that teammates claim and complete |
| **Mailbox** | Messaging system for inter-agent communication |

### Key Best Practices

1. **Give teammates enough context** -- they don't inherit lead's conversation history. Include task-specific details in spawn prompt.
2. **Size tasks appropriately** -- too small = coordination overhead exceeds benefit; too large = teammates work too long without check-ins. Target: self-contained units producing a clear deliverable.
3. **5-6 tasks per teammate** -- keeps everyone productive and lets lead reassign if someone gets stuck.
4. **Avoid file conflicts** -- two teammates editing the same file leads to overwrites. Each teammate should own different files.
5. **Start with research and review** -- clear boundaries, no code coordination challenges. Good first use case for teams.
6. **Monitor and steer** -- don't let teams run unattended too long.
7. **Use delegate mode** -- press Shift+Tab to restrict lead to coordination-only tools (prevents lead from implementing instead of delegating).

### Current Limitations

- No session resumption with in-process teammates
- Task status can lag (teammates may not mark tasks complete)
- One team per session
- No nested teams (teammates can't spawn their own teams)
- Lead is fixed for team lifetime
- Split panes require tmux or iTerm2
