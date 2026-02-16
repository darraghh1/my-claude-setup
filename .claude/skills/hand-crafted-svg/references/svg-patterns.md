# SVG Patterns Reference

Reusable SVG code templates extracted from production diagrams. Each pattern is copy-paste ready with `{{PLACEHOLDER}}` values for coordinates, colors, and text content.

---

## 1. Defs Block

The `<defs>` block defines reusable elements — markers (arrowheads), filters (shadows), and gradients — that render only when referenced via `url(#id)`. Place this immediately after the opening `<svg>` tag.

```xml
<defs>
  <!-- ── Arrow Markers ──────────────────────────────────────────────
       Each marker defines an arrowhead shape. Create one per color.
       refX/refY position the tip. markerWidth/Height scale the head.
       orient="auto" rotates to match line direction.                -->
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="8" markerHeight="8" orient="auto">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="{{ARROW_COLOR}}"/>
    <!-- fill: #6b7280 (gray), #22c55e (green/pass), #ef4444 (red/fail) -->
  </marker>

  <!-- ── Drop Shadow Filter ─────────────────────────────────────────
       Creates subtle depth. x/y/width/height expand the filter region
       beyond the element bounds so the shadow isn't clipped.
       flood-opacity controls shadow intensity (0.08 = very subtle).  -->
  <filter id="shadow" x="-4%" y="-4%" width="108%" height="108%">
    <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.08"/>
  </filter>

  <!-- ── Linear Gradient ────────────────────────────────────────────
       Vertical gradient (x1/y1=top, x2/y2=bottom). Use for group
       background fills. Create one per phase/group color scheme.     -->
  <linearGradient id="{{GRADIENT_ID}}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{{COLOR_LIGHT}}"/>
    <stop offset="100%" stop-color="{{COLOR_MEDIUM}}"/>
  </linearGradient>
  <!-- Example color pairs:
       Blue:   #eff6ff / #dbeafe  (planning)
       Purple: #faf5ff / #f3e8ff  (building)
       Green:  #f0fdf4 / #dcfce7  (validation)
       Gray:   #fafafa / #f5f5f5  (neutral container) -->
</defs>
```

### Common Marker Set

Most diagrams need three arrow markers. Here is the standard set:

```xml
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="8" markerHeight="8" orient="auto">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280"/>
  </marker>
  <marker id="arrow-pass" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="8" markerHeight="8" orient="auto">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#22c55e"/>
  </marker>
  <marker id="arrow-fail" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="8" markerHeight="8" orient="auto">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444"/>
  </marker>
  <filter id="shadow" x="-4%" y="-4%" width="108%" height="108%">
    <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.08"/>
  </filter>
</defs>
```

---

## 2. Style Block

CSS classes for consistent text rendering. Place after `<defs>`, before content elements.

```xml
<style>
  /* ── Group/section headings ─────────────────────────────────────
     Uppercase, small, bold — used for phase titles and labels.     */
  .title {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  /* ── Primary node text ──────────────────────────────────────────
     Medium weight, readable size — the main label inside nodes.    */
  .node-text { font-size: 13px; font-weight: 500; }

  /* ── Secondary/subtitle text ────────────────────────────────────
     Smaller, gray — descriptive text below the main label.         */
  .node-sub { font-size: 11px; fill: #6b7280; }

  /* ── Edge labels ────────────────────────────────────────────────
     Small bold text placed near arrows (Yes/No, PASS/FAIL).       */
  .label { font-size: 11px; font-weight: 600; }
  .label-pass { fill: #16a34a; }
  .label-fail { fill: #dc2626; }
  .label-fix  { fill: #d97706; }

  /* ── Monospace slash-command text ────────────────────────────────
     For /command names inside action nodes.                        */
  .slash {
    font-size: 13px;
    font-weight: 700;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
  }
</style>
```

---

## 3. Node Templates

### 3a. Action Node

A rounded rectangle with white fill, colored stroke, and drop shadow. The primary building block for process steps.

