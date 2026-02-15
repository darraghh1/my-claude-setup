# Anthropic Skills Guide

> Part of the [Anthropic Best Practices](./anthropic-best-practices.md) series.
> Covers: Building, testing, iterating, and distributing Agent Skills.
>
> Sources:
> - `docs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf` (Anthropic, Feb 2026)
> - Claude Code Skills Documentation (`code.claude.com/docs/skills`)

---

## 1. Core Architecture: MCP + Skills

### The Kitchen Analogy

Anthropic frames the relationship between MCP and Skills as a professional kitchen:

| Layer | Analogy | What It Provides |
|-------|---------|-----------------|
| **MCP (Connectivity)** | The professional kitchen -- tools, ingredients, equipment | Connects Claude to your service (Notion, Asana, Linear, etc.). Provides real-time data access and tool invocation. |
| **Skills (Knowledge)** | The recipes -- step-by-step instructions | Teaches Claude _how_ to use your service effectively. Captures workflows and best practices. |

Together, they enable users to accomplish complex tasks without figuring out every step themselves.

### Without Skills (MCP Alone)

- Users connect MCP but don't know what to do next
- Support tickets asking "how do I do X with your integration"
- Each conversation starts from scratch
- Inconsistent results because users prompt differently each time
- Users blame the connector when the real issue is workflow guidance

### With Skills

- Pre-built workflows activate automatically when needed
- Consistent, reliable tool usage
- Best practices embedded in every interaction
- Lower learning curve for integrations

**Takeaway:** Tools alone aren't enough. Any agent architecture needs embedded workflow knowledge alongside tool access.

---

## 2. Agent Skills as an Open Standard

- Anthropic published Agent Skills as an open standard, analogous to MCP
- Skills should be portable across tools and platforms -- the same skill should work whether you're using Claude or other AI platforms
- Some skills are designed for a specific platform's capabilities; authors can note this in the `compatibility` field
- Anthropic is collaborating with ecosystem members on the standard

**Takeaway:** When building skills, design for portability. Don't hard-couple to Claude-specific features unless necessary, and document platform dependencies in `compatibility`.

---

## 3. Progressive Disclosure (Three-Level System)

| Level | What | Loaded When |
|-------|------|-------------|
| **Level 1: YAML frontmatter** | Minimal metadata (name, description) | Always in system prompt |
| **Level 2: SKILL.md body** | Full instructions and guidance | When Claude determines the skill is relevant |
| **Level 3: Linked files** | `references/`, `scripts/`, `assets/`, `examples/` | On-demand as Claude navigates the skill directory |

- Minimizes token usage while maintaining specialized expertise
- Keep SKILL.md focused on core instructions; move detailed docs to `references/` and link to them
- Keep SKILL.md under 5,000 words

**General principle:** This progressive disclosure pattern applies beyond skills to any system prompt or context management strategy. Front-load minimal metadata for routing decisions, defer detail until needed.

---

## 4. Skill File Structure & Naming

### Required Folder Structure

```
your-skill-name/           # kebab-case, no spaces/underscores/capitals
  SKILL.md                  # Required - exact spelling, case-sensitive
  scripts/                  # Optional - executable code (Python, Bash, etc.)
  references/               # Optional - documentation loaded as needed
  examples/                 # Optional - example files
  assets/                   # Optional - templates, fonts, icons
```

### Critical Naming Rules

| Rule | Correct | Wrong |
|------|---------|-------|
| Folder: kebab-case | `notion-project-setup` | `Notion Project Setup`, `notion_project_setup`, `NotionProjectSetup` |
| File: exact spelling | `SKILL.md` | `SKILL.MD`, `skill.md`, `Skill.md` |
| No README.md inside skill folder | All docs in SKILL.md or `references/` | Don't include README.md (use repo-level README for GitHub distribution) |

### Composability

- Claude loads multiple skills simultaneously
- Skills should work well alongside others, not assume exclusivity
- Design for coexistence

### Portability

- Skills work identically across Claude.ai, Claude Code, and API
- Build once, works on all surfaces (provided environment supports dependencies)

---

## 5. YAML Frontmatter (The Most Important Part)

The frontmatter is how Claude decides whether to load your skill. This is the single most impactful element.

### Required Fields

| Field | Requirements |
|-------|-------------|
| **name** | kebab-case only, no spaces or capitals, should match folder name |
| **description** | Must include WHAT it does + WHEN to use it (trigger conditions). Under 1024 chars. No XML tags. Include specific tasks users might say. Mention file types if relevant. |

