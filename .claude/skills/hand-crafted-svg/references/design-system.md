# SVG Design System Reference

Canonical reference extracted from `docs/pipeline.svg`. All values are exact — use these when creating new diagrams.

## Color Palette

### Semantic Roles

| Role | Hex | Tailwind | Usage |
|------|-----|----------|-------|
| **Blue (planning)** | `#1d4ed8` | blue-700 | Planning group title |
| | `#2563eb` | blue-600 | Slash command text (planning) |
| | `#1e40af` | blue-800 | Diamond label text (planning) |
| | `#3b82f6` | blue-500 | Planning node stroke |
| | `#93c5fd` | blue-300 | Planning group stroke |
| **Purple (builder)** | `#7c3aed` | violet-600 | Builder group title |
| | `#5b21b6` | violet-800 | Builder node text |
| | `#8b5cf6` | violet-500 | Builder node stroke |
| | `#a78bfa` | violet-400 | Builder group stroke |
| **Green (validator/pass)** | `#15803d` | green-700 | Validator title, done pill text |
| | `#166534` | green-800 | Phase done text, validator verify text |
| | `#16a34a` | green-600 | Pass labels (`.label-pass`), done pill stroke |
| | `#22c55e` | green-500 | Pass arrows, validator node stroke, phase done stroke |
| | `#4ade80` | green-400 | Validator group stroke |
| **Red (fail)** | `#dc2626` | red-600 | Fail labels (`.label-fail`) |
| | `#ef4444` | red-500 | Fail arrows, fail arrow marker |
| **Orange (fix)** | `#d97706` | amber-600 | Fix labels (`.label-fix`) |
| **Yellow (annotations)** | `#a16207` | yellow-700 | Annotation title text |
| | `#eab308` | yellow-500 | Annotation border, dashed connectors |
| | `#fefce8` | yellow-50 | Annotation fill |
| **Gray (neutral)** | `#374151` | gray-700 | Implementation title, neutral node text |
| | `#6b7280` | gray-500 | Default arrows, `.node-sub` text, neutral strokes |
| | `#d1d5db` | gray-300 | Outer container stroke |
| | `#fafafa` | gray-50 | Outer container fill |
| **White** | `#ffffff` | white | All node fills |

### Gradient Definitions

All gradients are **vertical** (`x1="0" y1="0" x2="0" y2="1"`):

| ID | Start (top) | End (bottom) | Usage |
|----|-------------|-------------|-------|
| `planGrad` | `#eff6ff` (blue-50) | `#dbeafe` (blue-200) | Planning group fill |
| `buildGrad` | `#faf5ff` (purple-50) | `#f3e8ff` (purple-100) | Builder subgroup fill |
| `validateGrad` | `#f0fdf4` (green-50) | `#dcfce7` (green-200) | Validator subgroup fill |

### Terminal State Fills

| State | Fill | Stroke | Stroke Width | Text Color |
|-------|------|--------|-------------|------------|
| Done pill | `#dcfce7` (green-200) | `#16a34a` (green-600) | 2 | `#15803d` (green-700), bold |
| Phase done | `#f0fdf4` (green-50) | `#22c55e` (green-500) | 1.5 | `#166534` (green-800) |

---

## Typography

### Font Stacks

| Role | Font Family |
|------|-------------|
| **System (default)** | `Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` |
| **Monospace** | `'JetBrains Mono', 'Fira Code', monospace` |

Set the system font on the root `<svg>` element via `font-family`. Monospace is only used in the `.slash` class.

### CSS Classes

```css
.title     { font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
.node-text { font-size: 13px; font-weight: 500; }
.node-sub  { font-size: 11px; fill: #6b7280; }
.label     { font-size: 11px; font-weight: 600; }
.slash     { font-size: 13px; font-weight: 700; font-family: 'JetBrains Mono', 'Fira Code', monospace; }
```

### Conditional Label Colors

```css
.label-pass { fill: #16a34a; }   /* green-600 */
.label-fail { fill: #dc2626; }   /* red-600 */
.label-fix  { fill: #d97706; }   /* amber-600 */
```

### Size Scale

| Size | Usage |
|------|-------|
| 9px | Micro text (e.g., "shutdown team" subtitle under done pill) |
| 10px | Small inline labels, diamond text overrides, annotation items, gate checks |
| 11px | `.title`, `.node-sub`, `.label`, diamond label text |
| 12px | Slash commands with subtitle (e.g., `/audit-plan`), result diamond text, `/code-review` |
| 13px | `.node-text`, `.slash` — primary content size |

