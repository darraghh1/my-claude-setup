# Delegation Guide for Plan Reviews

Instructions for spawning and managing review sub-agents in Step 9 of `/create-plan`.

## Sub-Agent Batching Rules

Spawning more than 4 concurrent agents causes context window blowout — results flood back (~5KB each), earlier context gets compressed, and the agent produces unreliable summaries. This is the #1 failure mode that loses all progress and forces a restart.

1. **Maximum 4 agents at a time** — no exceptions
2. **`run_in_background: true`** on every Task tool call
3. **`TaskOutput` with `block: true`** to wait for completion — do NOT read streaming output
4. **Wait for ALL agents in a batch** to complete before spawning the next batch
5. **Summarize each batch** before moving to the next (prevents context bloat)

### Batching Example for 10 Phases

```
Batch 1 (4 agents): plan.md, phase 01, phase 02, phase 03
         → Wait for all 4 to complete
         → Read results with TaskOutput, summarize

Batch 2 (4 agents): phase 04, phase 05, phase 06, phase 07
         → Wait for all 4 to complete
         → Read results with TaskOutput, summarize

Batch 3 (3 agents): phase 08, phase 09, phase 10
         → Wait for all 3 to complete
         → Read results with TaskOutput, summarize
```

### Wrong Pattern

```
# Spawning all at once blows context window
Spawn agents for plan.md + phases 01-10 simultaneously
→ 11 agents return ~5KB each = 55KB+ of results flooding context
→ Agent loses track, produces garbage summaries
```

## Agent Prompt Templates

### For plan.md Review

```
Task tool parameters:
- subagent_type: "general-purpose"
- description: "Review plan.md"
- prompt: |
    Your FIRST action must be to call the Skill tool with:
    - skill: "review-plan"
    - args: "plans/{folder-name}"

    Do NOT do any other work until you have invoked that skill.

    The skill will instruct you to read the PLAN-TEMPLATE.md reference and compare
    every section in plan.md against it. Skipping this produces reviews that miss
    template gaps, which the user then discovers during implementation.

    This is a TEMPLATE COMPLIANCE review — check every section exists and write
    pass/fail for each of the 11 required sections.

    After the skill completes, report:
    1. The review file location (reviews/planning/plan.md)
    2. The verdict (Ready/Not Ready)
    3. Template score (e.g., "11/11 sections" or "9/11 sections — 2 missing")
```

### For Each Phase Review

```
Task tool parameters:
- subagent_type: "general-purpose"
- description: "Review phase NN"
- prompt: |
    Your FIRST action must be to call the Skill tool with:
    - skill: "review-plan"
    - args: "plans/{folder-name} phase NN"

    Do NOT do any other work until you have invoked that skill.

    The skill will instruct you to read the PHASE-TEMPLATE.md reference and compare
    every section in the phase against it. Skipping template or codebase checks produces
    phases that miss required sections or use wrong patterns — the user then discovers
    these during implementation.

    Specifically:
    1. Compare every section against the template
    2. Read a reference implementation from the codebase
    3. Verify code blocks against actual codebase patterns
    4. Write a review file with template score AND codebase compliance issues

    This is a TEMPLATE + CODEBASE COMPLIANCE review. Check every section exists
    AND verify code blocks match real codebase patterns.

    After the skill completes, report:
    1. The review file location (reviews/planning/phase-NN.md)
    2. The verdict (Ready/Not Ready)
    3. Template score (e.g., "12/12 sections")
    4. Codebase score (e.g., "3 issues: 1 critical, 2 medium")
```

### Batching Example for 5 Phases (6 Reviews, 2 Batches)

```
Batch 1 (4 agents max):
- Agent 1: args: "plans/{folder}"           → plan.md
- Agent 2: args: "plans/{folder} phase 01"  → phase-01
- Agent 3: args: "plans/{folder} phase 02"  → phase-02
- Agent 4: args: "plans/{folder} phase 03"  → phase-03
→ Wait for completion, then read results

Batch 2 (2 agents):
- Agent 5: args: "plans/{folder} phase 04"  → phase-04
- Agent 6: args: "plans/{folder} phase 05"  → phase-05
→ Wait for completion, then read results
```

## Anti-Patterns

These patterns have caused real failures in review delegation. Each was discovered through a failed review session.

### Vague Delegation (Agent Skips Skill Entirely)

```
# WRONG - Agent interprets as "do the review manually"
Use the Skill tool to invoke the /review-plan skill.
Invoke the skill like this:
Skill tool with skill: "review-plan"...
```

### Missing Context (Agent Does Superficial Review)

```
# WRONG - Agent doesn't know what the review involves
Your FIRST action must be to call the Skill tool with:
- skill: "review-plan"
- args: "plans/folder phase 01"
# No explanation of what the skill does or what success looks like
```

### Multiple Files Per Agent (Causes Superficial Reviews)

```
# WRONG - Too much cognitive load
- args: "plans/folder phases 01-08"
- args: "plans/folder all"

# RIGHT - One file per agent
- args: "plans/folder"           → plan.md only
- args: "plans/folder phase 01"  → phase-01 only
```

### Too Many Concurrent Agents

```
# WRONG - Context window blowout
for phase in 01..12: spawn review agent simultaneously

# RIGHT - Batch in groups of 4
Batch 1: phases 01-04, wait, summarize
Batch 2: phases 05-08, wait, summarize
Batch 3: phases 09-12, wait, summarize
```

## Correct Delegation Pattern Includes

1. Imperative command to invoke skill FIRST
2. Explanation that it's a TEMPLATE + CODEBASE COMPLIANCE review (for phases)
3. List of what the skill will instruct them to do (including codebase check)
4. Expected output format (template score + codebase score)
5. ONE file per agent (plan.md OR single phase)
