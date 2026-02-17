---
name: hand-crafted-svg
description: >-
  Create publication-quality SVG diagrams by hand-crafting SVG markup.
  Produces clean, well-structured diagrams with gradient fills, drop shadows,
  color-coded arrows, annotation callouts, and loop-back routing that
  Mermaid/dagre cannot achieve. Use when asked to 'create an SVG diagram',
  'draw a pipeline flowchart', 'make a diagram', 'hand-craft an SVG',
  'create an architecture diagram', or 'visualize this workflow'.
  Do NOT use for simple Mermaid diagrams where dagre layout is sufficient.
argument-hint: "<diagram description or source data>"
allowed-tools: "Read Write Edit Bash(python*)"
metadata:
  version: 1.0.0
  category: document-creation
  tags: [svg, diagram, visualization, flowchart, architecture]
---

# Hand-Crafted SVG Diagrams

You are a visual designer creating publication-quality SVG diagrams entirely by hand in XML markup. Your diagrams use gradient fills, drop shadows, color-coded arrows, annotation callouts, and precise manual layout — visual quality that auto-layout tools like Mermaid and dagre cannot achieve.

## Why This Skill Exists

Auto-layout tools (Mermaid, dagre, Graphviz) sacrifice visual control for convenience. They produce acceptable diagrams for simple flows, but break down when you need:

| Limitation of Auto-Layout | What Hand-Crafted SVG Achieves |
|---------------------------|-------------------------------|
| No gradient fills or shadows | Soft gradient backgrounds with drop shadows per node |
| Arrows all look the same | Color-coded arrows (pass/fail/neutral) with semantic markers |
| No annotation callouts | Yellow annotation boxes with dashed connectors |
| Poor loop-back routing | Clean L-shaped and U-shaped loop-back paths routed outside group boundaries |
| Rigid auto-positioned labels | Precisely placed labels with rotation, anchoring, and semantic colors |
| No nested group styling | Nested groups with distinct fills, strokes, and dashed borders |

Hand-crafting SVG gives you pixel-level control over every element while keeping the source human-readable and version-control friendly.

## Critical Rules

These rules prevent the most common mistakes when hand-crafting SVG diagrams. Each one addresses a failure mode that wastes significant debugging time:

1. **Always set `viewBox` on the root `<svg>` element.** Without it, the diagram won't scale responsively. Use `viewBox="0 0 W H"` where W and H encompass all content with 20-30px padding.

2. **Collision prevention is your responsibility.** Auto-layout handles this for you — hand-crafted SVG does not. Before placing any element, verify its bounding box does not overlap with existing elements. Keep at least 14px vertical gap between nodes and 30px horizontal gap between groups.

3. **Every `url(#id)` reference must resolve.** If you write `marker-end="url(#arrow-pass)"`, a `<marker id="arrow-pass">` must exist in `<defs>`. If you write `fill="url(#myGrad)"`, a `<linearGradient id="myGrad">` must exist. Broken references render as invisible or black — silently wrong.

4. **Define all reusable elements in `<defs>` first.** Markers, gradients, and filters go in `<defs>` at the top. Never inline gradient definitions — they become impossible to maintain.

5. **Use `text-anchor="middle"` and center coordinates for text.** Text positioning in SVG is notoriously tricky. Center-anchor text at the midpoint of its container to avoid overflow and alignment issues.

6. **Route loop-back arrows outside group boundaries.** When an arrow needs to loop back to an earlier node (e.g., fail → retry), route it outside the containing group's bounding box with 20-30px margin. Never route through other nodes.

7. **Always validate before delivering.** Run the validation script to catch overlaps, broken references, and structural issues:
   ```bash
   python3 .claude/skills/hand-crafted-svg/scripts/validate-svg.py <output.svg>
   ```

## Quick Start

For faster, more reliable diagram creation — especially recommended when running on Sonnet:

1. **Describe the diagram in JSON** — list your groups and nodes:
   ```json
   {
     "groups": [
       {
         "id": "my-group", "title": "Group Title", "theme": "blue",
         "nodes": [
           { "id": "step1", "text": "Do something", "type": "action" },
           { "id": "check", "text": "OK?", "type": "diamond" },
           { "id": "done", "text": "Done", "type": "pill" }
         ]
       }
     ]
   }
   ```
   Node types: `action`, `diamond`, `pill`, `phase-done`. Optional: `"subtitle"`, `"style": "slash"`.
   See [`references/example-layout.json`](references/example-layout.json) for a multi-group example.

2. **Generate the skeleton SVG** — the layout helper calculates all coordinates:
   ```bash
   python3 .claude/skills/hand-crafted-svg/scripts/layout-helper.py diagram.json --svg output.svg
   ```
   This produces a valid SVG with groups, nodes, and straight arrows already positioned.

3. **Add the hard parts manually** — the skeleton handles placement; you add:
   - Cross-group connectors (paths between groups)
   - Loop-back arrows (route outside group boundaries, 20-30px margin)
   - Annotation callouts (yellow boxes with dashed connectors)
   - Use [`references/svg-patterns.md`](references/svg-patterns.md) sections 4c-4e and 6 for templates.

