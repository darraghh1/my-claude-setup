---
name: create-plan
description: "Create complete implementation plans with phases for new features or projects. Use when starting a new feature, planning a refactor, or designing a system ('create a plan', 'plan this feature', 'design the phases for...', 'plan the implementation'). Do NOT use for implementing code (use /implement), reviewing existing plans (use /review-plan), or quick single-file changes."
argument-hint: "[feature-name] [description]"
context: fork
agent: general-purpose
model: sonnet
allowed-tools: Read, Write, Edit, Glob, Grep, Task, Skill, TaskCreate, TaskUpdate, TaskList, TaskGet, AskUserQuestion
metadata:
  version: 1.0.0
  category: workflow-automation
  tags: [planning, phases, architecture, feature-design]
---

# Create Complete Plan

Create a complete plan with phases for: **$ARGUMENTS**

## Current Plans

Existing plans in the repository (avoid naming conflicts):

!`ls plans/ 2>/dev/null || echo "(no plans directory yet)"`

## Workflow Overview

This skill creates a full planning package:
1. **Folder structure** with date-prefixed naming
2. **plan.md** with all sections (phases added iteratively)
3. **Reference reading** from actual codebase for pattern accuracy
4. **Phase files** created one at a time with correct code patterns
5. **Review** via sub-agents for template + codebase compliance

## Step 1: Clarify Requirements

The user has experienced 20-phase plans built on wrong assumptions — hours of work discarded because a 30-second question wasn't asked upfront. Clarification prevents this waste.

Read the task description above. If anything is ambiguous or underspecified, use `AskUserQuestion` to clarify before proceeding.

**Questions to ask if not clear from the description:**

1. **Problem:** What specific problem are we solving? What pain point does this address?
2. **Scope:** Is this a small feature, medium enhancement, or major system?
3. **Users:** Who uses this feature? (specific roles, account types)
4. **Integrations:** Does this connect to external services or APIs?
5. **Data:** What data does this create, read, update, or delete?
6. **UI:** Where does this appear in the app? New page, existing page, component?

If the description says "add voice commands" but doesn't specify which commands, ASK. If it says "improve performance" but doesn't specify what's slow, ASK. The user prefers a brief clarification dialogue over assumptions that lead to rework.

## Step 2: Read Templates

The user created these templates specifically so phases don't miss required sections. Skipping template reading causes incomplete phases that require rework during implementation.

Read both templates completely:
- `references/PLAN-TEMPLATE.md`
- `references/PHASE-TEMPLATE.md`

Every section in these templates is required.

## Step 3: Create Folder Structure

**Folder naming pattern:** `plans/{YYMMDD}-{feature-name}/`

Examples:
- `plans/250202-voice-assistant/`
- `plans/250202-notification-system/`
- `plans/250202-api-refactor/`

**Create these items:**
1. Main folder: `plans/{YYMMDD}-{feature-name}/`
2. Planning reviews folder: `plans/{YYMMDD}-{feature-name}/reviews/planning/`
3. Code reviews folder: `plans/{YYMMDD}-{feature-name}/reviews/code/`

## Step 4: Create Task List

Tasks survive context compacts — skipping this check causes duplicate tasks and lost progress.

Before creating tasks, run `TaskList` to check if tasks already exist from a previous session or before a compact. If tasks exist:
1. Read existing tasks with `TaskGet` for each task ID
2. Find the first task with status `pending` or `in_progress`
3. Resume from that task — do NOT recreate the task list

If no tasks exist, create them now. The user depends on task tracking to prevent skipped sections.

**Example task list:**

```
Task 1: Create plan.md structure (all sections except Phase Table content)
Task 2: Read codebase references
Task 3: Design phase breakdown
Task 4: Create Phase 01 - [Title]
Task 5: Create Phase 02 - [Title]
[...continue for all phases...]
Task N: Review complete plan (delegate to review sub-agents)
```

## Step 5: Create plan.md (Without Phase Details)

Write `plans/{folder}/plan.md` with ALL sections from the template:

1. YAML Frontmatter (title, status, priority, tags, dates)
2. Executive Summary (Mission, Big Shift, Deliverables)
3. Phasing Strategy (Phase Constraints, Phase File Naming)
4. **Phase Table** — Header row only, no content rows yet
5. Architectural North Star (patterns with Core Principle + Enforcement)
6. Component Library Priority (check your UI library before building custom)
7. Security Requirements (RLS, Input Validation, Authorization, Error Handling)
8. Implementation Standards (Test Strategy, Documentation Standard)
9. Success Metrics & Quality Gates
10. Global Decision Log (ADRs)
11. Resources & References

Complete ALL sections except Phase Table rows. Missing sections are caught during review (Step 9) but cost extra review cycles to fix.

## Step 6: Design Phase Breakdown

Before creating phase files, plan the full decomposition.

### Load Frontend Guidelines (If Applicable)

If the feature involves React components, Next.js pages, or UI work, invoke this skill BEFORE designing phases:

```
/vercel-react-best-practices
```

This loads 57 performance rules across 8 categories. Reference these when designing data fetching patterns, component architecture, and bundle optimization requirements.

