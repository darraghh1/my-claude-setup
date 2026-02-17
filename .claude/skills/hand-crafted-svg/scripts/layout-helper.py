#!/usr/bin/env python3
"""Layout helper for hand-crafted SVG diagrams.

Calculates node coordinates from a simple JSON description, then outputs
either a human-readable coordinate map or a skeleton SVG with all positions
pre-calculated. This offloads spatial math from the LLM, which can then
focus on adding cross-group connectors, loopbacks, and annotations.

Uses only Python stdlib — no external dependencies.

Usage:
    # Print coordinate map (default)
    python3 layout-helper.py diagram.json

    # Generate skeleton SVG
    python3 layout-helper.py diagram.json --svg output.svg

    # Output machine-readable JSON
    python3 layout-helper.py diagram.json --format json

    # Generate SVG to stdout
    python3 layout-helper.py diagram.json --format svg

Input JSON format — see references/example-layout.json for a complete example:

    {
      "groups": [
        {
          "id": "my-group",
          "title": "Group Title",
          "theme": "blue",
          "nodes": [
            { "id": "step1", "text": "Do something", "type": "action" },
            { "id": "check", "text": "OK?", "type": "diamond" },
            { "id": "done", "text": "Done", "type": "pill" }
          ]
        }
      ]
    }

Node types: action, diamond, pill, phase-done
Optional per-node: "subtitle" (string), "style": "slash" (monospace text)
Themes: blue, purple, green, gray
"""

import argparse
import json
import sys


# ── Design system constants ──────────────────────────────────────────
# Extracted from references/design-system.md

NODE_DIMS = {
    "action":     {"width": 200, "height": 40, "rx": 8},
    "action-sub": {"width": 200, "height": 50, "rx": 8},
    "diamond":    {"half_w": 58, "half_h": 26},
    "pill":       {"width": 140, "height": 32, "rx": 16},
    "pill-sub":   {"width": 140, "height": 42, "rx": 16},
    "phase-done": {"width": 130, "height": 32, "rx": 8},
}

THEMES = {
    "blue": {
        "gradient": "planGrad",
        "stroke": "#93c5fd", "node_stroke": "#3b82f6",
        "text": "#2563eb", "title": "#1d4ed8",
        "grad_start": "#eff6ff", "grad_end": "#dbeafe",
    },
    "purple": {
        "gradient": "buildGrad",
        "stroke": "#a78bfa", "node_stroke": "#8b5cf6",
        "text": "#5b21b6", "title": "#7c3aed",
        "grad_start": "#faf5ff", "grad_end": "#f3e8ff",
    },
    "green": {
        "gradient": "validateGrad",
        "stroke": "#4ade80", "node_stroke": "#22c55e",
        "text": "#166534", "title": "#15803d",
        "grad_start": "#f0fdf4", "grad_end": "#dcfce7",
    },
    "gray": {
        "gradient": "grayGrad",
        "stroke": "#d1d5db", "node_stroke": "#6b7280",
        "text": "#374151", "title": "#374151",
        "grad_start": "#fafafa", "grad_end": "#f5f5f5",
    },
}

# Layout constants
GROUP_PAD_X = 30           # horizontal padding inside group
GROUP_PAD_TOP = 44         # space above first node (includes title)
GROUP_PAD_BOTTOM = 24      # space below last node
NODE_GAP = 18              # vertical gap between nodes
GROUP_GAP = 40             # horizontal gap between groups
CANVAS_PAD = 30            # padding around entire canvas


# ── Layout calculation ───────────────────────────────────────────────

def _node_height(node: dict) -> int:
    """Vertical extent of a node based on type and subtitle presence."""
    ntype = node["type"]
    has_sub = "subtitle" in node
    if ntype == "diamond":
        return NODE_DIMS["diamond"]["half_h"] * 2
    if ntype == "pill":
        return NODE_DIMS["pill-sub" if has_sub else "pill"]["height"]
    if ntype == "phase-done":
        return NODE_DIMS["phase-done"]["height"]
    # action (default)
    return NODE_DIMS["action-sub" if has_sub else "action"]["height"]