### Description Formula

```
[What it does] + [When to use it] + [Key capabilities]
```

### Good vs Bad Descriptions

| Quality | Example | Why |
|---------|---------|-----|
| **Good** | "Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for 'design specs', 'component documentation', or 'design-to-code handoff'." | Specific, includes trigger phrases |
| **Good** | "Manages Linear project workflows including sprint planning, task creation, and status tracking. Use when user mentions 'sprint', 'Linear tasks', 'project planning', or asks to 'create tickets'." | Includes trigger phrases |
| **Good** | "End-to-end customer onboarding workflow for PayFlow. Handles account creation, payment setup, and subscription management. Use when user says 'onboard new customer', 'set up subscription', or 'create PayFlow account'." | Clear value proposition |
| **Bad** | "Helps with projects." | Too vague |
| **Bad** | "Creates sophisticated multi-page documentation systems." | Missing triggers |
| **Bad** | "Implements the Project entity model with hierarchical relationships." | Too technical, no user triggers |

### Optional Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `license` | Open-source license | `MIT`, `Apache-2.0` |
| `compatibility` | 1-500 chars. Environment requirements | Intended product, system packages, network needs |
| `allowed-tools` | Restrict which tools the skill can use | `"Bash(python:*) Bash(npm:*) WebFetch"` |
| `metadata` | Custom key-value pairs | `author`, `version`, `mcp-server`, `category`, `tags`, `documentation`, `support` |

### Full Optional Fields Example

```yaml
name: skill-name
description: [required description]
license: MIT
allowed-tools: "Bash(python:*) Bash(npm:*) WebFetch"
metadata:
  author: Company Name
  version: 1.0.0
  mcp-server: server-name
  category: productivity
  tags: [project-management, automation]
  documentation: https://example.com/docs
  support: support@example.com
```

### Security Restrictions (Forbidden in Frontmatter)

| Forbidden | Why |
|-----------|-----|
| XML angle brackets (`<` or `>`) | Could inject into system prompt |
| Skills named with "claude" or "anthropic" | Reserved prefixes |
| Code execution in YAML | Safe YAML parsing only |

---

## 6. Writing Effective Instructions

### Be Specific and Actionable

| Quality | Example |
|---------|---------|
| **Good** | `Run 'python scripts/validate.py --input {filename}' to check data format. If validation fails, common issues include: missing required fields, invalid date formats (use YYYY-MM-DD)` |
| **Bad** | `Validate the data before proceeding.` |

### Recommended SKILL.md Structure

```markdown
---
name: your-skill
description: [...]
---

# Your Skill Name

## Instructions

### Step 1: [First Major Step]
Clear explanation of what happens.

```bash
python scripts/fetch_data.py --project-id PROJECT_ID
Expected output: [describe what success looks like]
```

### Step 2: [Next Step]
Include expected output.

## Examples

### Example 1: [Common scenario]
User says: "Set up a new marketing campaign"
Actions:
1. Fetch existing campaigns via MCP
2. Create new campaign with provided parameters
Result: Campaign created with confirmation link

## Troubleshooting

### Error: [Common error message]
Cause: [Why]
Solution: [How to fix]
```

### Key Writing Principles

1. **Put critical instructions at the top** -- use `## Important` or `## Critical` headers
2. **Reference bundled resources clearly** -- tell Claude where to find reference docs and what they contain
3. **Use progressive disclosure** -- core instructions in SKILL.md, detailed docs in `references/`
4. **Include error handling** -- document common failure modes and recovery steps
5. **Provide concrete examples** -- show input/output pairs for common scenarios
6. **Use bullet points and numbered lists** -- keep instructions concise and scannable
7. **Repeat key points if needed** -- important instructions are worth restating
8. **Avoid ambiguous language** -- "Make sure to validate things properly" is bad; "CRITICAL: Before calling create_project, verify: project name is non-empty, at least one team member assigned, start date is not in the past" is good

---

## 7. General Claude Prompting Insights

These insights from the guide apply beyond skills to any Claude interaction.

### Code Is Deterministic; Language Interpretation Isn't

For critical validations, bundle a script that performs checks programmatically rather than relying on language instructions. Anthropic references their Office skills as examples of this pattern.

**Takeaway:** When a check must be reliable (not "usually works"), use a validation script in `scripts/` rather than prose instructions in SKILL.md.

### Performance Encouragement: User Prompt > System Prompt