### Phase Constraints

Phases that exceed one context window cause Claude to lose earlier context mid-implementation, producing incomplete or inconsistent code. Each phase should be atomic enough for implementation in **1 context window** (~15KB document, ~2-3 hour focused session).

**30 small phases > 5 large phases**

| Wrong Approach | Right Approach |
|----------------|----------------|
| "Phase 01: Database + API + UI" | Split into 3 phases |
| "Phase 02: Full Feature Implementation" | Break into atomic steps |
| "Phase 03: Testing and Polish" | TDD is Step 0 in EACH phase |

**TDD Note:** Both backend and frontend code require full unit tests:
- **Backend** (services, schemas, APIs): Unit tests in `__tests__/{feature}/`
- **Frontend** (React/TSX): Component tests using happy-dom (default) and @testing-library/react
- The default happy-dom environment works for component tests. Only add `// @vitest-environment happy-dom` if explicitly overriding another environment.
- Use `it.todo('description')` for TDD stubs
- Use `vi.hoisted()` for mock variables needed before module evaluation
- For Supabase client mocks, add `.then()` method for thenable/awaitable pattern
- Path aliases in tests: use your project's configured path alias (e.g., `@/` or `~/`)

**Atomic phase examples:**
- Phase 01: Database Schema & RLS Policies
- Phase 02: Service Layer Functions
- Phase 03: Server Actions with Validation
- Phase 04: List View Component
- Phase 05: Create Form Component

**The test:** Can Claude implement this phase without running out of context? If unsure, split it.

## Step 7: Read Codebase References

Code blocks written from memory often don't match the real codebase — this is the #1 source of phase quality issues. Reading actual files before writing phases ensures patterns are accurate.

Identify which file types the feature will need and read one reference for each:

| Feature Needs | Reference to Read |
|---------------|-------------------|
| Server actions | Glob `app/home/[account]/**/*server-actions*.ts` → read one |
| Service layer | Glob `app/home/[account]/**/*service*.ts` → read one |
| Zod schemas | Glob `app/home/[account]/**/*.schema.ts` → read one |
| SQL migrations / RLS | Glob `supabase/migrations/*.sql` → read a recent one |
| React components | Glob `app/home/[account]/**/_components/*.tsx` → read one |
| Page files | Glob `app/home/[account]/**/page.tsx` → read one |
| Tests | Glob `__tests__/**/*.test.ts` → read one |

**Key patterns to extract and use in phase code blocks:**
- Server action pattern: `'use server'` + Zod parse + `getSession()` auth check
- Account resolution: slug → ID via `client.from('accounts').select('id').eq('slug', data.accountSlug).single()`
- Permission check: your RLS helper function (e.g., `client.rpc('check_account_access', { ... })`)
- Supabase client: `createClient()` from `@/lib/supabase/server`
- Service factory: `createXxxService(client: SupabaseClient<Database>)` wrapping a private class
- Import paths: `import 'server-only'`, `@/` path alias for project root
- File naming: `_lib/schema/` (singular), `server-actions.ts`, exports ending in `Action`
- TypeScript: consider enums or union types for constants, `interface` preferred for objects
- After mutations: `revalidatePath('/home/[account]/...')`

Keep these patterns in mind for every code block you write in phase files. The review step (Step 9) will flag any code blocks that deviate from these codebase patterns.

## Step 8: Create Phases (Iterative)

For EACH phase, in order:

### 8a: Add Row to Phase Table

Edit `plan.md` to add the phase row:

```markdown
| **01** | [Title](./phase-01-slug.md) | [Focus] | Pending |
```

### 8b: Create Phase File

Write the complete phase file following PHASE-TEMPLATE.md exactly.

**File:** `plans/{folder}/phase-{NN}-{slug}.md`

**Include `skill` in Frontmatter** — without it, the implementer won't know which skill to invoke and will use generic patterns instead of project-specific ones.

| Phase Type | Skill Value |
|------------|-------------|
| Database schema, migrations, RLS | `postgres-expert` |
| Server actions, services, API | `server-action-builder` |
| React forms with validation | `react-form-builder` |
| E2E tests | `playwright-e2e` |
| React components/pages | `vercel-react-best-practices` |
| UI/UX focused work | `web-design-guidelines` |

**Example frontmatter:**
```yaml
---
title: "Phase 01 - Database Schema"
skill: postgres-expert
status: pending
---
```

For phases spanning multiple concerns, list the primary skill or use comma-separated values:
```yaml
skill: react-form-builder, vercel-react-best-practices
```

**Required sections** (from template):
1. YAML Frontmatter (title, description, status, dependencies, tags, dates, **skill**)
2. Overview (brief description, single-sentence Goal)
3. Context & Workflow (How the Project Uses This, User Workflow, Problem Being Solved)
4. Prerequisites & Clarifications (Questions for User with Context/Assumptions/Impact)
5. Requirements (Functional + Technical)
6. Decision Log (phase-specific ADRs)
7. Implementation Steps — **Step 0: TDD is first**
8. Verifiable Acceptance Criteria (Critical Path, Quality Gates, Integration)
9. Quality Assurance (Manual Testing, Automated Testing, Performance Testing, Review Checklist)
10. Dependencies (Upstream, Downstream, External)
11. Completion Gate (Sign-off checklist)