def _node_width(node: dict) -> int:
    """Horizontal extent of a node."""
    ntype = node["type"]
    if ntype == "diamond":
        return NODE_DIMS["diamond"]["half_w"] * 2
    if ntype in ("pill", "phase-done"):
        return NODE_DIMS[ntype]["width"]
    has_sub = "subtitle" in node
    return NODE_DIMS["action-sub" if has_sub else "action"]["width"]


def _layout_group(group: dict, x0: int, y0: int) -> dict:
    """Calculate positions for one group and all its child nodes."""
    theme = THEMES.get(group.get("theme", "gray"), THEMES["gray"])
    nodes = group.get("nodes", [])

    # Content dimensions
    content_h = sum(_node_height(n) for n in nodes) + NODE_GAP * max(len(nodes) - 1, 0)
    max_node_w = max((_node_width(n) for n in nodes), default=200)

    group_w = max_node_w + GROUP_PAD_X * 2
    group_h = GROUP_PAD_TOP + content_h + GROUP_PAD_BOTTOM
    cx = x0 + group_w / 2  # horizontal center of group

    result = {
        "id": group["id"],
        "rect": {"x": x0, "y": y0, "width": group_w, "height": group_h, "rx": 12},
        "title": {"x": cx, "y": y0 + 26, "text": group.get("title", "")},
        "theme_name": group.get("theme", "gray"),
        "nodes": [],
    }

    cursor_y = y0 + GROUP_PAD_TOP
    for node in nodes:
        ntype = node["type"]
        has_sub = "subtitle" in node
        nh = _node_height(node)
        nw = _node_width(node)
        nx = cx - nw / 2

        entry: dict = {
            "id": node["id"],
            "type": ntype,
            "text": node.get("text", ""),
            "style": node.get("style", "node-text"),
        }

        if ntype == "diamond":
            hw = NODE_DIMS["diamond"]["half_w"]
            hh = NODE_DIMS["diamond"]["half_h"]
            cy = cursor_y + hh
            entry["center"] = {"x": cx, "y": cy}
            entry["points"] = f"{cx:.0f},{cursor_y} {cx + hw:.0f},{cy:.0f} {cx:.0f},{cursor_y + nh} {cx - hw:.0f},{cy:.0f}"
            entry["text_pos"] = {"x": cx, "y": cy + 4}
            entry["bounds"] = {"top": cursor_y, "bottom": cursor_y + nh, "left": cx - hw, "right": cx + hw}
        else:
            # action, pill, phase-done
            if ntype == "pill":
                rx = NODE_DIMS["pill-sub" if has_sub else "pill"]["rx"]
            elif ntype == "phase-done":
                rx = NODE_DIMS["phase-done"]["rx"]
            else:
                rx = NODE_DIMS["action-sub" if has_sub else "action"]["rx"]

            entry["rect"] = {"x": nx, "y": cursor_y, "width": nw, "height": nh, "rx": rx}
            text_y = cursor_y + (nh / 2 - 2 if has_sub else nh / 2 + 4)
            entry["text_pos"] = {"x": cx, "y": text_y}
            if has_sub:
                entry["subtitle"] = node["subtitle"]
                entry["subtitle_pos"] = {"x": cx, "y": text_y + 15}
            entry["bounds"] = {"top": cursor_y, "bottom": cursor_y + nh, "left": nx, "right": nx + nw}

        result["nodes"].append(entry)
        cursor_y += nh + NODE_GAP

    return result


