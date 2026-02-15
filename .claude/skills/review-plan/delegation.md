# Delegating Review to Sub-Agents

Instructions for the **parent agent** spawning review sub-agents. This file is NOT for the forked review agent itself.

## When Delegating This Skill

When using the Task tool to delegate this skill to a sub-agent, be explicit that:
1. The agent must invoke the Skill tool FIRST
2. This is a TEMPLATE + CODEBASE COMPLIANCE review (not a content quality review)
3. Each agent reviews ONE file only

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
→ 12 agents return ~5KB each = 60KB+ of results flooding context
→ Agent loses track, produces garbage summaries
→ Earlier results get compressed/lost
```

**Rules:**
1. **Maximum 4 agents at a time** — no exceptions
2. **`run_in_background: true`** on every Task tool call
3. **`TaskOutput` with `block: true`** to wait for completion — do NOT read streaming output
4. **Wait for ALL agents in a batch** to complete before spawning the next batch
5. **Summarize each batch** before moving to the next (prevents context bloat)

---

## Prompt Templates for Sub-Agents

**For plan.md review:**

```
Your FIRST action must be to call the Skill tool with:
- skill: "review-plan"
- args: "plans/[plan-folder]"

Do NOT do any other work until you have invoked that skill.

The skill will instruct you to:
1. Read the PLAN-TEMPLATE.md reference
2. Compare every section in plan.md against the template
3. Write a review file with pass/fail for each required section

This is a template compliance review — missing sections cause implementation failures downstream. Check every section exists.

After the skill completes, report the verdict and missing section count.
```

**For single phase review:**

```
Your FIRST action must be to call the Skill tool with:
- skill: "review-plan"
- args: "plans/[plan-folder] phase 01"

Do NOT do any other work until you have invoked that skill.

The skill will instruct you to:
1. Read the PHASE-TEMPLATE.md reference
2. Compare every section in phase-01-*.md against the template
3. Verify code blocks against actual codebase patterns
4. Auto-fix Critical/High/Medium issues directly in the phase file
5. Write a review file with pass/fail for EACH required section AND codebase issues

This is a TEMPLATE + CODEBASE COMPLIANCE review with auto-fix (Critical/High/Medium).
Check every section exists AND verify code blocks match real codebase patterns.

After the skill completes, report the verdict, section count, codebase issue count,
auto-fixed items, and any Low improvement suggestions for the main agent.
```

**Anti-patterns:**

```
# WRONG - Vague, agent skips skill
Use the Skill tool to invoke the /review-plan skill...

# WRONG - No context, agent does superficial review
Your FIRST action must be to call the Skill tool with:
- skill: "review-plan"
- args: "plans/folder phase 01"
# Missing: what the review involves

# WRONG - Multiple phases causes superficial reviews
- args: "plans/folder phases 01-08"
- args: "plans/folder all"

# WRONG - Spawning all agents at once
for phase in 01..12: spawn review agent  ← context blowout
```

The key difference: Include BOTH the imperative command AND explanation of what the review entails. One file per agent.

---

## Auto-Fix Behavior

Auto-fix of Critical, High, and Medium codebase issues is built into the `/review-plan` skill (Step 9). When delegating reviews, you do NOT need to add separate fix instructions. The forked agent will:

1. Complete the full review (template + codebase compliance)
2. Auto-fix Critical, High, and Medium issues directly in the phase file
3. Return a summary including what was fixed, what was deferred, and Low improvement suggestions

The delegation prompts above already account for this — no additional "review AND fix" composite prompts needed.

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