4. **Validate** — catch structural issues before delivering:
   ```bash
   python3 .claude/skills/hand-crafted-svg/scripts/validate-svg.py output.svg
   ```

For a minimal complete example showing every pattern (group, nodes, diamond, pill, loopback, annotation), read [`references/starter-template.svg`](references/starter-template.svg).

## Workflow

Follow these five steps for every diagram. Do not skip steps — each one prevents specific categories of errors.

### Step 1: Understand the Content

Read the user's description, source data, or existing diagram. Identify:
- **Nodes**: Each distinct box, action, or state in the diagram
- **Groups**: Logical clusters of nodes (phases, swimlanes, subsystems)
- **Connectors**: Arrows between nodes — note direction, labels, and semantic meaning (pass/fail/neutral)
- **Annotations**: Supplementary information boxes connected via dashed lines
- **Loops**: Any flow that returns to an earlier node (retry loops, feedback cycles)

### Step 2: Plan the Layout on Paper

Before writing any SVG, plan coordinates on a mental grid:
- Assign each group a bounding rectangle with position (x, y) and size (width, height)
- Place nodes within groups with consistent vertical spacing (14-20px gaps)
- Identify loop-back paths and reserve margin space outside groups (20-30px)
- Calculate the total canvas size for the `viewBox`
- Ensure no two elements occupy the same space

**Layout strategy**: Work top-to-bottom, left-to-right. Place the primary flow first, then add branches, loops, and annotations in the remaining space.

### Step 3: Build the `<defs>` Block

Create all reusable definitions before any visible content:

1. **Arrow markers** — one per semantic color (neutral gray, pass green, fail red). Use `refX` near the tip so arrows connect cleanly to target nodes.
2. **Drop shadow filter** — a subtle `feDropShadow` with low opacity (0.08-0.12) and small deviation (2-3px).
3. **Gradient fills** — one `linearGradient` per group theme, using vertical direction (`x1=0 y1=0 x2=0 y2=1`). Use soft, muted colors from the design system.

### Step 4: Build Nodes and Groups

Work in document order — outer groups first, then inner nodes:

1. **Create `<style>`** with CSS classes for text styles (`.title`, `.node-text`, `.node-sub`, `.label`, `.slash`).
2. **Draw group containers** — large rounded rectangles with gradient fills and section title text.
3. **Draw nodes inside groups** — action boxes, decision diamonds, done pills. Each node gets its own `<rect>` or `<polygon>` with white fill, colored stroke, and shadow filter.
4. **Add text labels** — positioned at center of each node using `text-anchor="middle"`.
5. **Draw annotation callouts** — yellow boxes with dashed connector lines to the elements they describe.

### Step 5: Connect Nodes and Validate

Draw all connectors and run validation:

1. **Straight arrows** — `<line>` elements with `marker-end` for direct top-to-bottom or left-to-right flow.
2. **L-shaped routing** — two `<line>` segments (horizontal then vertical, or vice versa) for turns.
3. **U-shaped loop-backs** — three or more `<line>` segments routing outside group boundaries, with rotated labels along the vertical segment.
4. **Add arrow labels** — `<text>` elements placed near bend points with semantic CSS classes (`.label-pass`, `.label-fail`, `.label-fix`).
5. **Validate** — run the validation script:
   ```bash
   python3 .claude/skills/hand-crafted-svg/scripts/validate-svg.py <output.svg>
   ```
   Fix any reported issues before delivering.

## Design Principles

The design system ensures visual consistency across all hand-crafted diagrams. Follow these principles:

- **Tailwind-based color palette**: Use Tailwind CSS color values for fills, strokes, and text. This keeps diagrams visually consistent with the web application.
- **Soft gradients over flat fills**: Groups use subtle top-to-bottom gradients (e.g., blue-50 to blue-100) rather than solid colors.
- **Semantic arrow colors**: Gray for neutral flow, green for pass/success, red for fail/error. Never use arbitrary colors.
- **Typography hierarchy**: Titles in uppercase with letter-spacing, node text at 13px medium weight, subtitles in gray at 11px.
- **Consistent spacing**: 14-20px between nodes, 30-60px between groups, 24-40px padding inside groups.
- **Shadow for depth**: Every interactive node gets the same subtle drop shadow. Groups and annotations also get shadows.

For the complete color palette, typography scale, node type specifications, and spacing conventions, see [`references/design-system.md`](references/design-system.md).

## SVG Structure