def calculate_layout(spec: dict) -> dict:
    """Calculate full layout from input specification."""
    groups = spec.get("groups", [])
    layouts = []
    cursor_x = CANVAS_PAD
    max_bottom = 0

    for group in groups:
        layout = _layout_group(group, cursor_x, CANVAS_PAD)
        layouts.append(layout)
        cursor_x += layout["rect"]["width"] + GROUP_GAP
        group_bottom = layout["rect"]["y"] + layout["rect"]["height"]
        max_bottom = max(max_bottom, group_bottom)

    canvas_w = cursor_x - GROUP_GAP + CANVAS_PAD
    canvas_h = max_bottom + CANVAS_PAD

    return {
        "viewBox": f"0 0 {canvas_w:.0f} {canvas_h:.0f}",
        "canvas": {"width": round(canvas_w), "height": round(canvas_h)},
        "groups": layouts,
    }


# ── SVG generation ───────────────────────────────────────────────────

def _svg_defs(themes_used: set[str]) -> list[str]:
    """Generate <defs> block with markers, filter, and gradients."""
    lines = [
        "  <defs>",
        '    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">',
        '      <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280"/>',
        "    </marker>",
        '    <marker id="arrow-pass" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">',
        '      <path d="M 0 0 L 10 5 L 0 10 z" fill="#22c55e"/>',
        "    </marker>",
        '    <marker id="arrow-fail" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">',
        '      <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444"/>',
        "    </marker>",
        '    <filter id="shadow" x="-4%" y="-4%" width="108%" height="108%">',
        '      <feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.08"/>',
        "    </filter>",
    ]
    for tname in sorted(themes_used):
        t = THEMES[tname]
        lines.append(f'    <linearGradient id="{t["gradient"]}" x1="0" y1="0" x2="0" y2="1">')
        lines.append(f'      <stop offset="0%" stop-color="{t["grad_start"]}"/>')
        lines.append(f'      <stop offset="100%" stop-color="{t["grad_end"]}"/>')
        lines.append("    </linearGradient>")
    lines.append("  </defs>")
    return lines


def _svg_styles() -> list[str]:
    """Generate <style> block."""
    return [
        "  <style>",
        "    .title { font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }",
        "    .node-text { font-size: 13px; font-weight: 500; }",
        "    .node-sub { font-size: 11px; fill: #6b7280; }",
        "    .label { font-size: 11px; font-weight: 600; }",
        "    .label-pass { fill: #16a34a; }",
        "    .label-fail { fill: #dc2626; }",
        "    .label-fix { fill: #d97706; }",
        "    .slash { font-size: 13px; font-weight: 700; font-family: 'JetBrains Mono', 'Fira Code', monospace; }",
        "  </style>",
    ]


def _svg_node(node: dict, theme: dict) -> list[str]:
    """Generate SVG for a single node."""
    lines = []
    ntype = node["type"]

    if ntype == "diamond":
        lines.append(f'    <polygon points="{node["points"]}"')
        lines.append(f'             fill="#fff" stroke="{theme["node_stroke"]}" stroke-width="1.5"/>')
        tp = node["text_pos"]
        lines.append(f'    <text x="{tp["x"]:.0f}" y="{tp["y"]:.0f}" text-anchor="middle"')
        lines.append(f'          class="node-text" fill="{theme["text"]}" font-size="11">{node["text"]}</text>')

    elif ntype in ("pill", "phase-done"):
        nr = node["rect"]
        fill = "#dcfce7" if ntype == "pill" else "#f0fdf4"
        stroke = "#16a34a" if ntype == "pill" else "#22c55e"
        sw = "2" if ntype == "pill" else "1.5"
        text_fill = "#15803d" if ntype == "pill" else "#166534"
        lines.append(f'    <rect x="{nr["x"]:.0f}" y="{nr["y"]:.0f}" width="{nr["width"]:.0f}" height="{nr["height"]:.0f}" rx="{nr["rx"]}"')
        lines.append(f'          fill="{fill}" stroke="{stroke}" stroke-width="{sw}" filter="url(#shadow)"/>')
        tp = node["text_pos"]
        lines.append(f'    <text x="{tp["x"]:.0f}" y="{tp["y"]:.0f}" text-anchor="middle"')
        lines.append(f'          class="node-text" fill="{text_fill}" font-weight="700">{node["text"]}</text>')
        if "subtitle_pos" in node:
            sp = node["subtitle_pos"]
            lines.append(f'    <text x="{sp["x"]:.0f}" y="{sp["y"]:.0f}" text-anchor="middle"')
            lines.append(f'          class="node-sub" font-size="9">{node.get("subtitle", "")}</text>')

    else:  # action
        nr = node["rect"]
        text_class = "slash" if node.get("style") == "slash" else "node-text"
        lines.append(f'    <rect x="{nr["x"]:.0f}" y="{nr["y"]:.0f}" width="{nr["width"]:.0f}" height="{nr["height"]:.0f}" rx="{nr["rx"]}"')
        lines.append(f'          fill="#fff" stroke="{theme["node_stroke"]}" stroke-width="1.5" filter="url(#shadow)"/>')
        tp = node["text_pos"]
        lines.append(f'    <text x="{tp["x"]:.0f}" y="{tp["y"]:.0f}" text-anchor="middle"')
        lines.append(f'          class="{text_class}" fill="{theme["text"]}">{node["text"]}</text>')
        if "subtitle_pos" in node:
            sp = node["subtitle_pos"]
            lines.append(f'    <text x="{sp["x"]:.0f}" y="{sp["y"]:.0f}" text-anchor="middle"')
            lines.append(f'          class="node-sub">{node.get("subtitle", "")}</text>')

    return lines


