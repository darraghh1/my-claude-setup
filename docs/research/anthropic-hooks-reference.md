# Anthropic Hooks Reference

> Part of the [Anthropic Best Practices](./anthropic-best-practices.md) series.
> Covers: All 14 hook event types, input/output schemas, configuration, and design patterns.
>
> Sources:
> - Claude Code Hooks Reference (`code.claude.com/docs/en/hooks`)
> - Claude Code Hooks Guide (`code.claude.com/docs/en/hooks-guide`)

---

## 25. Hooks -- Lifecycle Events & Context Injection

Hooks are shell commands (or LLM prompts) that fire at specific lifecycle events. They let you observe, block, modify, or inject context into Claude's behavior -- without changing the model itself.

### Architecture

```
  User prompt -> [UserPromptSubmit] -> Claude thinks -> [PreToolUse] -> Permission check
       |                                                  |
  [SessionStart]                                   [PermissionRequest]
                                                          |
                                               Tool executes (or blocked)
                                                          |
                                                   [PostToolUse] or [PostToolUseFailure]
                                                          |
                                               Claude responds -> [Stop]
                                                          |
                                               [Notification] (if idle/permission)
                                                          |
                                               [SessionEnd] (on exit)
```

Subagent lifecycle: `[SubagentStart]` -> subagent works -> `[SubagentStop]`
Team lifecycle: teammate works -> `[TeammateIdle]` / `[TaskCompleted]`
Context management: `[PreCompact]` -> compaction occurs

### Hook Handler Types

Three types of handler can be attached to any event:

| Type | What It Does | Best For |
|------|-------------|----------|
| `command` | Runs a shell command, reads stdin JSON, writes stdout JSON | Scripts, telemetry, file operations |
| `prompt` | Sends input to an LLM for a single response | Quick analysis, classification |
| `agent` | Sends input to an agentic LLM that can use tools | Complex validation, multi-step checks |

```json
{
  "type": "command",
  "command": "python hooks/my_hook.py",
  "async": false,
  "timeout": 600,
  "statusMessage": "Running quality check...",
  "once": false
}
```

| Handler Field | Type | Description |
|---------------|------|-------------|
| `type` | `"command" \| "prompt" \| "agent"` | Required. Handler type |
| `command` | `string` | Required for `command` type. Shell command to run |
| `prompt` | `string` | Required for `prompt`/`agent` types. Use `$ARGUMENTS` for input |
| `model` | `string?` | For `prompt`/`agent`. Model to use (default: inherit) |
| `async` | `boolean?` | `command` only. Run in background without blocking |
| `timeout` | `number?` | Seconds before timeout (default varies by type) |
| `statusMessage` | `string?` | Custom spinner text while hook runs |
| `once` | `boolean?` | Run only once per session |

### Exit Code Protocol

| Exit Code | Meaning | Effect |
|-----------|---------|--------|
| `0` | Success / Allow | JSON on stdout parsed for decisions |
| `2` | Block | stderr message fed back to Claude or shown to user |
| Other | Non-blocking error | stderr shown in verbose mode only |

### Common Input Fields (All Events)

Every hook receives these on stdin as JSON:

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `string` | Current session identifier |
| `transcript_path` | `string` | Path to conversation transcript JSON |
| `cwd` | `string` | Current working directory |
| `permission_mode` | `string` | `default`, `plan`, `acceptEdits`, `dontAsk`, `bypassPermissions` |
| `hook_event_name` | `string` | Name of the event that fired |

### Universal Output Fields (All Events)

Any hook can return these in the stdout JSON:

| Field | Type | Description |
|-------|------|-------------|
| `continue` | `boolean?` | `false` = Claude stops the entire session |
| `stopReason` | `string?` | Message shown when `continue=false` |
| `suppressOutput` | `boolean?` | Hide stdout from verbose mode |
| `systemMessage` | `string?` | Warning message surfaced to the user |

---

### Event Reference

#### 1. SessionStart