```xml
<!-- Action Node ─────────────────────────────────────────────────────
     {{X}}, {{Y}}:      top-left corner position
     {{W}}, {{H}}:      width and height (common: 180x40, 242x34)
     {{STROKE_COLOR}}:  border color (#3b82f6 blue, #8b5cf6 purple, #22c55e green)
     {{TEXT_COLOR}}:     text fill (#2563eb blue, #5b21b6 purple, #166534 green)
     {{TEXT_CLASS}}:     "node-text" for plain, "slash" for /commands   -->
<rect x="{{X}}" y="{{Y}}" width="{{W}}" height="{{H}}" rx="8"
      fill="#fff" stroke="{{STROKE_COLOR}}" stroke-width="1.5"
      filter="url(#shadow)"/>
<text x="{{TEXT_X}}" y="{{TEXT_Y}}" text-anchor="middle"
      class="{{TEXT_CLASS}}" fill="{{TEXT_COLOR}}">{{LABEL}}</text>
```

**With subtitle** (two lines of text inside):

```xml
<rect x="{{X}}" y="{{Y}}" width="{{W}}" height="{{H}}" rx="8"
      fill="#fff" stroke="{{STROKE_COLOR}}" stroke-width="1.5"
      filter="url(#shadow)"/>
<text x="{{TEXT_X}}" y="{{TEXT_Y}}" text-anchor="middle"
      class="{{TEXT_CLASS}}" fill="{{TEXT_COLOR}}">{{LABEL}}</text>
<text x="{{TEXT_X}}" y="{{TEXT_Y_SUB}}" text-anchor="middle"
      class="node-sub">{{SUBTITLE}}</text>
<!-- TEXT_Y_SUB is typically TEXT_Y + 15 -->
```

### 3b. Decision Diamond

A rotated square (polygon with 4 points) used for yes/no or pass/fail branching.

```xml
<!-- Decision Diamond ────────────────────────────────────────────────
     Center at ({{CX}}, {{CY}}).
     {{HALF_W}}: horizontal radius (typical: 55-60)
     {{HALF_H}}: vertical radius (typical: 25-26)
     Points: top, right, bottom, left
     {{STROKE_COLOR}}: #3b82f6 (blue), #6b7280 (gray)                -->
<polygon points="{{CX}},{{TOP}} {{RIGHT}},{{CY}} {{CX}},{{BOTTOM}} {{LEFT}},{{CY}}"
         fill="#fff" stroke="{{STROKE_COLOR}}" stroke-width="1.5"/>
<text x="{{CX}}" y="{{LABEL_Y}}" text-anchor="middle"
      class="node-text" fill="{{TEXT_COLOR}}" font-size="11">{{LABEL}}</text>
<!-- LABEL_Y is typically CY + 4 to vertically center text
     TOP    = CY - HALF_H
     BOTTOM = CY + HALF_H
     RIGHT  = CX + HALF_W
     LEFT   = CX - HALF_W -->
```

**Computed example** (center at 500, 144 with half-width 58, half-height 26):

```xml
<polygon points="500,118 558,144 500,170 442,144"
         fill="#fff" stroke="#6b7280" stroke-width="1.5"/>
<text x="500" y="148" text-anchor="middle"
      class="node-text" fill="#374151" font-size="10">All done?</text>
```

### 3c. Done Pill

A highly-rounded rectangle indicating completion. The large `rx` value creates the pill shape.

```xml
<!-- Done Pill ───────────────────────────────────────────────────────
     rx="16" creates the pill shape (half of height).
     Green color scheme signals success/completion.
     {{X}}, {{Y}}: top-left position
     {{W}}: width (typically 120-140)                                 -->
<rect x="{{X}}" y="{{Y}}" width="{{W}}" height="32" rx="16"
      fill="#dcfce7" stroke="#16a34a" stroke-width="2"
      filter="url(#shadow)"/>
<text x="{{TEXT_X}}" y="{{TEXT_Y}}" text-anchor="middle"
      class="node-text" fill="#15803d" font-weight="700">{{LABEL}}</text>
<!-- Optional subtitle below the main label: -->
<text x="{{TEXT_X}}" y="{{TEXT_Y_SUB}}" text-anchor="middle"
      class="node-sub" font-size="9">{{SUBTITLE}}</text>
<!-- TEXT_X = X + W/2, TEXT_Y = Y + 18, TEXT_Y_SUB = TEXT_Y + 11 -->
```

### 3d. Phase Done Box