Code blocks in phases should match codebase patterns from Step 7 — not memory, not generic examples. Generic code blocks cause the implementer to write code that doesn't follow project conventions, creating rework. If you don't remember the exact pattern, re-read the reference file from Step 7 before writing the code block.

### 8c: Update Task Status

Mark the phase task as completed, move to next phase.

### 8d: Validate Phase Quality

After creating each phase file, run these validators to catch issues immediately (before review agents get involved). Run them via Bash — they read from stdin but only need `{"cwd": "."}`:

```bash
# Check for skeleton/placeholder content (catches the Phase 17 lesson)
echo '{"cwd":"."}' | uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_no_placeholders.py \
  --directory plans/{folder} --extension .md

# Check TDD tasks appear before implementation tasks
echo '{"cwd":"."}' | uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_tdd_tasks.py \
  --directory plans/{folder} --extension .md

# Confirm the phase file was actually created
echo '{"cwd":"."}' | uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_new_file.py \
  --directory plans/{folder} --extension .md
```

If any validator exits non-zero, fix the issue before moving to the next phase. Placeholder content and missing TDD steps are the two most common causes of rework during implementation.

### 8e: Repeat

Continue until all phases are created.

## Step 9: Review Complete Plan

Independent review agents catch template gaps and codebase compliance issues that self-review misses. The user depends on this step to prevent discovering problems during implementation when they're 10x more costly to fix.

Spawn **one agent per file** for thorough reviews. See [Delegation Guide](references/delegation-guide.md) for:
- Batching rules (max 4 concurrent agents to prevent context window blowout)
- Agent prompt templates for plan.md and phase reviews
- Anti-patterns to avoid when delegating
- Batching examples for plans of different sizes

## Step 10: Report Summary

After reviews complete, provide the user with:

1. **Folder location:** `plans/{YYMMDD}-{feature-name}/`
2. **Files created:**
   - plan.md
   - phase-01-*.md through phase-NN-*.md
   - reviews/planning/ folder with review files
3. **Review status:**
   - Plan.md: template score (X/11)
   - Each phase: template score (X/12) + codebase score (N issues by severity)
4. **Overall verdict:** Ready/Not Ready for implementation
5. **Critical issues** (if any) that need addressing before implementation

## Resuming After Context Compact

If you notice context was compacted or you're unsure of current progress:

1. Run `TaskList` to see all tasks and their status
2. Find the `in_progress` task — that's where you were
3. Run `TaskGet {id}` on that task to read full details
4. Continue from that task — don't restart from the beginning

Tasks persist across compacts. The task list is your source of truth for progress, not your memory.

**Pattern for every work session:**
```
TaskList → find in_progress or first pending → TaskGet → continue work → TaskUpdate (completed) → next task
```

## Troubleshooting

### Context Window Overflow

**Symptom:** Agent loses track of phases mid-creation, produces incomplete or inconsistent output.

**Cause:** Too many phases being created without task tracking, or review agents spawned without batching.

**Fix:** Follow Task List pattern in Step 4 — mark tasks complete as you go. For reviews, batch agents in groups of 4 per the [Delegation Guide](references/delegation-guide.md).

### Missing Template Sections

**Symptom:** Review agents flag missing sections in plan.md or phase files.

**Cause:** Template not read before writing, or sections skipped during creation.

**Fix:** Re-read the template (`references/PLAN-TEMPLATE.md` or `references/PHASE-TEMPLATE.md`) and add the missing sections. Each section exists because omitting it caused implementation problems.

### Agent Delegation Failures

**Symptom:** Review agents skip the `/review-plan` skill invocation or produce superficial reviews.

**Cause:** Vague delegation prompts that don't specify the skill to invoke or what success looks like.

**Fix:** Use the exact prompt templates from [Delegation Guide](references/delegation-guide.md). Include both the imperative command AND explanation of what the review entails.

## Patterns That Prevent User-Reported Failures

The user experienced each of these failures. Understanding the harm helps you avoid them:

| Pattern to Avoid | Harm When Ignored |
|------------------|-------------------|
| Writing code blocks without reading codebase | Phases contain wrong patterns, caught late during implementation |
| Large multi-concern phases | Phases exceed context window, work gets lost mid-implementation |
| Skipping template sections | The user created templates so requirements aren't re-explained each time |
| Assuming instead of asking | Wrong plan built on false premises, hours of wasted effort |
| Self-reviewing the plan | Blind spots missed; `/review-plan` catches template AND codebase deviations |
| Vague delegation prompts | Agents misinterpret and skip skill invocation |
| Folder without date prefix | Folders become unsorted chronologically |
| Skipping TaskList check | Duplicates tasks if resuming after context compact |

## Template Locations

- Plan: `references/PLAN-TEMPLATE.md`
- Phase: `references/PHASE-TEMPLATE.md`

These templates are auto-loaded into your context from the skill's `references/` folder. Match them section-by-section.
