# Delegating Code Review to Sub-Agents

Instructions for the **parent agent** spawning code review sub-agents. This file is NOT for the forked review agent itself.

## When Delegating This Skill

When using the Task tool to delegate this skill to sub-agents:

1. The agent must invoke the Skill tool FIRST
2. Each agent reviews ONE phase only
3. Include explanation of what the review entails (not just "run the skill")

---

## Sub-Agent Batching Rules

**Never have more than 4 concurrent review agents. Context window blowout is the #1 failure mode.**

When reviewing multiple phases, you MUST follow this pattern:

```
# CORRECT: Spawn 4, wait for ALL 4 to complete, then spawn next 4
Batch 1: Spawn agents for phases 01, 02, 03, 04 (run_in_background: true)
         → Wait: TaskOutput block: true for ALL 4
         → Read results, summarize
Batch 2: Spawn agents for phases 05, 06, 07, 08 (run_in_background: true)
         → Wait: TaskOutput block: true for ALL 4
         → Read results, summarize
```

```
# WRONG: Spawning all at once blows context window
Spawn agents for phases 01-12 simultaneously
→ 12 agents return ~8KB each = 96KB+ of results flooding context
→ Agent loses track, produces garbage summaries
```

**Rules:**
1. **Maximum 4 agents at a time** — no exceptions
2. **`run_in_background: true`** on every Task tool call
3. **`TaskOutput` with `block: true`** to wait for completion — do NOT read streaming output
4. **Wait for ALL agents in a batch** to complete before spawning the next batch
5. **Summarize each batch** before moving to the next (prevents context bloat)

---

## Prompt Template for Delegating a Single Phase Review

```
Your FIRST action must be to call the Skill tool with:
- skill: "code-review"
- args: "plans/[plan-folder]/phase-[NN]-[slug].md"

Do NOT do any other work until you have invoked that skill.

The skill will instruct you to:
1. Read the phase document and extract all implementation steps
2. Find and read reference implementations from the codebase
3. Review each implemented file against the phase spec AND codebase patterns
4. Auto-fix Critical/High/Medium issues directly in the source files
5. Write a review file with completeness check + quality issues at specific file:line locations

This is a code quality + codebase compliance review with auto-fix (Critical/High/Medium).
Check every step was implemented AND verify code matches established codebase patterns.

After the skill completes, report the verdict, issue counts, auto-fixed items,
and any Low improvement suggestions for the main agent.
```

---

## Auto-Fix Behavior

Auto-fix of Critical, High, and Medium issues is built into the `/code-review` skill (Step 7). When delegating reviews, you do NOT need to add separate fix instructions. The forked agent will:

1. Complete the full review (completeness + code quality + security)
2. Auto-fix Critical, High, and Medium issues directly in the source files
3. Return a summary including what was fixed, what was deferred, and Low improvement suggestions

The delegation prompt above already accounts for this — no additional fix instructions needed.

## After a Review Completes — Main Agent Responsibilities

**When the forked review agent returns, the main agent MUST act on the results:**

1. **If there are deferred items** (Critical/High the agent couldn't fix):
   - Present them to the user with the agent's reasoning for deferring
   - Ask the user how to proceed (fix them, skip them, or discuss)
   - Apply fixes the user approves

2. **If there are Medium/Low improvement suggestions:**
   - Medium/Low findings are valid quality items, not optional suggestions
   - Fix all items that are grounded in actual codebase patterns (reference file cited)
   - Only skip items that are clearly hallucinated:
     * Reference non-existent files
     * Contradict actual codebase conventions
     * Flag patterns that the reference file itself uses
   - For Low items, also skip purely cosmetic changes (comment style, whitespace)
   - Present any deferred items to user with rationale

3. **If the verdict is PASS with no deferred items:**
   - Confirm the phase is ready and move on

**Do NOT just echo the review summary and stop.** The review's value comes from acting on its findings. The forked agent does the analysis; the main agent closes the loop by fixing what remains.