A subtler completion indicator — lighter green with thinner stroke than the done pill.

```xml
<!-- Phase Done Box ──────────────────────────────────────────────────
     Lighter green (#f0fdf4) background distinguishes from the
     full-completion pill. rx="8" keeps standard rounded corners.
     {{X}}, {{Y}}: top-left position                                  -->
<rect x="{{X}}" y="{{Y}}" width="{{W}}" height="32" rx="8"
      fill="#f0fdf4" stroke="#22c55e" stroke-width="1.5"
      filter="url(#shadow)"/>
<text x="{{TEXT_X}}" y="{{TEXT_Y}}" text-anchor="middle"
      class="node-text" fill="#166534">{{LABEL}}</text>
<!-- TEXT_X = X + W/2, TEXT_Y = Y + 20 -->
```

### 3e. Annotation Callout

A yellow-tinted box for side notes, tips, or checklist items.

```xml
<!-- Annotation Callout ──────────────────────────────────────────────
     Yellow scheme signals "informational, not in main flow."
     Place to the right or left of the main flow, connected
     with a dashed line.
     {{X}}, {{Y}}: top-left position
     {{W}}, {{H}}: width and height (sized to fit content)
     {{LINE_SPACING}}: vertical gap between text lines (typically 13-15) -->
<rect x="{{X}}" y="{{Y}}" width="{{W}}" height="{{H}}" rx="6"
      fill="#fefce8" stroke="#eab308" stroke-width="1"
      filter="url(#shadow)"/>
<text x="{{TEXT_X}}" y="{{HEADING_Y}}" text-anchor="middle"
      class="title" fill="#a16207" font-size="10">{{HEADING}}</text>
<text x="{{TEXT_X}}" y="{{LINE1_Y}}" text-anchor="middle"
      class="node-sub" font-size="10">{{LINE_1}}</text>
<text x="{{TEXT_X}}" y="{{LINE2_Y}}" text-anchor="middle"
      class="node-sub" font-size="10">{{LINE_2}}</text>
<text x="{{TEXT_X}}" y="{{LINE3_Y}}" text-anchor="middle"
      class="node-sub" font-size="10">{{LINE_3}}</text>
<!-- TEXT_X = X + W/2
     HEADING_Y = Y + 18
     LINE1_Y   = HEADING_Y + 15
     LINE2_Y   = LINE1_Y + 13
     LINE3_Y   = LINE2_Y + 13
     Add/remove <text> lines as needed -->
```

---

## 4. Arrow Templates

### 4a. Straight Down Arrow

Connects two vertically stacked elements.

```xml
<!-- Straight Down Arrow ─────────────────────────────────────────────
     {{X}}:       horizontal center (same as both connected nodes)
     {{Y_START}}: bottom edge of source node
     {{Y_END}}:   top edge of target node
     {{MARKER}}:  "arrow" (gray), "arrow-pass" (green), "arrow-fail" (red) -->
<line x1="{{X}}" y1="{{Y_START}}" x2="{{X}}" y2="{{Y_END}}"
      stroke="{{STROKE_COLOR}}" stroke-width="1.5"
      marker-end="url(#{{MARKER}})"/>
```

**With edge label** (e.g., Yes/No/PASS/FAIL):

```xml
<line x1="{{X}}" y1="{{Y_START}}" x2="{{X}}" y2="{{Y_END}}"
      stroke="{{STROKE_COLOR}}" stroke-width="1.5"
      marker-end="url(#{{MARKER}})"/>
<text x="{{LABEL_X}}" y="{{LABEL_Y}}" class="label {{LABEL_CLASS}}">{{LABEL}}</text>
<!-- LABEL_X: X + 10 (right of line) or X - 10 (left of line)
     LABEL_Y: midpoint between Y_START and Y_END
     LABEL_CLASS: "label-pass", "label-fail", or "label-fix" -->
```

### 4b. Straight Horizontal Arrow

Connects two side-by-side elements.