---

## SVG Defs

### Shadow Filter

Applied to all nodes and group containers:

```xml
<filter id="shadow" x="-4%" y="-4%" width="108%" height="108%">
  <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.08"/>
</filter>
```

- Subtle downward shadow (dy=1)
- Very light opacity (0.08)
- Applied via `filter="url(#shadow)"`

### Arrow Markers

Three arrow markers share identical geometry, differing only in fill color:

```xml
<marker id="arrow"      viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280"/>
</marker>
<marker id="arrow-fail"  ... fill="#ef4444"/>
<marker id="arrow-pass"  ... fill="#22c55e"/>
```

| Marker | Fill | Usage |
|--------|------|-------|
| `#arrow` | `#6b7280` (gray-500) | Default flow arrows |
| `#arrow-pass` | `#22c55e` (green-500) | Pass/success arrows |
| `#arrow-fail` | `#ef4444` (red-500) | Fail/error arrows |

---

## Node Types

### Action Node (standard)

Top-level nodes within major groups.

```xml
<rect x="70" y="64" width="180" height="40" rx="8"
      fill="#fff" stroke="#3b82f6" stroke-width="1.5" filter="url(#shadow)"/>
<text x="160" y="88" text-anchor="middle" class="slash" fill="#2563eb">/create-plan</text>
```

| Attribute | Value | Notes |
|-----------|-------|-------|
| Shape | `<rect>` | |
| Corner radius | `rx="8"` | |
| Fill | `#fff` | Always white |
| Stroke width | `1.5` | |
| Stroke color | Varies by phase | Blue `#3b82f6` (planning), Gray `#6b7280` (orchestrator) |
| Shadow | `filter="url(#shadow)"` | Always applied |
| Typical sizes | 180x40, 200x38 | Planning nodes, orchestrator nodes |

**With subtitle** (taller node):

```xml
<rect ... width="180" height="44" .../>
<text ... y="278" class="slash" font-size="12">/audit-plan</text>
<text ... y="293" class="node-sub">for plans with 3+ phases</text>
```

- Height increases to 44px
- Primary text uses `font-size="12"` (smaller than standard 13px slash)
- Subtitle 15px below primary text, uses `.node-sub`

### Inner Node (subgroup)

Nodes inside Builder/Validator subgroups. Smaller and lighter than action nodes.

```xml
<rect x="412" y="310" width="242" height="34" rx="6"
      fill="#fff" stroke="#8b5cf6" stroke-width="1" filter="url(#shadow)"/>
<text x="533" y="331" text-anchor="middle" class="node-text" fill="#5b21b6">
  Find reference + domain skill
</text>
```

| Attribute | Value | Notes |
|-----------|-------|-------|
| Shape | `<rect>` | |
| Corner radius | `rx="6"` | Tighter than action nodes |
| Fill | `#fff` | Always white |
| Stroke width | `1` | Thinner than action nodes |
| Stroke color | Varies by subgroup | Purple `#8b5cf6` (builder), Green `#22c55e` (validator) |
| Size | 242x34 | Consistent across all inner nodes |
| Text class | `.node-text` or `.slash` | Slash for skill-invocable nodes |

### Decision Diamond

```xml
<polygon points="160,188 215,213 160,238 105,213"
         fill="#fff" stroke="#3b82f6" stroke-width="1.5"/>
<text x="160" y="216" text-anchor="middle" class="node-text" fill="#1e40af" font-size="11">
  Passes?
</text>
```

| Attribute | Value | Notes |
|-----------|-------|-------|
| Shape | `<polygon>` with 4 points | Points: top, right, bottom, left |
| Fill | `#fff` | Always white |
| Stroke width | `1.5` | |
| Stroke color | Varies by context | Blue (planning), Gray (orchestrator) |
| No shadow | — | Diamonds omit the shadow filter |
| Text size | 10-12px | Overrides `.node-text` default of 13px |

**Point geometry:** `center_x, center_y - half_h` → `center_x + half_w, center_y` → `center_x, center_y + half_h` → `center_x - half_w, center_y`

Typical diamond dimensions:

