"""MCP orphan cleanup — discovers patterns from config, kills only true orphans.

Problem: MCP servers spawned via npx create a deep process chain
(claude → npm → sh → node). When Claude crashes, SessionEnd never fires,
stdin doesn't close cleanly through the npx wrapper chain, and leaf node
processes survive — reparented to init. On restart, Claude spawns NEW
MCP servers on top of the orphans. After a few crash cycles, 100+ orphaned
processes consume gigabytes of RAM.

Solution: Instead of hardcoding server names, read mcpServers from all
config sources (claude.json, settings.json, settings.local.json, .mcp.json).
Then use process-tree ancestry to distinguish orphans from live servers:
  - Orphan: MCP process with NO running Claude ancestor → safe to kill
  - Live: MCP process whose ancestor chain includes a Claude PID → leave it

Config sources checked (in order):
  ~/.claude.json              — user-level Claude config
  ~/.claude/settings.json     — user-level settings
  <project>/.claude/settings.json       — project-level settings
  <project>/.claude/settings.local.json — project-level local settings
  <project>/.mcp.json                   — project-level MCP config
"""

import json
import os
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Config discovery
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    """Read a JSON file, returning empty dict on any failure."""
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _collect_mcp_servers() -> dict[str, dict]:
    """Merge mcpServers from all known config locations."""
    home = Path.home()
    project_dir = Path(
        os.environ.get("CLAUDE_PROJECT_DIR", str(Path.cwd()))
    )

    sources = [
        home / ".claude.json",
        home / ".claude" / "settings.json",
        project_dir / ".claude" / "settings.json",
        project_dir / ".claude" / "settings.local.json",
        project_dir / ".mcp.json",
    ]

    servers: dict[str, dict] = {}
    for src in sources:
        cfg = _read_json(src)
        # Top-level mcpServers
        servers.update(cfg.get("mcpServers", {}))
        # Per-project mcpServers (in ~/.claude.json)
        for proj in cfg.get("projects", {}).values():
            if isinstance(proj, dict):
                servers.update(proj.get("mcpServers", {}))

    return servers


def _extract_patterns(server_cfg: dict) -> list[str]:
    """Extract process-identifiable patterns from one MCP server config.

    For npx-based servers, extracts patterns from the package reference:
      @scope/name@version → ["scope/name", "name"] (if name is specific)
      name@version        → ["name"]

    For direct binary commands, uses the binary filename.

    Generic names like "mcp", "mcp-server", "server" are only used in
    their scoped form to avoid matching unrelated MCP servers (e.g.,
    a project's own @alfred/mcp-server).
    """
    args = server_cfg.get("args", [])
    command = server_cfg.get("command", "")

    # Direct binary (not npx/npm) — use the filename
    if command and command not in ("npx", "npm"):
        name = Path(command).name
        return [name] if name else []

    # Names too generic to use as standalone patterns — only match
    # when qualified with their scope (e.g., "next-ai-drawio/mcp-server")
    generic_names = {"mcp", "mcp-server", "server", "client"}

    patterns: list[str] = []
    for arg in args:
        if arg.startswith("-"):
            continue

        # Found the package reference
        if arg.startswith("@"):
            # Scoped: @scope/name@version
            slash = arg.find("/")
            if slash < 0:
                break
            scope = arg[1:slash]
            rest = arg[slash + 1:]
            at = rest.find("@")
            name = rest[:at] if at > 0 else rest
            # Full scoped pattern — matches `npm exec @scope/name`
            patterns.append(f"{scope}/{name}")
            # Short name — matches `node .../name` binary
            # Skip generic names that would false-positive on unrelated servers
            if name not in generic_names and len(name) > 3:
                patterns.append(name)
        else:
            # Unscoped: name@version
            at = arg.find("@")
            name = arg[:at] if at > 0 else arg
            if name:
                patterns.append(name)
        break  # Only process first non-flag arg

    return patterns


def discover_mcp_patterns() -> list[str]:
    """Get all unique MCP process patterns from config files.

    Returns patterns like: ["playwright/mcp", "tavily-mcp", "context7-mcp"]
    """
    servers = _collect_mcp_servers()
    seen: set[str] = set()
    for cfg in servers.values():
        seen.update(_extract_patterns(cfg))
    return list(seen)


# ---------------------------------------------------------------------------
# Process tree helpers
# ---------------------------------------------------------------------------