```xml
<!-- Straight Horizontal Arrow ───────────────────────────────────────
     {{Y}}:       vertical center of both connected nodes
     {{X_START}}: right edge of source node (or diamond tip)
     {{X_END}}:   left edge of target node                            -->
<line x1="{{X_START}}" y1="{{Y}}" x2="{{X_END}}" y2="{{Y}}"
      stroke="{{STROKE_COLOR}}" stroke-width="1.5"
      marker-end="url(#{{MARKER}})"/>
<text x="{{LABEL_X}}" y="{{LABEL_Y}}" class="label {{LABEL_CLASS}}">{{LABEL}}</text>
<!-- LABEL_X: midpoint of X_START and X_END
     LABEL_Y: Y - 7 (above the line) -->
```

### 4c. L-Shape Arrow (Right-Angle Routing)

Routes around nodes when source and target aren't aligned. Uses a `<path>` for multi-segment routing, or individual `<line>` segments.

**Path approach** (single element, cleaner):

```xml
<!-- L-Shape Arrow (path) ────────────────────────────────────────────
     Routes from ({{X1}},{{Y1}}) through intermediate points to
     ({{X_END}},{{Y_END}}). Only the last segment gets the arrowhead.
     M = move to start, L = line to next point.                       -->
<path d="M {{X1}} {{Y1}} L {{X1}} {{Y_TURN}} L {{X_END}} {{Y_TURN}}"
      fill="none" stroke="{{STROKE_COLOR}}" stroke-width="1.5"
      marker-end="url(#{{MARKER}})"/>
```

**Multi-line approach** (individual segments, arrowhead on last):

```xml
<!-- L-Shape Arrow (lines) ───────────────────────────────────────────
     Three segments: horizontal out, vertical transit, horizontal in.
     Only the LAST segment gets marker-end.                           -->
<line x1="{{X1}}" y1="{{Y1}}" x2="{{X_CORNER}}" y2="{{Y1}}"
      stroke="{{STROKE_COLOR}}" stroke-width="1.5"/>
<line x1="{{X_CORNER}}" y1="{{Y1}}" x2="{{X_CORNER}}" y2="{{Y2}}"
      stroke="{{STROKE_COLOR}}" stroke-width="1.5"/>
<line x1="{{X_CORNER}}" y1="{{Y2}}" x2="{{X_END}}" y2="{{Y2}}"
      stroke="{{STROKE_COLOR}}" stroke-width="1.5"
      marker-end="url(#{{MARKER}})"/>
```

**Concrete example** — diamond left tip to loopback:

```xml
<!-- Fix loop: diamond left → outside → back up → into target node -->
<line x1="105" y1="213" x2="56" y2="213" stroke="#ef4444" stroke-width="1.5"/>
<line x1="56" y1="213" x2="56" y2="146" stroke="#ef4444" stroke-width="1.5"/>
<line x1="56" y1="146" x2="68" y2="146" stroke="#ef4444" stroke-width="1.5"
      marker-end="url(#arrow-fail)"/>
<text x="44" y="183" class="label label-fix"
      transform="rotate(-90 44 183)">Fix</text>
<!-- rotate(-90 X Y) renders vertical text, reading bottom-to-top -->
```

### 4d. U-Shape Loopback Arrow

Routes along the outside boundary of the diagram to loop back to an earlier node. Uses 3 segments forming a U or C shape.

```xml
<!-- U-Shape Loopback ────────────────────────────────────────────────
     Routes: source → right margin → up to target row → left into target.
     {{X_START}}: right edge of source node
     {{Y_START}}: vertical center of source node
     {{X_MARGIN}}: x-coordinate of the outer routing channel
     {{Y_END}}:   vertical center of target node
     {{X_END}}:   right edge of target node
     Three segments: rightward, upward, leftward (arrow on last).     -->
<line x1="{{X_START}}" y1="{{Y_START}}" x2="{{X_MARGIN}}" y2="{{Y_START}}"
      stroke="{{STROKE_COLOR}}" stroke-width="1.5"/>
<line x1="{{X_MARGIN}}" y1="{{Y_START}}" x2="{{X_MARGIN}}" y2="{{Y_END}}"
      stroke="{{STROKE_COLOR}}" stroke-width="1.5"/>
<line x1="{{X_MARGIN}}" y1="{{Y_END}}" x2="{{X_END}}" y2="{{Y_END}}"
      stroke="{{STROKE_COLOR}}" stroke-width="1.5"
      marker-end="url(#{{MARKER}})"/>
<!-- Vertical label alongside the long vertical segment: -->
<text x="{{LABEL_X}}" y="{{LABEL_Y}}" class="label {{LABEL_CLASS}}"
      transform="rotate(-90 {{LABEL_X}} {{LABEL_Y}})">{{LABEL}}</text>
<!-- LABEL_X: X_MARGIN + 8 (to the right of the line)
     LABEL_Y: midpoint of Y_START and Y_END -->
```