**When:** Session begins, resumes, clears, or compacts.
**Matcher values:** `startup`, `resume`, `clear`, `compact`
**Can block:** No

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `source` | `"startup" \| "resume" \| "clear" \| "compact"` | What triggered the session |
| `model` | `string` | Active model identifier |
| `agent_type` | `string?` | Present if started with `--agent` flag |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Inject context | `hookSpecificOutput.additionalContext` | Text added to Claude's system context |
| Set env vars | Write `export VAR=value` to `$CLAUDE_ENV_FILE` | Persisted for subsequent Bash tool calls |

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Project is on sprint 14. Focus area: payments."
  }
}
```

---

#### 2. UserPromptSubmit

**When:** User submits a prompt, before Claude processes it.
**Matcher:** None
**Can block:** Yes (exit 2, or `decision: "block"` in output)

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | `string` | The full text the user submitted |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Block prompt | `"decision": "block"` + `"reason"` | Prompt rejected, reason shown to user |
| Inject context | `hookSpecificOutput.additionalContext` | Text added to Claude's context alongside the prompt |

```json
{
  "decision": "block",
  "reason": "Prompt contains production database credentials. Remove them before submitting.",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "User's last prompt was blocked for containing secrets."
  }
}
```

**Use cases:** Secret scanning, prompt transformation, injecting project state.

---

#### 3. PreToolUse

**When:** Before a tool executes (before permission check).
**Matcher:** Tool name regex -- `Bash`, `Edit`, `Write`, `Read`, `Glob`, `Grep`, `Task`, `WebFetch`, `WebSearch`, `mcp__server__tool`
**Can block:** Yes (via `permissionDecision: "deny"`)

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `tool_name` | `string` | Tool being called |
| `tool_input` | `object` | Tool-specific arguments (see below) |
| `tool_use_id` | `string` | Unique ID for this tool invocation |

**Tool-specific `tool_input` shapes:**

| Tool | Key Fields |
|------|-----------|
| **Bash** | `command`, `description?`, `timeout?`, `run_in_background?` |
| **Write** | `file_path`, `content` |
| **Edit** | `file_path`, `old_string`, `new_string`, `replace_all?` |
| **Read** | `file_path`, `offset?`, `limit?` |
| **Glob** | `pattern`, `path?` |
| **Grep** | `pattern`, `path?`, `glob?`, `output_mode?`, `-i?`, `multiline?` |
| **WebFetch** | `url`, `prompt` |
| **WebSearch** | `query`, `allowed_domains?`, `blocked_domains?` |
| **Task** | `prompt`, `description`, `subagent_type`, `model?` |
| **MCP tools** | Varies by MCP server/tool definition |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Auto-allow | `permissionDecision: "allow"` | Bypasses permission prompt |
| Auto-deny | `permissionDecision: "deny"` | Blocks tool call, reason fed back to Claude |
| Force prompt | `permissionDecision: "ask"` | Shows permission dialog regardless of settings |
| Modify args | `updatedInput: { ... }` | Replaces tool_input before execution |
| Inject context | `additionalContext` | Text added to Claude's context |

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Cannot write to production config files.",
    "updatedInput": null,
    "additionalContext": "Tool call was blocked by project policy."
  }
}
```

**Use cases:** Auto-approve safe operations, block dangerous commands, rewrite file paths, inject warnings.

---

#### 4. PermissionRequest

**When:** A permission dialog is about to be shown to the user.
**Matcher:** Tool name regex (same as PreToolUse)
**Can block:** Yes (via `decision.behavior: "deny"`)

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `tool_name` | `string` | Tool requesting permission |
| `tool_input` | `object` | Same tool-specific shapes as PreToolUse |
| `permission_suggestions` | `array?` | Suggested "always allow" rules |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Auto-allow | `decision.behavior: "allow"` | Skips the permission dialog |
| Auto-deny | `decision.behavior: "deny"` + `decision.message` | Denies without prompting |
| Modify args | `decision.updatedInput: { ... }` | Changes tool args (allow only) |
| Update rules | `decision.updatedPermissions: { ... }` | Adjusts permission rules (allow only) |
| Interrupt | `interrupt: true` | Stops Claude entirely (deny only) |

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": { "command": "npm test -- --bail" },
      "updatedPermissions": {}
    },
    "interrupt": false
  }
}
```

**Use cases:** Auto-approve CI-safe commands, enforce org policies, add safety flags to commands.

---

#### 5. PostToolUse

**When:** After a tool executes successfully.
**Matcher:** Tool name regex
**Can block:** Yes (via `decision: "block"` -- doesn't undo the tool, but tells Claude to address the issue)

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `tool_name` | `string` | Tool that ran |
| `tool_input` | `object` | Args it was called with |
| `tool_response` | `object` | The tool's output/result |
| `tool_use_id` | `string` | Unique ID |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Flag issue | `"decision": "block"` + `"reason"` | Claude sees the reason and must address it |
| Inject context | `additionalContext` | Added to Claude's context after the tool result |
| Replace MCP output | `updatedMCPToolOutput: { ... }` | For MCP tools only -- replaces tool response |

```json
{
  "decision": "block",
  "reason": "File was written without 'use server' directive. Add it before proceeding.",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Lint check failed on the written file.",
    "updatedMCPToolOutput": null
  }
}
```

**Use cases:** Post-write linting, enforcing coding standards, augmenting tool output, telemetry.

---

#### 6. PostToolUseFailure

**When:** After a tool fails.
**Matcher:** Tool name regex
**Can block:** No

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `tool_name` | `string` | Tool that failed |
| `tool_input` | `object` | Args it was called with |
| `tool_use_id` | `string` | Unique ID |
| `error` | `string` | Error description |
| `is_interrupt` | `boolean?` | Whether the user interrupted the tool |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Inject context | `additionalContext` | Added alongside the error message Claude sees |

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "This error usually means the Supabase container isn't running. Try: pnpm supabase:web:start"
  }
}
```