| Diamond | Width | Height | Half-W | Half-H |
|---------|-------|--------|--------|--------|
| Planning "Passes?" | 110 | 50 | 55 | 25 |
| "All done?" | 116 | 52 | 58 | 26 |
| "Phase gate" | 124 | 48 | 62 | 24 |
| "Result" | 120 | 50 | 60 | 25 |

### Done Pill (terminal success)

```xml
<rect x="616" y="128" width="140" height="32" rx="16"
      fill="#dcfce7" stroke="#16a34a" stroke-width="2" filter="url(#shadow)"/>
<text x="686" y="146" text-anchor="middle" class="node-text" fill="#15803d" font-weight="700">
  All done
</text>
<text x="686" y="157" text-anchor="middle" class="node-sub" font-size="9">shutdown team</text>
```

| Attribute | Value | Notes |
|-----------|-------|-------|
| Corner radius | `rx="16"` | Full pill shape (rx = height/2) |
| Fill | `#dcfce7` (green-200) | Colored fill — not white |
| Stroke | `#16a34a` (green-600), width `2` | Thicker than standard |
| Text | Bold (`font-weight="700"`) | Emphasizes terminal state |
| Subtitle | 9px, `.node-sub` | Optional micro text below |

### Phase Done Box

```xml
<rect x="660" y="653" width="130" height="32" rx="8"
      fill="#f0fdf4" stroke="#22c55e" stroke-width="1.5" filter="url(#shadow)"/>
<text x="725" y="673" text-anchor="middle" class="node-text" fill="#166534">Phase done</text>
```

| Attribute | Value | Notes |
|-----------|-------|-------|
| Corner radius | `rx="8"` | Standard action node radius |
| Fill | `#f0fdf4` (green-50) | Light green — not white |
| Stroke | `#22c55e` (green-500) | |
| Size | 130x32 | Compact |

### Annotation Callout

```xml
<rect x="700" y="210" width="175" height="72" rx="6"
      fill="#fefce8" stroke="#eab308" stroke-width="1" filter="url(#shadow)"/>
<text x="788" y="228" text-anchor="middle" class="title" fill="#a16207" font-size="10">
  Gate Checks
</text>
<text x="788" y="243" text-anchor="middle" class="node-sub" font-size="10">Flow audit exists</text>
<text x="788" y="256" text-anchor="middle" class="node-sub" font-size="10">No placeholder content</text>
<text x="788" y="269" text-anchor="middle" class="node-sub" font-size="10">Phase review passes</text>
```

| Attribute | Value | Notes |
|-----------|-------|-------|
| Corner radius | `rx="6"` | Same as inner nodes |
| Fill | `#fefce8` (yellow-50) | Warm yellow tint |
| Stroke | `#eab308` (yellow-500), width `1` | Thin border |
| Title | `.title` at 10px, fill `#a16207` | Smaller than group titles |
| Items | `.node-sub` at 10px | Stacked at ~13px line height |
| Width | 175 | Consistent across all annotations |
| Height | 72-74 | Varies by content (3-4 items) |

**Connected via dashed line** to related element:

```xml
<line x1="562" y1="234" x2="698" y2="234"
      stroke="#eab308" stroke-width="1" stroke-dasharray="4 3"/>
```

---

## Group Containers

### Major Group (phase container)

Top-level colored region representing a pipeline phase.

```xml
<rect x="30" y="20" width="260" height="300" rx="12"
      fill="url(#planGrad)" stroke="#93c5fd" stroke-width="1.5" filter="url(#shadow)"/>
<text x="160" y="46" text-anchor="middle" class="title" fill="#1d4ed8">Planning</text>
```

| Attribute | Value | Notes |
|-----------|-------|-------|
| Corner radius | `rx="12"` | Largest radius in the system |
| Fill | Gradient (`url(#planGrad)`) | Phase-specific gradient |
| Stroke width | `1.5` | |
| Stroke color | Phase-specific | Blue `#93c5fd`, Gray `#d1d5db` |
| Shadow | `filter="url(#shadow)"` | Applied |
| Title position | 26px below top edge | Centered horizontally |

### Subgroup (Builder/Validator)

Nested group inside the outer container, distinguished by dashed stroke.

```xml
<rect x="388" y="278" width="290" height="194" rx="10"
      fill="url(#buildGrad)" stroke="#a78bfa" stroke-width="1.5" stroke-dasharray="6 3"/>
<text x="533" y="298" text-anchor="middle" class="title" fill="#7c3aed">
  Builder (ephemeral, per phase)
</text>
```