Adding explicit encouragement is more effective when placed in the user-facing prompt than in SKILL.md/system instructions:

```
## Performance Notes
- Take your time to do this thoroughly
- Quality is more important than speed
- Do not skip validation steps
```

**Takeaway:** For our CLAUDE.md and skill instructions, performance nudges ("be thorough", "don't skip steps") may be more effective if surfaced closer to the user prompt layer rather than buried in system instructions.

### In-Context Learning Workflow

> "The most effective skill creators iterate on a single challenging task until Claude succeeds, then extract the winning approach into a skill."

This leverages Claude's in-context learning and provides faster signal than broad testing. Once you have a working foundation, expand to multiple test cases for coverage.

**Takeaway:** When building any new workflow (not just skills), perfect it in a single conversation first, then codify it.

### Model "Laziness" Mitigation

When Claude skips steps or takes shortcuts, add explicit encouragement:

- "Take your time to do this thoroughly"
- "Quality is more important than speed"
- "Do not skip validation steps"

---

## 8. Planning & Use Case Design

### Start with Use Cases (Before Writing Code)

- Identify 2-3 concrete use cases your skill should enable
- For each use case define: trigger, steps, tools needed, expected result

### Good Use Case Definition

```
Use Case: Project Sprint Planning
Trigger: User says "help me plan this sprint" or "create sprint tasks"
Steps:
1. Fetch current project status from Linear (via MCP)
2. Analyze team velocity and capacity
3. Suggest task prioritization
4. Create tasks in Linear with proper labels and estimates
Result: Fully planned sprint with tasks created
```

### Ask Yourself

1. What does a user want to accomplish?
2. What multi-step workflows does this require?
3. Which tools are needed (built-in or MCP)?
4. What domain knowledge or best practices should be embedded?

### Three Skill Categories

| Category | Purpose | Key Techniques |
|----------|---------|----------------|
| **Document & Asset Creation** | Consistent, high-quality output (documents, code, presentations) | Embedded style guides, template structures, quality checklists, no external tools needed |
| **Workflow Automation** | Multi-step processes with consistent methodology | Step-by-step validation gates, templates for common structures, built-in review/improvement suggestions, iterative refinement loops |
| **MCP Enhancement** | Workflow guidance layered on top of MCP tool access | Coordinates multiple MCP calls in sequence, embeds domain expertise, provides context users would otherwise specify, error handling for common MCP issues |

### Problem-First vs Tool-First Framing

| Approach | When | Example |
|----------|------|---------|
| **Problem-first** | User describes outcome, skill orchestrates tools | "I need to set up a project workspace" -- skill handles the MCP calls in the right sequence |
| **Tool-first** | User has MCP connected, skill teaches best practices | "I have Notion MCP connected" -- skill teaches optimal workflows and best practices |

Most skills lean one direction. Knowing which framing fits your use case helps choose the right pattern.

---

## 9. Success Metrics

### Quantitative Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Trigger accuracy | 90% of relevant queries | Run 10-20 test queries. Track how many times it loads automatically vs. requires explicit invocation |
| Workflow efficiency | Complete in X tool calls | Compare same task with and without skill. Count tool calls and total tokens consumed |
| API reliability | 0 failed API calls per workflow | Monitor MCP server logs during test runs. Track retry rates and error codes |

### Qualitative Metrics

| Metric | How to Assess |
|--------|---------------|
| No user prompting needed | During testing, note how often you need to redirect or clarify. Ask beta users for feedback |
| Completes without correction | Run same request 3-5 times, compare structural consistency and quality |
| Consistent across sessions | Can a new user accomplish the task on first try with minimal guidance? |

These are aspirational targets -- rough benchmarks rather than precise thresholds. Anthropic notes they are actively developing more robust measurement guidance and tooling.

---

## 10. Testing Strategy

### Three Testing Approaches

| Approach | Best For | Setup Required |
|----------|----------|----------------|
| **Manual testing in Claude.ai** | Fast iteration, exploring edge cases | None |
| **Scripted testing in Claude Code** | Repeatable validation across changes | Minimal |
| **Programmatic testing via Skills API** | Evaluation suites against defined test sets | API setup |

Choose based on quality requirements and visibility. A skill used internally by a small team has different testing needs than one deployed to thousands.

### Pro Tip: Iterate on a Single Task First

> "We've found that the most effective skill creators iterate on a single challenging task until Claude succeeds, then extract the winning approach into a skill."