**Concrete example** — "Next phase" green loopback:

```xml
<line x1="790" y1="669" x2="905" y2="669" stroke="#22c55e" stroke-width="1.5"/>
<line x1="905" y1="669" x2="905" y2="83" stroke="#22c55e" stroke-width="1.5"/>
<line x1="905" y1="83" x2="602" y2="83" stroke="#22c55e" stroke-width="1.5"
      marker-end="url(#arrow-pass)"/>
<text x="913" y="376" class="label label-pass"
      transform="rotate(-90 913 376)">Next phase</text>
```

### 4e. Multi-Segment Path Arrow

For complex routing that crosses between groups, a single `<path>` is cleaner than multiple `<line>` elements.

```xml
<!-- Multi-Segment Path ──────────────────────────────────────────────
     Routes through multiple waypoints. Uses M (move) and L (line-to).
     fill="none" is required — without it, the path interior fills.   -->
<path d="M {{X1}} {{Y1}} L {{X2}} {{Y2}} L {{X3}} {{Y3}} L {{X4}} {{Y4}}"
      fill="none" stroke="{{STROKE_COLOR}}" stroke-width="1.5"
      marker-end="url(#{{MARKER}})"/>
```

**Concrete example** — planning group to implementation group:

```xml
<path d="M 160 306 L 160 340 L 315 340 L 315 83 L 398 83"
      fill="none" stroke="#6b7280" stroke-width="1.5"
      marker-end="url(#arrow)"/>
```

---

## 5. Group Template

Groups visually contain related nodes. A rounded rectangle with gradient fill, a title, and inner content.

```xml
<!-- Group Container ─────────────────────────────────────────────────
     {{X}}, {{Y}}:          top-left of group boundary
     {{W}}, {{H}}:          total width and height
     {{GRADIENT_ID}}:       gradient from defs block (or solid fill color)
     {{STROKE_COLOR}}:      border color matching the phase color
     {{TITLE}}, {{TITLE_X}}, {{TITLE_Y}}: group heading
     {{TITLE_COLOR}}:       text color for heading

     Inner content starts below the title. Inset child nodes by
     ~24px horizontally and ~44px vertically from the group origin.   -->
<g>
  <rect x="{{X}}" y="{{Y}}" width="{{W}}" height="{{H}}" rx="12"
        fill="url(#{{GRADIENT_ID}})" stroke="{{STROKE_COLOR}}"
        stroke-width="1.5" filter="url(#shadow)"/>
  <text x="{{TITLE_X}}" y="{{TITLE_Y}}" text-anchor="middle"
        class="title" fill="{{TITLE_COLOR}}">{{TITLE}}</text>

  <!-- Child nodes go here, indented within the <g> -->
</g>
<!-- TITLE_X = X + W/2  (horizontally centered)
     TITLE_Y = Y + 26   (below the top edge)
     Children start at approximately Y + 44 -->
```

### Subgroup (Dashed Border)

For nested groups within a main container (e.g., "Builder" within "Implementation"):

```xml
<!-- Subgroup (dashed border) ────────────────────────────────────────
     stroke-dasharray="6 3" creates a dashed border to visually
     distinguish subgroups from the outer container.                  -->
<rect x="{{X}}" y="{{Y}}" width="{{W}}" height="{{H}}" rx="10"
      fill="url(#{{GRADIENT_ID}})" stroke="{{STROKE_COLOR}}"
      stroke-width="1.5" stroke-dasharray="6 3"/>
<text x="{{TITLE_X}}" y="{{TITLE_Y}}" text-anchor="middle"
      class="title" fill="{{TITLE_COLOR}}">{{TITLE}}</text>
<!-- Nodes inside use smaller rx="6" and thinner stroke-width="1" -->
```

---

## 6. Annotation Template