| Attribute | Value | Notes |
|-----------|-------|-------|
| Corner radius | `rx="10"` | Between inner nodes (6) and groups (12) |
| Fill | Gradient | Phase-specific gradient |
| Stroke width | `1.5` | |
| Stroke pattern | `stroke-dasharray="6 3"` | **Dashed** — distinguishes from major groups |
| No shadow | — | Subgroups omit the shadow filter |
| Title position | 20px below top edge | |

### Outer Container (orchestrator shell)

Contains the entire implementation phase including subgroups.

```xml
<rect x="342" y="20" width="585" height="694" rx="12"
      fill="#fafafa" stroke="#d1d5db" stroke-width="1.5" filter="url(#shadow)"/>
<text x="634" y="46" text-anchor="middle" class="title" fill="#374151">
  /implement — Orchestrator Loop
</text>
```

| Attribute | Value | Notes |
|-----------|-------|-------|
| Corner radius | `rx="12"` | Same as major groups |
| Fill | `#fafafa` (gray-50) | Flat color, no gradient |
| Stroke | `#d1d5db` (gray-300) | Neutral |
| Shadow | Applied | |

---

## Arrow System

### Straight Arrows (default flow)

Simple vertical or horizontal connections between adjacent nodes:

```xml
<line x1="160" y1="104" x2="160" y2="124"
      stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow)"/>
```

- Stroke width: `1.5` (consistent across all arrows)
- Marker always on the end: `marker-end="url(#arrow)"`
- Color matches semantic role (gray for default, green for pass, red for fail)

### L-Shaped Routing (two segments)

Used when an arrow needs to turn 90 degrees, e.g., from a diamond's side to a horizontal target:

```xml
<!-- PASS → right to "Phase done" -->
<line x1="593" y1="669" x2="658" y2="669" stroke="#22c55e" stroke-width="1.5" marker-end="url(#arrow-pass)"/>
```

For two-segment L-shapes, use two `<line>` elements. Only the **final segment** gets `marker-end`.

### U-Shaped Loopback (three segments)

Routes outside the group boundaries to loop back to an earlier node. Three `<line>` segments form a U:

**Fail loop (left side):**

```xml
<!-- Left from diamond → down → right into builder -->
<line x1="473" y1="669" x2="365" y2="669" stroke="#ef4444" stroke-width="1.5"/>
<line x1="365" y1="669" x2="365" y2="327" stroke="#ef4444" stroke-width="1.5"/>
<line x1="365" y1="327" x2="410" y2="327" stroke="#ef4444" stroke-width="1.5" marker-end="url(#arrow-fail)"/>
```

**Pass loop (right side):**

```xml
<!-- Right from "Phase done" → up → left into "Find unblocked" -->
<line x1="790" y1="669" x2="905" y2="669" stroke="#22c55e" stroke-width="1.5"/>
<line x1="905" y1="669" x2="905" y2="83"  stroke="#22c55e" stroke-width="1.5"/>
<line x1="905" y1="83"  x2="602" y2="83"  stroke="#22c55e" stroke-width="1.5" marker-end="url(#arrow-pass)"/>
```

**Planning fix loop (left side, tighter):**

```xml
<!-- Left from diamond → up → right into /review-plan -->
<line x1="105" y1="213" x2="56" y2="213" stroke="#ef4444" stroke-width="1.5"/>
<line x1="56"  y1="213" x2="56" y2="146" stroke="#ef4444" stroke-width="1.5"/>
<line x1="56"  y1="146" x2="68" y2="146" stroke="#ef4444" stroke-width="1.5" marker-end="url(#arrow-fail)"/>
```

### Path-Based Routing (complex multi-turn)

For routes that require 3+ turns, use a `<path>` instead of multiple lines:

```xml
<!-- Planning → Implementation (L-shaped with 4 segments) -->
<path d="M 160 306 L 160 340 L 315 340 L 315 83 L 398 83"
      fill="none" stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow)"/>
```

Paths are cleaner when there are 4+ direction changes.

### Arrow Labels

Labels are placed near the bend point or alongside the arrow:

```xml
<!-- Horizontal label (above the line) -->
<text x="620" y="662" class="label label-pass">PASS</text>

<!-- Vertical label (rotated 90 degrees) -->
<text x="913" y="376" class="label label-pass" transform="rotate(-90 913 376)">Next phase</text>

<!-- Small inline "No" label -->
<text x="512" y="194" class="node-sub" font-size="10">No</text>
```