def generate_svg(layout: dict) -> str:
    """Generate a skeleton SVG from calculated layout."""
    lines = []

    # Collect themes used
    themes_used = {g["theme_name"] for g in layout["groups"]}

    # Header
    vb = layout["viewBox"]
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"')
    lines.append("     font-family=\"Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif\">")
    lines.append("")

    lines.extend(_svg_defs(themes_used))
    lines.append("")
    lines.extend(_svg_styles())
    lines.append("")

    # Groups and nodes
    for g in layout["groups"]:
        theme = THEMES[g["theme_name"]]
        gr = g["rect"]
        gt = g["title"]

        lines.append(f'  <!-- ═══ {gt["text"]} {"═" * max(1, 60 - len(gt["text"]))} -->')
        lines.append("  <g>")
        lines.append(f'    <rect x="{gr["x"]:.0f}" y="{gr["y"]:.0f}" width="{gr["width"]:.0f}" height="{gr["height"]:.0f}" rx="{gr["rx"]}"')
        lines.append(f'          fill="url(#{theme["gradient"]})" stroke="{theme["stroke"]}" stroke-width="1.5" filter="url(#shadow)"/>')
        lines.append(f'    <text x="{gt["x"]:.0f}" y="{gt["y"]:.0f}" text-anchor="middle"')
        lines.append(f'          class="title" fill="{theme["title"]}">{gt["text"]}</text>')
        lines.append("")

        prev_node = None
        for node in g["nodes"]:
            # Arrow from previous node
            if prev_node:
                start_y = prev_node["bounds"]["bottom"]
                end_y = node["bounds"]["top"]
                cx = gt["x"]
                lines.append(f'    <line x1="{cx:.0f}" y1="{start_y:.0f}" x2="{cx:.0f}" y2="{end_y:.0f}"')
                lines.append('          stroke="#6b7280" stroke-width="1.5" marker-end="url(#arrow)"/>')

            lines.extend(_svg_node(node, theme))
            lines.append("")
            prev_node = node

        lines.append("  </g>")
        lines.append("")

    # TODO placeholders for manual work
    lines.append("  <!-- ═══ TODO: Cross-group connectors ═══════════════════════════")
    lines.append("       Add <path> or <line> segments connecting groups.")
    lines.append("       See references/svg-patterns.md sections 4c-4e. -->")
    lines.append("")
    lines.append("  <!-- ═══ TODO: Loop-back arrows ═════════════════════════════════")
    lines.append("       Route outside group boundaries with 20-30px margin.")
    lines.append("       See references/svg-patterns.md sections 4c-4d. -->")
    lines.append("")
    lines.append("  <!-- ═══ TODO: Annotation callouts ══════════════════════════════")
    lines.append("       Yellow boxes with dashed connectors.")
    lines.append("       See references/svg-patterns.md section 6. -->")
    lines.append("")
    lines.append("</svg>")

    return "\n".join(lines)