This leverages Claude's in-context learning and provides faster signal than broad testing. Once you have a working foundation, expand to multiple test cases.

### Three Testing Areas

**1. Triggering Tests** -- Does the skill load at the right times?

```
Should trigger:
- "Help me set up a new ProjectHub workspace"
- "I need to create a project in ProjectHub"
- "Initialize a ProjectHub project for Q4 planning"

Should NOT trigger:
- "What's the weather in San Francisco?"
- "Help me write Python code"
- "Create a spreadsheet" (unless ProjectHub skill handles sheets)
```

**2. Functional Tests** -- Does the skill produce correct outputs?

```
Test: Create project with 5 tasks
Given: Project name "Q4 Planning", 5 task descriptions
When: Skill executes workflow
Then:
  - Project created in ProjectHub
  - 5 tasks created with correct properties
  - All tasks linked to project
  - No API errors
```

**3. Performance Comparison** -- Does the skill improve results vs. baseline?

```
Without skill:               With skill:
- User provides instructions  - Automatic workflow execution
  each time
- 15 back-and-forth messages  - 2 clarifying questions only
- 3 failed API calls          - 0 failed API calls
- 12,000 tokens consumed      - 6,000 tokens consumed
```

### Using the skill-creator Skill

The `skill-creator` skill (built into Claude.ai, available for Claude Code download) helps build and iterate on skills:

| Capability | What It Does |
|------------|-------------|
| **Creating** | Generates skills from natural language descriptions. Produces properly formatted SKILL.md with frontmatter. Suggests trigger phrases and structure. |
| **Reviewing** | Flags common issues (vague descriptions, missing triggers, structural problems). Identifies over/under-triggering risks. Suggests test cases. |
| **Iterating** | Bring edge cases and failures back to skill-creator. Example: "Use the issues & solutions identified in this chat to improve how the skill handles [specific edge case]" |

**Note:** skill-creator helps design and refine skills but does not execute automated test suites or produce quantitative evaluation results.

---

## 11. Iteration Signals

Skills are living documents. Plan to iterate based on these signals:

### Undertriggering (Skill Doesn't Load When It Should)

| Signal | Solution |
|--------|----------|
| Skill doesn't load when it should | Add more detail and nuance to description |
| Users manually enabling it | Include keywords, especially technical terms |
| Support questions about when to use it | Add trigger phrases users would actually say |

### Overtriggering (Skill Loads for Irrelevant Queries)

| Signal | Solution |
|--------|----------|
| Skill loads for irrelevant queries | Add negative triggers ("Do NOT use for...") |
| Users disabling it | Be more specific about scope |
| Confusion about purpose | Clarify scope in description |

Example negative trigger:
```
description: Advanced data analysis for CSV files. Use for
statistical modeling, regression, clustering. Do NOT use for
simple data exploration (use data-viz skill instead).
```

### Execution Issues

| Signal | Solution |
|--------|----------|
| Inconsistent results | Improve instructions, add more structure |
| API call failures | Add error handling guidance |
| User corrections needed | Add validation steps and quality checks |

---

## 12. Workflow Patterns

These patterns emerged from skills created by early adopters and internal teams. They represent common approaches, not prescriptive templates.

### Pattern 1: Sequential Workflow Orchestration

**Use when:** Multi-step processes in a specific order.

```
## Workflow: Onboard New Customer

### Step 1: Create Account
Call MCP tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call MCP tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

### Step 4: Send Welcome Email
Call MCP tool: `send_email`
Template: welcome_email_template
```

| Technique | Purpose |
|-----------|---------|
| Explicit step ordering | Prevents skipping or reordering |
| Dependencies between steps | Data from Step 1 feeds Step 2 |
| Validation at each stage | Catch errors early |
| Rollback instructions for failures | Graceful recovery |

### Pattern 2: Multi-MCP Coordination

**Use when:** Workflows span multiple services.

```
### Phase 1: Design Export (Figma MCP)
1. Export design assets from Figma
2. Generate design specifications
3. Create asset manifest

### Phase 2: Asset Storage (Drive MCP)
1. Create project folder in Drive
2. Upload all assets
3. Generate shareable links

### Phase 3: Task Creation (Linear MCP)
1. Create development tasks
2. Attach asset links to tasks
3. Assign to engineering team

### Phase 4: Notification (Slack MCP)
1. Post handoff summary to #engineering
2. Include asset links and task references
```