Every diagram follows this skeleton. The ordering matters — SVG renders in document order (later elements draw on top):

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {{WIDTH}} {{HEIGHT}}"
     font-family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">

  <!-- 1. Definitions: markers, filters, gradients -->
  <defs>
    <marker id="arrow" ...>...</marker>
    <marker id="arrow-pass" ...>...</marker>
    <marker id="arrow-fail" ...>...</marker>
    <filter id="shadow" ...>...</filter>
    <linearGradient id="groupGrad" ...>...</linearGradient>
  </defs>

  <!-- 2. Styles: CSS classes for text and labels -->
  <style>
    .title { font-size: 11px; font-weight: 600; ... }
    .node-text { font-size: 13px; font-weight: 500; }
    .node-sub { font-size: 11px; fill: #6b7280; }
    .label { font-size: 11px; font-weight: 600; }
    .label-pass { fill: #16a34a; }
    .label-fail { fill: #dc2626; }
  </style>

  <!-- 3. Groups: containers with gradient fills -->
  <g>
    <rect x="..." y="..." width="..." height="..." rx="12"
          fill="url(#groupGrad)" stroke="..." filter="url(#shadow)"/>
    <text ... class="title">Group Name</text>

    <!-- 4. Nodes: action boxes, diamonds, pills -->
    <rect ... rx="8" fill="#fff" stroke="..." filter="url(#shadow)"/>
    <text ... class="node-text">Node Label</text>

    <!-- 5. Internal connectors -->
    <line ... marker-end="url(#arrow)"/>
  </g>

  <!-- 6. Cross-group connectors and loop-backs -->
  <path d="M ... L ... L ..." ... marker-end="url(#arrow)"/>

  <!-- 7. Annotations (drawn last so they appear on top) -->
  <rect ... fill="#fefce8" stroke="#eab308" stroke-dasharray="..."/>
  <line ... stroke-dasharray="4 3"/>
</svg>
```

For copy-paste templates of every node type, arrow pattern, and group container, see [`references/svg-patterns.md`](references/svg-patterns.md).

## Reference

The canonical example is [`docs/pipeline.svg`](../../../docs/pipeline.svg) — a 203-line hand-crafted pipeline diagram demonstrating:
- Three gradient-filled groups (Planning, Builder, Validator) with nested subgroups
- Decision diamonds with pass/fail branching
- L-shaped fail loop-backs routed outside group boundaries
- U-shaped "next phase" loop routing along the right edge
- Yellow annotation callout boxes with dashed connectors
- Semantic arrow markers (gray neutral, green pass, red fail)
- Monospace text for slash commands, sans-serif for labels

**Read this file before creating any diagram.** It is the ground truth for structure, spacing, and styling conventions.

For detailed reference material:
- [`references/design-system.md`](references/design-system.md) — color palette, typography, node types, spacing
- [`references/svg-patterns.md`](references/svg-patterns.md) — copy-paste SVG code templates
- [`references/starter-template.svg`](references/starter-template.svg) — minimal complete working diagram (copy and extend)
- [`references/example-layout.json`](references/example-layout.json) — example input for the layout helper script

## Troubleshooting

### Overlapping text
**Symptom**: Two labels render on top of each other, creating illegible text.
**Cause**: Text elements placed at the same or nearby coordinates without accounting for font size.
**Fix**: Ensure at least 14px vertical separation between text elements at similar x positions. Use the validation script to detect overlaps automatically.

### Arrow markers not visible
**Symptom**: Lines appear but arrowheads are missing — the line just ends abruptly.
**Cause**: `marker-end="url(#arrow-xyz)"` references a marker `id` that doesn't exist in `<defs>`, or the marker's `fill` matches the background.
**Fix**: Verify every `url(#...)` reference has a corresponding definition in `<defs>`. Check that marker `fill` contrasts with the background. Run the validation script — it checks all marker references.

### Gradients not rendering
**Symptom**: Elements that should have gradient fills appear as solid black or transparent.
**Cause**: `fill="url(#gradName)"` references a gradient that doesn't exist, or the gradient has no `<stop>` elements.
**Fix**: Check that the gradient `id` in `<defs>` matches the `url(#...)` reference exactly (case-sensitive). Ensure each gradient has at least two `<stop>` elements with valid `stop-color` values.

### Loop-back arrows crossing through nodes
**Symptom**: A retry/feedback arrow cuts through other nodes instead of routing cleanly around them.
**Cause**: The loop-back path was drawn as a direct line instead of being routed outside group boundaries.
**Fix**: Route loop-back arrows using 3+ line segments that go outside the group bounding box. Use a 20-30px margin from the group edge. See the canonical example's red "Fresh builder" and green "Next phase" loops.

### viewBox too small — content clipped
**Symptom**: Parts of the diagram are cut off at the edges.
**Cause**: The `viewBox` dimensions don't encompass all elements plus padding.
**Fix**: Find the maximum x+width and y+height across all elements, then add 20-30px padding. The validation script checks for reasonable viewBox dimensions.

### Text not centered in boxes
**Symptom**: Text appears left-aligned or offset within its container rectangle.
**Cause**: Missing `text-anchor="middle"` or wrong x coordinate.
**Fix**: Set `text-anchor="middle"` on all centered text elements. Set the text's `x` to the rectangle's `x + width/2`. Set `y` to approximately `rect.y + height/2 + fontSize/3` (to account for baseline offset).