Annotations are informational callouts placed beside the main flow, connected by dashed lines.

### Full Annotation (Callout + Dashed Connector)

```xml
<!-- ── Annotation with Dashed Connector ─────────────────────────────
     1. The callout box (yellow, positioned beside the main flow)
     2. A dashed line connecting the callout to the relevant node

     {{CALLOUT_X}}, {{CALLOUT_Y}}: top-left of callout box
     {{CALLOUT_W}}, {{CALLOUT_H}}: callout dimensions
     {{CONNECTOR_X1}}, {{CONNECTOR_Y1}}: start of dashed line (near main flow)
     {{CONNECTOR_X2}}, {{CONNECTOR_Y2}}: end of dashed line (at callout edge)
     stroke-dasharray="4 3" creates dashes: 4px dash, 3px gap          -->

<!-- Callout box -->
<rect x="{{CALLOUT_X}}" y="{{CALLOUT_Y}}" width="{{CALLOUT_W}}" height="{{CALLOUT_H}}"
      rx="6" fill="#fefce8" stroke="#eab308" stroke-width="1"
      filter="url(#shadow)"/>
<text x="{{TEXT_X}}" y="{{HEADING_Y}}" text-anchor="middle"
      class="title" fill="#a16207" font-size="10">{{HEADING}}</text>
<text x="{{TEXT_X}}" y="{{LINE1_Y}}" text-anchor="middle"
      class="node-sub" font-size="10">{{LINE_1}}</text>
<text x="{{TEXT_X}}" y="{{LINE2_Y}}" text-anchor="middle"
      class="node-sub" font-size="10">{{LINE_2}}</text>

<!-- Dashed connector line -->
<line x1="{{CONNECTOR_X1}}" y1="{{CONNECTOR_Y1}}"
      x2="{{CONNECTOR_X2}}" y2="{{CONNECTOR_Y2}}"
      stroke="#eab308" stroke-width="1" stroke-dasharray="4 3"/>
<!-- Connector is typically horizontal, from a diamond's right tip
     or a node's edge to the callout's left edge.
     TEXT_X    = CALLOUT_X + CALLOUT_W / 2
     HEADING_Y = CALLOUT_Y + 18
     LINE1_Y   = HEADING_Y + 15
     LINE2_Y   = LINE1_Y + 13 -->
```

---

## Quick Reference: Color Palette

| Role | Fill | Stroke | Text |
|------|------|--------|------|
| **Blue (planning)** | `#fff` | `#3b82f6` | `#2563eb` / `#1d4ed8` |
| **Purple (building)** | `#fff` | `#8b5cf6` | `#5b21b6` / `#7c3aed` |
| **Green (validation)** | `#fff` | `#22c55e` | `#166534` / `#15803d` |
| **Gray (neutral)** | `#fff` | `#6b7280` | `#374151` |
| **Yellow (annotation)** | `#fefce8` | `#eab308` | `#a16207` |
| **Green done pill** | `#dcfce7` | `#16a34a` | `#15803d` |
| **Green phase done** | `#f0fdf4` | `#22c55e` | `#166534` |
| **Red (fail)** | — | `#ef4444` | `#dc2626` |

## Quick Reference: Gradient Pairs

| Name | Light (top) | Medium (bottom) |
|------|-------------|-----------------|
| `planGrad` (blue) | `#eff6ff` | `#dbeafe` |
| `buildGrad` (purple) | `#faf5ff` | `#f3e8ff` |
| `validateGrad` (green) | `#f0fdf4` | `#dcfce7` |

## Quick Reference: Sizing Conventions

| Element | Typical Dimensions |
|---------|-------------------|
| Action node (standard) | `180 x 40`, `rx="8"` |
| Action node (in subgroup) | `242 x 34`, `rx="6"` |
| Decision diamond | half-width `55-60`, half-height `25-26` |
| Done pill | `140 x 32`, `rx="16"` |
| Phase done box | `130 x 32`, `rx="8"` |
| Annotation callout | `175 x 72-74`, `rx="6"` |
| Group container | `rx="12"`, inset children `24px` h / `44px` v |
| Subgroup | `rx="10"`, dashed border |
| Arrow gap | `18-22px` between node bottom and next node top |