- **Horizontal labels**: Positioned above the line (y offset ~7px above line y)
- **Vertical labels**: Use `transform="rotate(-90 x y)"` centered on the rotation point
- **Diamond exit labels**: Adjacent to the exit point, use `.label` class + semantic color class

### Dashed Connectors (annotation links)

```xml
<line x1="562" y1="234" x2="698" y2="234"
      stroke="#eab308" stroke-width="1" stroke-dasharray="4 3"/>
```

- Stroke width: `1` (thinner than arrows)
- Dash pattern: `4 3` (4px dash, 3px gap)
- Color: `#eab308` (yellow-500, matches annotation border)
- No marker/arrowhead

---

## Spacing Conventions

### Group Padding

| Container Type | Left/Right Padding | Top to Title | Top to First Node | Bottom Padding |
|----------------|-------------------|-------------|-------------------|----------------|
| Major group (Planning) | 40px | 26px | 44px | 16px |
| Outer container | 58px (left) | 26px | 44px | — |
| Subgroup (Builder/Validator) | 24px | 20px | 32px | 14-28px |

### Vertical Gaps Between Nodes

| Context | Gap (px) | Notes |
|---------|----------|-------|
| Action nodes in major group | 22 | Includes arrow (20px line + 2px marker) |
| Inner nodes in subgroup | 16 | Tighter spacing, 14px arrow + 2px |
| Subgroup to subgroup | 22 | Builder bottom to Validator top |
| Diamond to next node (default) | 18-22 | Standard flow |
| Diamond to next node (with label) | 40 | Extra space for label text |
| Last node to Result diamond | 20 | Standard |
| Phase gate to subgroup | 20 | With pass arrow |

### Horizontal Gaps

| Between | Gap (px) |
|---------|----------|
| Major groups (Planning → Implementation) | 52 |
| Subgroup edge → Annotation box | 46 (node edge to annotation edge) |

### Loop-Back Margins

Loopback arrows route *outside* their containing group. The margin is the distance from the arrow to the nearest group edge:

| Loop | Arrow X | Nearest Edge | Margin |
|------|---------|-------------|--------|
| Planning fix (left) | x=56 | Group left at x=30 | 26px |
| Fail loop (left) | x=365 | Outer left at x=342 | 23px |
| Pass loop (right) | x=905 | Outer right at x=927 | 22px |

### Node Dimensions

| Node Type | Width | Height | Notes |
|-----------|-------|--------|-------|
| Planning action | 180 | 40 | Standard slash command nodes |
| Planning action (with sub) | 180 | 44 | Has subtitle text |
| Orchestrator action | 200 | 38 | "Find unblocked phases" |
| Inner node (subgroup) | 242 | 34 | Builder/Validator step nodes |
| Done pill | 140 | 32 | Terminal success state |
| Phase done | 130 | 32 | Per-phase completion |
| Annotation box | 175 | 72-74 | Varies by number of items |

### Text Vertical Centering

Text is vertically centered within nodes by positioning the baseline:

| Node Height | Text Y Offset from Top | Formula |
|-------------|----------------------|---------|
| 40px | 24px | `node_y + 24` |
| 38px | 18px (line 1), 31px (line 2) | Two-line layout |
| 34px | 21px | `node_y + 21` |
| 32px | 18px | `node_y + 18` |

### Canvas

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 950 734"
     font-family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">
```

- ViewBox starts at origin (0, 0)
- Content starts at approximately x=30, y=20 (top-left margin)
- Right margin: ~23px (950 - 927)
- Bottom margin: ~20px (734 - 714)

---

## Hierarchy Summary

```
rx="12"  →  Major group, Outer container (top-level containers)
rx="10"  →  Subgroup (nested, dashed stroke)
rx="8"   →  Action node, Phase done (standard interactive elements)
rx="6"   →  Inner node, Annotation (smaller elements)
rx="16"  →  Done pill (full pill shape, terminal state)
```

```
stroke-width="2"    →  Done pill only (terminal emphasis)
stroke-width="1.5"  →  Groups, action nodes, arrows, diamonds
stroke-width="1"    →  Inner nodes, annotations, dashed connectors
```

```
Solid stroke        →  Major groups, all nodes, arrows
Dashed "6 3"        →  Subgroups (Builder, Validator)
Dashed "4 3"        →  Annotation connectors
```