| Technique | Purpose |
|-----------|---------|
| Clear phase separation | Each MCP gets its own phase |
| Data passing between MCPs | Output of one feeds input of next |
| Validation before moving to next phase | Prevent cascading failures |
| Centralized error handling | One place to diagnose issues |

### Pattern 3: Iterative Refinement

**Use when:** Output quality improves with iteration.

```
## Iterative Report Creation

### Initial Draft
1. Fetch data via MCP
2. Generate first draft report
3. Save to temporary file

### Quality Check
1. Run validation script: `scripts/check_report.py`
2. Identify issues:
   - Missing sections
   - Inconsistent formatting
   - Data validation errors

### Refinement Loop
1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met

### Finalization
1. Apply final formatting
2. Generate summary
3. Save final version
```

| Technique | Purpose |
|-----------|---------|
| Explicit quality criteria | Define "done" |
| Iterative improvement | Generate, check, fix, repeat |
| Validation scripts | Automate quality checks |
| Know when to stop iterating | Prevent infinite loops |

### Pattern 4: Context-Aware Tool Selection

**Use when:** Same outcome, different tools depending on context.

```
## Smart File Storage

### Decision Tree
1. Check file type and size
2. Determine best storage location:
   - Large files (>10MB): Use cloud storage MCP
   - Collaborative docs: Use Notion/Docs MCP
   - Code files: Use GitHub MCP
   - Temporary files: Use local storage

### Execute Storage
Based on decision:
- Call appropriate MCP tool
- Apply service-specific metadata
- Generate access link

### Provide Context to User
Explain why that storage was chosen
```

| Technique | Purpose |
|-----------|---------|
| Clear decision criteria | Rules for choosing which tool |
| Fallback options | If primary tool fails, try alternative |
| Transparency about choices | Explain to user why a tool was chosen |

### Pattern 5: Domain-Specific Intelligence

**Use when:** Skill adds specialized knowledge beyond tool access.

```
## Payment Processing with Compliance

### Before Processing (Compliance Check)
1. Fetch transaction details via MCP
2. Apply compliance rules:
   - Check sanctions lists
   - Verify jurisdiction allowances
   - Assess risk level
3. Document compliance decision

### Processing
IF compliance passed:
  - Call payment processing MCP tool
  - Apply appropriate fraud checks
  - Process transaction
ELSE:
  - Flag for review
  - Create compliance case

### Audit Trail
- Log all compliance checks
- Record processing decisions
- Generate audit report
```

| Technique | Purpose |
|-----------|---------|
| Domain expertise embedded in logic | Compliance rules, business logic |
| Compliance before action | Check rules before executing |
| Comprehensive documentation | Audit trail of decisions |
| Clear governance | Who approves what |

---

## 13. Anti-Patterns & Troubleshooting

### Instructions Not Followed

| Cause | Fix |
|-------|-----|
| **Instructions too verbose** | Keep concise, use bullet points and numbered lists, move detail to `references/` |
| **Instructions buried** | Put critical instructions at the top with `## Important` or `## Critical` headers. Repeat key points if needed. |
| **Ambiguous language** | Replace vague directives with explicit checklists. "Make sure to validate things properly" becomes "CRITICAL: Before calling create_project, verify: project name is non-empty, at least one team member assigned, start date is not in the past" |
| **Model "laziness"** | Add explicit encouragement (see Section 7). More effective in user prompt than in SKILL.md. |

**Advanced technique:** For critical validations, bundle a script that performs checks programmatically rather than relying on language instructions. Code is deterministic; language interpretation isn't. See the Office skills for examples of this pattern.

### Large Context Issues

**Symptom:** Skill seems slow or responses degraded.

| Cause | Fix |
|-------|-----|
| Skill content too large | Keep SKILL.md under 5,000 words, move docs to `references/`, link to references instead of inlining |
| Too many skills enabled | Evaluate if you have more than 20-50 skills enabled simultaneously. Recommend selective enablement. Consider skill "packs" for related capabilities. |
| All content loaded instead of progressive disclosure | Use the three-level system properly (Section 3) |

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Could not find SKILL.md in uploaded folder" | Wrong filename | Must be exactly `SKILL.md` (case-sensitive). Verify with `ls -la` |
| "Invalid frontmatter" | YAML formatting issue | Use `---` delimiters, close all quotes. Common mistakes: missing delimiters, unclosed quotes |
| "Invalid skill name" | Name has spaces or capitals | Use kebab-case only: `my-cool-skill` not `My Cool Skill` |

### Skill Never Loads Automatically