# ── Human-readable output ────────────────────────────────────────────

def print_coordinate_map(layout: dict) -> None:
    """Print a human-readable coordinate map for the LLM to reference."""
    cw = layout["canvas"]["width"]
    ch = layout["canvas"]["height"]
    print(f"Canvas: {cw} x {ch}")
    print(f"viewBox: {layout['viewBox']}")
    print()

    for g in layout["groups"]:
        gr = g["rect"]
        print(f"Group: {g['id']}  ({g['theme_name']})")
        print(f"  Rect:  x={gr['x']:.0f}  y={gr['y']:.0f}  w={gr['width']:.0f}  h={gr['height']:.0f}")
        print(f"  Title: x={g['title']['x']:.0f}  y={g['title']['y']:.0f}  \"{g['title']['text']}\"")
        print()

        for node in g["nodes"]:
            print(f"  Node: {node['id']}  ({node['type']})")
            if "rect" in node:
                nr = node["rect"]
                print(f"    Rect:   x={nr['x']:.0f}  y={nr['y']:.0f}  w={nr['width']:.0f}  h={nr['height']:.0f}  rx={nr['rx']}")
            if "center" in node:
                c = node["center"]
                print(f"    Center: ({c['x']:.0f}, {c['y']:.0f})")
                print(f"    Points: {node['points']}")
            tp = node["text_pos"]
            print(f"    Text:   ({tp['x']:.0f}, {tp['y']:.0f})  \"{node['text']}\"")
            if "subtitle_pos" in node:
                sp = node["subtitle_pos"]
                print(f"    Sub:    ({sp['x']:.0f}, {sp['y']:.0f})  \"{node.get('subtitle', '')}\"")
            b = node["bounds"]
            print(f"    Bounds: top={b['top']:.0f}  bottom={b['bottom']:.0f}  left={b['left']:.0f}  right={b['right']:.0f}")
            print()

    # Print connection hints
    print("Connection hints (add manually):")
    for i, g in enumerate(layout["groups"]):
        if i < len(layout["groups"]) - 1:
            g2 = layout["groups"][i + 1]
            right_edge = g["rect"]["x"] + g["rect"]["width"]
            left_edge = g2["rect"]["x"]
            print(f"  {g['id']} → {g2['id']}: right_edge={right_edge:.0f}  gap={left_edge - right_edge:.0f}px  left_edge={left_edge:.0f}")

    # Loopback hints
    print()
    print("Loopback routing margins:")
    for g in layout["groups"]:
        gx = g["rect"]["x"]
        gw = g["rect"]["width"]
        print(f"  {g['id']}: left_margin={gx - 20:.0f}  right_margin={gx + gw + 20:.0f}")


# ── Main ─────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calculate SVG layout coordinates from a JSON description.",
        epilog="See references/example-layout.json for input format.",
    )
    parser.add_argument("input", help="JSON file describing the diagram structure")
    parser.add_argument("--svg", metavar="FILE", help="Write skeleton SVG to FILE")
    parser.add_argument(
        "--format", choices=["map", "svg", "json"], default="map",
        help="Output format: map (human-readable), svg (stdout), json (machine-readable)",
    )
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            spec = json.load(f)
    except FileNotFoundError:
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        return 1

    layout = calculate_layout(spec)

    if args.svg:
        svg_content = generate_svg(layout)
        with open(args.svg, "w") as f:
            f.write(svg_content)
        print(f"SVG written to {args.svg}")
        print()
        print_coordinate_map(layout)
    elif args.format == "svg":
        print(generate_svg(layout))
    elif args.format == "json":
        print(json.dumps(layout, indent=2))
    else:
        print_coordinate_map(layout)

    return 0


if __name__ == "__main__":
    sys.exit(main())
