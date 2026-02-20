# MCP Tools -- Prefer Over Manual Alternatives

MCP server tools are available as **direct tool calls** -- just like `Read`, `Grep`, or `Bash`. They are NOT CLI commands. Do NOT run them via `claude mcp call` or any shell command. Call them directly as tools.

**CORRECT** -- call the tool directly:
```
Tool: mcp__playwright__browser_snapshot
Parameters: {}
```

**WRONG** -- do NOT shell out:
```
Bash: claude mcp call playwright browser_snapshot ...  # WRONG -- not a CLI command
```

## MCP Server Overview

| Server | Prefix | Purpose | When to Use Instead of... |
|--------|--------|---------|--------------------------|
| **Playwright** | `mcp__playwright__` | Live browser interaction, form filling, screenshots | Manual browser testing |
| **Context7** | `mcp__context7__` | Library/framework documentation | Googling docs, outdated training data |
| **Tavily** | `mcp__tavily__` | Web search, URL extraction, site crawling | `WebSearch`, `WebFetch` for complex queries |
| **Sequential Thinking** | `mcp__sequential-thinking__` | Structured multi-step reasoning | Unstructured debugging of complex problems |
| **Draw.io** | `mcp__drawio__` | Create/edit diagrams with browser preview | Hand-crafting SVG, manual diagram tools |

---

## Playwright MCP

For live browser interaction -- navigating pages, clicking buttons, filling forms, taking screenshots.

| Key Rule | Why |
|----------|-----|
| **Always `browser_snapshot` before interacting** | Gives `ref` values needed for click/type/hover |
| **Prefer snapshot over screenshot** | Structured accessibility tree vs opaque image |
| **Use `browser_wait_for` for async pages** | Pages may not have rendered yet after navigation |

**Do NOT use for writing Playwright test code** -- use the `playwright-e2e` skill instead. This is for live browser control.

---

## Context7 MCP

For querying up-to-date library and framework documentation.

| Key Rule | Why |
|----------|-----|
| **Always `resolve-library-id` first** | Must resolve library name to `/org/project` ID before querying |
| **Max 3 calls per tool per question** | Avoid excessive API usage |
| **Be specific in queries** | "Next.js 15 middleware auth" beats "middleware" |

### Common Library IDs (skip resolve for these)

| Library | ID |
|---------|-----|
| Next.js | `/vercel/next.js` |
| React | `/facebook/react` |
| Supabase JS | `/supabase/supabase-js` |
| TanStack Query | `/tanstack/query` |
| Zod | `/colinhacks/zod` |

**Do NOT use for general web search** -- use Tavily.

---

## Tavily MCP

For web search, content extraction, site crawling, and multi-source research.

| Key Rule | Why |
|----------|-----|
| **Start with `tavily_search`** | Low cost, fast -- sufficient for most questions |
| **Use `tavily_research` sparingly** | Very expensive -- multi-source synthesis |
| **Include the year in queries** | "topic 2026" gets current results |
| **`tavily_map` before `tavily_crawl`** | Understand site structure before extracting content |

**Do NOT use for library docs** -- use Context7.

---

## Sequential Thinking MCP

For structured multi-step reasoning on complex problems. Single tool: `mcp__sequential-thinking__sequentialthinking`.

| Key Rule | Why |
|----------|-----|
| **Only use for genuinely complex problems** | Simple problems don't need structured reasoning |
| **Use `isRevision: true` to correct earlier thoughts** | Maintains coherent reasoning chain |
| **Use `branchFromThought` for alternatives** | Explore "what if?" without losing main thread |
| **Start with `totalThoughts: 5`** | Adjust with `needsMoreThoughts: true` if needed |

### When to Use

- Bug with 3+ possible causes needing elimination
- Architectural decision with competing trade-offs
- Root cause analysis requiring hypothesis testing

### When NOT to Use

- Simple errors with clear stack traces
- Straightforward implementation decisions
- Problems with known solutions

---

## Parallel MCP Calls

Claude defaults to sequential MCP tool calls even when tools are independent. For multi-tool workflows, explicitly mark independent calls for parallel execution:

```
**Run these in parallel** (they are independent):
- `mcp__context7__searchDocs` -> library docs
- `mcp__tavily__tavily_search` -> web results
```

Independent MCP calls (different servers, no data dependencies) should always run in parallel to reduce latency.

---

## When NOT to Use MCP Tools

- **Writing SQL/migrations** -- use the `postgres-expert` skill instead
- **Building application code** -- use `service-builder`, `server-action-builder`, `react-form-builder`
- **Reading a specific known file** -- `Read` is faster when you already know the exact path
- **Broad codebase search** -- `Grep`/`Glob` are more flexible for arbitrary pattern matching
- **Writing Playwright test code** -- use the `playwright-e2e` skill (not the Playwright MCP server)