**Use cases:** Error enrichment, suggested fixes, failure telemetry.

---

#### 7. Stop

**When:** Claude finishes its response and is about to stop.
**Matcher:** None
**Can block:** Yes (via `decision: "block"` -- tells Claude to keep working)

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `stop_hook_active` | `boolean` | `true` if a stop hook already triggered continuation this turn |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Force continuation | `"decision": "block"` + `"reason"` | Claude reads the reason and continues working |

```json
{
  "decision": "block",
  "reason": "You haven't run pnpm verify yet. Run typecheck + lint + test before stopping."
}
```

**Use cases:** Enforce verification steps, ensure Claude doesn't stop prematurely, append summaries.

**Warning:** Check `stop_hook_active` to avoid infinite loops -- if it's `true`, a previous stop hook already forced continuation this turn.

---

#### 8. Notification

**When:** Claude Code sends a system notification (permission prompt, idle, auth, dialog).
**Matcher:** `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`
**Can block:** No

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `message` | `string` | Notification text |
| `title` | `string?` | Notification title |
| `notification_type` | `string` | Type of notification |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Inject context | `additionalContext` | Added to Claude's context |

**Use cases:** Custom notification routing (Slack, desktop), telemetry, notification filtering.

---

#### 9. SubagentStart

**When:** A subagent (Task tool) is spawned.
**Matcher:** Agent type regex -- `Bash`, `Explore`, `Plan`, or custom agent names
**Can block:** No

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | `string` | Unique subagent identifier |
| `agent_type` | `string` | Agent type being spawned |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Inject context into subagent | `additionalContext` | Text injected into the subagent's system context |

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "You are working in a monorepo. Always use absolute paths."
  }
}
```

**Use cases:** Inject project rules into subagents, log subagent spawning, enforce subagent policies.

---

#### 10. SubagentStop

**When:** A subagent finishes its work.
**Matcher:** Agent type regex
**Can block:** Yes (via `decision: "block"` -- tells subagent to keep working)

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | `string` | Unique subagent identifier |
| `agent_type` | `string` | Agent type |
| `agent_transcript_path` | `string` | Path to subagent's full transcript |
| `stop_hook_active` | `boolean` | Whether a stop hook already triggered continuation |

**Output actions:**

| Action | How | Effect |
|--------|-----|--------|
| Force continuation | `"decision": "block"` + `"reason"` | Subagent reads reason and continues |

```json
{
  "decision": "block",
  "reason": "Subagent output is missing test coverage. Write tests before finishing."
}
```

**Use cases:** Quality gates on subagent output, transcript analysis, telemetry.

---

#### 11. PreCompact

**When:** Before context window compaction occurs.
**Matcher:** `manual`, `auto`
**Can block:** No
**Output:** Exit code only -- no JSON decision control.

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `trigger` | `"manual" \| "auto"` | How compaction was triggered |
| `custom_instructions` | `string` | User's custom compaction instructions (empty if auto) |

**Use cases:** Save pre-compaction state, log context size, inject compaction instructions.

---

#### 12. SessionEnd

**When:** Session terminates.
**Matcher:** `clear`, `logout`, `prompt_input_exit`, `bypass_permissions_disabled`, `other`
**Can block:** No
**Output:** Exit code only -- no JSON decision control.

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `reason` | `string` | Why the session ended |

**Use cases:** Cleanup, final telemetry, save session summaries.

---

#### 13. TeammateIdle (Agent Teams)

**When:** An agent team teammate is about to go idle.
**Matcher:** None
**Can block:** Exit code 2 only (stderr as feedback). No JSON decision control.

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `teammate_name` | `string` | Name of the teammate going idle |
| `team_name` | `string` | Team name |

**Use cases:** Prevent premature idling, reassign work, log idle patterns.

---

#### 14. TaskCompleted (Agent Teams)

**When:** A task is being marked as completed.
**Matcher:** None
**Can block:** Exit code 2 only (stderr as feedback). No JSON decision control.

**Input fields:**

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `string` | Task identifier |
| `task_subject` | `string` | Task title |
| `task_description` | `string?` | Detailed description |
| `teammate_name` | `string?` | Who completed it |
| `team_name` | `string?` | Team name |

**Use cases:** Verify acceptance criteria, enforce "tests must pass" gates, log completion metrics.

---

### Hook Configuration Structure

Hooks are configured in `settings.json` (project or user level):

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "regex_pattern",
        "hooks": [
          {
            "type": "command",
            "command": "python hooks/my_hook.py",
            "async": false,
            "timeout": 600,
            "statusMessage": "Checking...",
            "once": false
          }
        ]
      }
    ]
  }
}
```