**Symptom:** Skill never triggers on its own.

**Fix:** Revise description field. Quick checklist:
- Is it too generic? ("Helps with projects" won't work)
- Does it include trigger phrases users would actually say?
- Does it mention relevant file types if applicable?

**Debug technique:** Ask Claude "When would you use the [skill name] skill?" Claude will quote the description back -- adjust based on what's missing.

### Skill Triggers Too Often

**Symptom:** Skill loads for unrelated queries.

**Solutions:**
1. Add negative triggers: `"Do NOT use for simple data exploration (use data-viz skill instead)."`
2. Be more specific: `"Processes PDF legal documents for contract review"` not `"Processes documents"`
3. Clarify scope: `"PayFlow payment processing for e-commerce. Use specifically for online payment workflows, not for general financial queries."`

### MCP Connection Issues

**Symptom:** Skill loads but MCP calls fail.

**Checklist:**
1. **Verify MCP server is connected** -- Claude.ai: Settings > Extensions > [Your Service], should show "Connected"
2. **Check authentication** -- API keys valid, permissions/scopes granted, OAuth tokens refreshed
3. **Test MCP independently** -- Ask Claude to call MCP directly without skill: "Use [Service] MCP to fetch my projects." If this fails, issue is MCP not skill
4. **Verify tool names** -- Skill must reference correct MCP tool names (case-sensitive). Check MCP server documentation

---

## 14. MCP Tool Usage in Skills -- Lessons Learned

These lessons emerged from building and iteratively testing a skill that orchestrates 55 MCP tools across 10 categories. Each lesson cost at least one failed test session to discover.

### Lesson 1: Claude Doesn't Know MCP Tools Are Direct Tool Calls

**Problem:** In a fresh session, Claude saw `mcp__makerkit__get_table_info` in the skill instructions and ran it via Bash as `claude mcp call makerkit get_table_info ...` -- which produced empty output. It didn't realize MCP tools are native tool calls, the same as `Read` or `Grep`.

**Fix:** Both the skill AND always-loaded rules must show an explicit CORRECT vs WRONG example:

```markdown
## Critical: These Are Direct Tool Calls

MCP tools are **direct tool calls** -- exactly like `Read`, `Grep`, or `Bash`.

**CORRECT** -- call the tool directly:
Tool: mcp__makerkit__get_table_info
Parameters: { "state": { "tableName": "accounts" } }

**WRONG** -- do NOT shell out:
Bash: claude mcp call makerkit get_table_info ...  # This does not work
```

**Takeaway:** Never assume Claude understands _how_ to invoke MCP tools just because they're listed. Show the invocation mechanism explicitly, with a negative example of the most likely mistake.

### Lesson 2: Skills Alone Don't Drive Habitual Tool Usage

**Problem:** A skill with good trigger phrases ("what columns does X have?") was loaded correctly, but Claude still defaulted to `Read` and `Grep` for database questions in sessions where the skill wasn't explicitly triggered. Skills only load when Claude decides they're relevant -- they don't create habits.

**Fix:** Create an always-loaded `.claude/rules/` file that nudges MCP tool usage for common scenarios. Rules are in the system prompt for every session, unlike skills which are loaded on-demand.

| Mechanism | When It Helps | Limitation |
|-----------|--------------|------------|
| **Skill description** (frontmatter) | Explicit requests matching trigger phrases | Only loads when triggered |
| **Rules file** (`.claude/rules/`) | Every session, every context | Always consumes system prompt tokens |

**Takeaway:** For tools you want Claude to use habitually (not just when asked), put the guidance in always-loaded rules, not just in skills. Skills teach workflows; rules create habits.

### Lesson 3: MCP Tools That Return Large Output Need Guardrails

**Problem:** Several MCP tools flooded context with massive payloads (86 database tables, 717 translation keys, 70+ UI components), degrading response quality and wasting tokens.

**Fix:** Document output-size awareness in the skill with a clear table of large-output tools and their targeted alternatives:

```markdown
## Critical: Output Size Awareness

| Tool | Output Size | Prefer Instead |
|------|------------|----------------|
| `get_database_summary` | Very large (86 tables, partitions bloat) | `get_schemas_by_topic` for targeted queries |
| `kit_translations_list` | Very large (all values inline) | `kit_translations_stats` for overview |
| `get_components` | Large (70+ components) | `components_search` with keyword |
```

**Takeaway:** When building MCP Enhancement skills (Section 8), test every tool's actual output size. Document which tools are "safe to call freely" vs "call only when you need the full list" -- Claude has no way to know this without being told.

### Lesson 4: MCP Tools May Have Coverage Gaps -- Document Fallback Paths

**Problem:** `get_table_info` only reads declarative schema files. Tables created via migrations (40 of 86 tables in our project) returned "not found." Claude then called `get_database_tables` to discover the table, which dumped all 86 tables into context.

**Fix:** Document the tool's coverage limitation AND the correct fallback:

```markdown
### Fallback: `get_table_info` Only Works for Schema-File Tables

When `get_table_info` fails with "not found in schema files", fall back to
grepping migration files for the CREATE TABLE statement.

Do NOT call `get_database_tables` as a fallback -- it returns all 86 tables
and floods context.
```

**Takeaway:** MCP tools abstract away details, but that abstraction can hide coverage gaps. Test each tool against edge cases (tables created differently, missing data, empty results) and document what happens when the tool can't find what Claude is looking for. The fallback path is as important as the happy path.

### Lesson 5: Parallel MCP Calls Need Explicit Permission

**Problem:** Claude called MCP tools sequentially even when they were independent (e.g., checking table structure AND migration status). This doubled response latency.

**Fix:** Explicitly state which tools can run in parallel:

```markdown
### Steps
1. **Run these in parallel** (they are independent):
   - `get_table_info` -> table structure
   - `kit_db_status` -> pending migrations
```

**Takeaway:** Claude defaults to sequential tool calls unless told otherwise. For MCP Enhancement skills with multi-tool workflows, explicitly mark which steps are independent and can run in parallel.

### Summary: MCP Skill Checklist

| Check | Why |
|-------|-----|
| Show how to invoke tools (CORRECT vs WRONG) | Claude may try to shell out instead of calling directly |
| Put habits in `.claude/rules/`, workflows in skills | Rules are always loaded; skills load on-demand |
| Document output sizes and targeted alternatives | Prevent context flooding from large-payload tools |
| Test tools against edge cases and document fallbacks | Coverage gaps cause cascading failures |
| Mark independent tools as parallelizable | Reduces latency on multi-tool workflows |
| Include "Do NOT use for..." in description | Prevents overtriggering on adjacent domains |

---

## 15. Distribution & Sharing

### Current Distribution Model (January 2026)

**Individual users:**
1. Download the skill folder
2. Zip the folder (if needed)
3. Upload to Claude.ai via Settings > Capabilities > Skills
4. Or place in Claude Code skills directory

**Organization-level skills** (shipped December 18, 2025):
- Admins deploy skills workspace-wide
- Automatic updates
- Centralized management

### Skills via API

Skills in the API require the **Code Execution Tool beta**, which provides the secure environment skills need to run.

| Capability | Detail |
|------------|--------|
| Endpoint | `/v1/skills` for listing and managing skills |
| Messages API | `container.skills` parameter to attach skills to requests |
| Version control | Through the Claude Console |
| Agent SDK | Works with the Claude Agent SDK for building custom agents |

### API vs Claude.ai/Claude Code: When to Use Which

| Use Case | Best Surface |
|----------|-------------|
| End users interacting with skills directly | Claude.ai / Claude Code |
| Manual testing and iteration during development | Claude.ai / Claude Code |
| Individual, ad-hoc workflows | Claude.ai / Claude Code |
| Applications using skills programmatically | API |
| Production deployments at scale | API |
| Automated pipelines and agent systems | API |

### Recommended Distribution Approach

**1. Host on GitHub**
- Public repo for open-source skills
- Clear README with installation instructions (repo-level, separate from SKILL.md)
- Example usage and screenshots

**2. Document in Your MCP Repo**
- Link to skills from MCP documentation
- Explain the value of using both together
- Provide quick-start guide

**3. Create an Installation Guide**
```
## Installing the [Your Service] skill

1. Download the skill:
   - Clone repo: `git clone https://github.com/yourcompany/skills`
   - Or download ZIP from Releases

2. Install in Claude:
   - Open Claude.ai > Settings > skills
   - Click "Upload skill"
   - Select the skill folder (zipped)

3. Enable the skill:
   - Toggle on the [Your Service] skill
   - Ensure your MCP server is connected

4. Test:
   - Ask Claude: "Set up a new project in [Your Service]"
```

### Positioning Your Skill

**Focus on outcomes, not features:**

| Quality | Example |
|---------|---------|
| **Good** | "The ProjectHub skill enables teams to set up complete project workspaces in seconds -- including pages, databases, and templates -- instead of spending 30 minutes on manual setup." |
| **Bad** | "The ProjectHub skill is a folder containing YAML frontmatter and Markdown instructions that calls our MCP server tools." |

**Highlight the MCP + skills story:**

> "Our MCP server gives Claude access to your Linear projects. Our skills teach Claude your team's sprint planning workflow. Together, they enable AI-powered project management."

---

## 16. Pre-Release Checklist

### Before You Start

- [ ] Identified 2-3 concrete use cases
- [ ] Tools identified (built-in or MCP)
- [ ] Reviewed this guide and example skills
- [ ] Planned folder structure

### During Development

- [ ] Folder named in kebab-case
- [ ] `SKILL.md` file exists (exact spelling)
- [ ] YAML frontmatter has `---` delimiters
- [ ] `name` field: kebab-case, no spaces, no capitals
- [ ] `description` includes WHAT and WHEN
- [ ] No XML tags (`<` `>`) anywhere in frontmatter
- [ ] Instructions are clear and actionable
- [ ] Error handling included
- [ ] Examples provided
- [ ] References clearly linked

### Before Upload

- [ ] Tested triggering on obvious tasks
- [ ] Tested triggering on paraphrased requests
- [ ] Verified doesn't trigger on unrelated topics
- [ ] Functional tests pass
- [ ] Tool integration works (if applicable)
- [ ] Compressed as .zip file

### After Upload

- [ ] Test in real conversations
- [ ] Monitor for under/over-triggering
- [ ] Collect user feedback
- [ ] Iterate on description and instructions
- [ ] Update version in metadata

---

## 17. Official Resources

### Anthropic Documentation

| Resource | Purpose |
|----------|---------|
| Best Practices Guide | Core guidance for skill building |
| Skills Documentation | Technical reference |
| API Reference | Programmatic skill management |
| MCP Documentation | Tool connectivity |

### Blog Posts

- Introducing Agent Skills
- Engineering Blog: Equipping Agents for the Real World
- Skills Explained
- How to Create Skills for Claude
- Building Skills for Claude Code
- Improving Frontend Design through Skills

### Example Skills

| Repository | Contents |
|------------|----------|
| `anthropic/skills` (GitHub) | Anthropic-created skills you can customize |
| Document Skills | PDF, DOCX, PPTX, XLSX creation |
| Example Skills | Various workflow patterns |
| Partner Skills Directory | Skills from Asana, Atlassian, Canva, Figma, Sentry, Zapier, and more |

### Support

| Channel | For |
|---------|-----|
| Claude Developers Discord | General technical questions |
| GitHub Issues (`anthropic/skills/issues`) | Bug reports (include skill name, error message, steps to reproduce) |

---

## 18. Key Takeaways for Our Setup

| Insight | Action for DigitalMastery |
|---------|--------------------------|
| Description field is the #1 factor for triggering | Audit all our existing skill descriptions against the `[What] + [When] + [Capabilities]` formula |
| Progressive disclosure saves tokens | Move detailed reference docs out of SKILL.md into `references/` subdirectories |
| Negative triggers prevent overtriggering | Add "Do NOT use for..." clauses to skills that overlap in scope |
| Validation scripts beat language instructions | For critical checks (typecheck, lint), use `scripts/` rather than prose instructions. Code is deterministic. |
| Iterate on one task before broadening | When building new skills, nail one use case completely before expanding |
| Keep SKILL.md under 5,000 words | Audit current skills for bloat; extract to `references/` |
| Performance encouragement in user prompt > system prompt | "Take your time", "Quality over speed" works better in the user-facing prompt layer |
| Test with 10-20 queries for trigger accuracy | Build trigger test suites for each skill (should trigger + should NOT trigger) |
| `allowed-tools` field restricts tool access | Use for skills that should only use specific tools (security benefit). Syntax: `"Bash(python:*) Bash(npm:*) WebFetch"` |
| Skills are an open standard | Same skill works across Claude.ai, Claude Code, and API. Design for portability. |
| MCP alone isn't enough | Tools without workflow knowledge leads to inconsistent results and user frustration. Pair every MCP integration with skills. |
| Code Execution Tool beta required for API skills | Plan for this dependency if using skills programmatically |
| Organization-level deployment available | Admins can deploy skills workspace-wide with automatic updates (shipped Dec 2025) |
| In-context learning workflow | Perfect a workflow in a single conversation first, then codify it as a skill |