def _get_process_table() -> list[tuple[int, int, str]]:
    """Return (pid, ppid, cmdline) for all processes."""
    try:
        r = subprocess.run(
            ["ps", "-eo", "pid,ppid,args"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, OSError):
        return []

    rows: list[tuple[int, int, str]] = []
    for line in r.stdout.strip().split("\n")[1:]:  # skip header
        parts = line.strip().split(None, 2)
        if len(parts) >= 2:
            try:
                rows.append((
                    int(parts[0]),
                    int(parts[1]),
                    parts[2] if len(parts) > 2 else "",
                ))
            except ValueError:
                pass
    return rows


def _is_claude_cmd(cmd: str) -> bool:
    """Check if a command line belongs to a Claude CLI process."""
    if not cmd:
        return False
    first_word = cmd.split()[0]
    basename = os.path.basename(first_word)
    return basename == "claude"


def _has_claude_ancestor(
    pid: int,
    ppid_map: dict[int, int],
    cmd_map: dict[int, str],
) -> bool:
    """Walk ancestor chain looking for a running Claude process.

    Returns True if any ancestor is a `claude` process — meaning
    this process belongs to a live session and should NOT be killed.
    """
    current = pid
    visited: set[int] = set()
    while current > 1:
        if current in visited:
            break
        visited.add(current)
        parent = ppid_map.get(current, 0)
        if parent <= 0:
            break
        if _is_claude_cmd(cmd_map.get(parent, "")):
            return True
        current = parent
    return False


def _find_claude_ancestor(
    pid: int,
    ppid_map: dict[int, int],
    cmd_map: dict[int, str],
) -> int | None:
    """Find the Claude PID in the ancestor chain of a process."""
    current = pid
    visited: set[int] = set()
    while current > 1:
        if current in visited:
            break
        visited.add(current)
        parent = ppid_map.get(current, 0)
        if parent <= 0:
            break
        if _is_claude_cmd(cmd_map.get(parent, "")):
            return parent
        current = parent
    return None


def _get_descendants(
    pid: int,
    ppid_map: dict[int, int],
) -> list[int]:
    """Get all descendant PIDs of a process (breadth-first)."""
    # Build parent → children index
    children: dict[int, list[int]] = {}
    for p, pp in ppid_map.items():
        children.setdefault(pp, []).append(p)

    result: list[int] = []
    queue = list(children.get(pid, []))
    while queue:
        child = queue.pop()
        result.append(child)
        queue.extend(children.get(child, []))
    return result


def _matches_mcp_pattern(cmd: str, patterns: list[str]) -> bool:
    """Check if a process command line matches any MCP pattern."""
    return any(pat in cmd for pat in patterns)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def kill_orphaned_mcp() -> list[tuple[str, int]]:
    """Kill MCP processes with no running Claude ancestor.

    Safe for concurrent sessions — only kills true orphans whose
    entire ancestor chain contains no living Claude process.

    Called from session_start.py to clean up after previous crashes.

    Returns [(description, count)] for logging.
    """
    patterns = discover_mcp_patterns()
    if not patterns:
        return []

    procs = _get_process_table()
    ppid_map = {p: pp for p, pp, _ in procs}
    cmd_map = {p: c for p, _, c in procs}

    killed = 0
    for pid, _ppid, cmd in procs:
        if not _matches_mcp_pattern(cmd, patterns):
            continue
        if _has_claude_ancestor(pid, ppid_map, cmd_map):
            continue
        try:
            os.kill(pid, 15)  # SIGTERM for graceful shutdown
            killed += 1
        except (ProcessLookupError, PermissionError, OSError):
            pass

    return [("orphaned_mcp_servers", killed)] if killed > 0 else []


def kill_session_mcp() -> list[tuple[str, int]]:
    """Kill MCP processes owned by the current Claude session only.

    Finds the Claude PID by walking up from the current process,
    then kills only MCP descendants of THAT Claude process.
    Other sessions' MCP servers are untouched.

    Called from session_end.py for targeted cleanup on graceful exit.

    Returns [(description, count)] for logging.
    """
    patterns = discover_mcp_patterns()
    if not patterns:
        return []

    procs = _get_process_table()
    ppid_map = {p: pp for p, pp, _ in procs}
    cmd_map = {p: c for p, _, c in procs}

    # Find our Claude ancestor
    claude_pid = _find_claude_ancestor(os.getpid(), ppid_map, cmd_map)
    if not claude_pid:
        return []

    # Kill only MCP descendants of OUR Claude process
    descendants = _get_descendants(claude_pid, ppid_map)
    killed = 0
    for pid in descendants:
        cmd = cmd_map.get(pid, "")
        if _matches_mcp_pattern(cmd, patterns):
            try:
                os.kill(pid, 15)  # SIGTERM
                killed += 1
            except (ProcessLookupError, PermissionError, OSError):
                pass

    return [("session_mcp_servers", killed)] if killed > 0 else []