| Config Field | Type | Description |
|-------------|------|-------------|
| `matcher` | `string?` | Regex to filter when this hook group fires. Empty string = match all. |
| `hooks` | `array` | List of handlers to run (all run in order) |

**Matcher examples:**

| Event | Matcher | Matches |
|-------|---------|---------|
| PreToolUse | `Bash` | Only Bash tool calls |
| PreToolUse | `mcp__makerkit__.*` | All MakerKit MCP tools |
| PreToolUse | `Write\|Edit` | Write or Edit tool calls |
| SubagentStart | `Explore` | Only Explore subagents |
| SessionStart | `startup` | Only fresh sessions (not resume/clear) |
| Notification | `idle_prompt` | Only idle notifications |
| PreCompact | `auto` | Only auto-triggered compaction |

### Hook Scope & Priority

| Location | Scope | Shareable |
|----------|-------|-----------|
| `~/.claude/settings.json` | All your projects | No (personal) |
| `.claude/settings.json` | Single project | Yes (committed) |
| `.claude/settings.local.json` | Single project | No (gitignored) |
| Skill frontmatter `hooks:` | While skill is active | Yes |
| Subagent frontmatter `hooks:` | While subagent runs | Yes |
| Plugin `hooks/hooks.json` | When plugin enabled | Yes |

### Async Hooks

Setting `"async": true` on command hooks runs them in the background:

- Hook output is delivered on the **next** conversation turn
- Cannot block or modify tool calls (already completed)
- Only `systemMessage` and `additionalContext` are processed from output
- Ideal for telemetry, logging, and non-blocking notifications

### Design Patterns

#### Pattern 1: Pre/Post Sandwich (Quality Gates)

```
PreToolUse(Write) -> validate file path, inject coding standards
  | tool executes
PostToolUse(Write) -> lint the written file, flag issues
```

The user depends on this pattern for enforcing `import 'server-only'`, `'use client'`, and coding standards without manual review.

#### Pattern 2: Context Enrichment Pipeline

```
SessionStart -> inject project status, sprint context
UserPromptSubmit -> inject relevant file context based on prompt analysis
PreToolUse -> inject tool-specific guidance
PostToolUse -> inject follow-up suggestions
```

Each hook adds targeted context, building a rich understanding without bloating the system prompt.

#### Pattern 3: Telemetry Pipeline (Async)

```
Every event -> async send_event.py -> external analytics
```

Non-blocking telemetry on every lifecycle event. The async flag ensures zero latency impact.

#### Pattern 4: Stop Gate (Verification Enforcement)

```
Stop -> check if pnpm verify was run -> block with reason if not
```

Prevents Claude from stopping before running required verification steps.

#### Pattern 5: Subagent Policy Injection

```
SubagentStart -> inject project rules into subagent context
SubagentStop -> analyze transcript, block if quality insufficient
```

Ensures subagents follow project conventions even though they don't inherit the parent's CLAUDE.md.

### Lessons Learned

| Lesson | Detail |
|--------|--------|
| **Check `stop_hook_active`** | Without this guard, Stop hooks can create infinite loops (block -> Claude responds -> Stop fires again -> block...) |
| **Exit 2 stderr is the message** | For blocking hooks, stderr is what Claude or the user sees. Make it actionable. |
| **`additionalContext` is powerful but invisible** | It's injected into Claude's context as a `<system-reminder>` tag. Claude sees it but may not explicitly reference it. |
| **Async hooks can't block** | They run after the fact. Use sync hooks for gates, async for telemetry. |
| **Matcher empty string = match all** | Omitting the matcher or setting it to `""` means the hook fires for every instance of that event. |
| **Multiple handlers run in order** | If you have two hooks in the array, both run sequentially. First to block wins. |
| **Welfare framing in hook messages** | Hook messages injected via `additionalContext` or block reasons are more effective when they explain *why* (see [Directive Compliance Framing](./anthropic-memory-and-prompting.md#23-directive-compliance-framing)). |
| **`updatedInput` in PreToolUse is underused** | You can transparently rewrite tool arguments -- e.g., adding `--bail` to test commands, fixing file paths, injecting flags. |
| **`updatedMCPToolOutput` in PostToolUse** | Only works for MCP tools. Lets you transform or filter MCP responses before Claude sees them -- useful for redacting sensitive data or trimming large outputs. |
