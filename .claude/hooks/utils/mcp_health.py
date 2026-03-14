"""
MCP server health check — verifies runtime prerequisites are available.

Called from session_start.py. Returns warnings as a list of strings
to be injected into additionalContext. Empty list = all healthy.

MCP servers are stdio-based child processes managed by Claude Code,
so we can't ping them directly. Instead we verify:
  1. The configured npx binary exists and is executable
  2. Node.js is available (required for all npx-based MCP servers)

This catches the most common failure mode: Node.js not installed
or nvm not loaded in the shell environment.
"""

import json
import shutil
from pathlib import Path

# User-level Claude config where MCP servers are defined
CLAUDE_CONFIG = Path.home() / ".claude.json"


def _get_configured_servers() -> dict:
    """Read MCP server configs from config files.

    Checks ~/.claude.json and ~/.claude/settings.json for mcpServers
    at the top level and under per-project entries.

    Returns a dict of {server_name: {command, args, ...}} or empty dict.
    """
    servers: dict = {}

    for config_path in [CLAUDE_CONFIG, CLAUDE_CONFIG.parent / "settings.json"]:
        if not config_path.exists():
            continue

        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # Top-level mcpServers
        servers.update(config.get("mcpServers", {}))

        # Per-project mcpServers
        for _path, project_config in config.get("projects", {}).items():
            if isinstance(project_config, dict):
                servers.update(project_config.get("mcpServers", {}))

    return servers


def check_mcp_health() -> list[str]:
    """Check MCP server prerequisites and return warnings.

    Returns a list of warning strings. Empty list = healthy.
    """
    warnings: list[str] = []

    servers = _get_configured_servers()
    if not servers:
        return warnings

    # Collect all unique command binaries used by MCP servers
    commands = set()
    for _name, config in servers.items():
        cmd = config.get("command", "")
        if cmd:
            commands.add(cmd)

    # Check each binary exists
    for cmd in commands:
        cmd_path = Path(cmd)

        if cmd_path.is_absolute():
            # Absolute path (e.g., /home/user/.nvm/.../npx)
            if not cmd_path.exists():
                warnings.append(
                    f"Warning: MCP binary not found: {cmd} — "
                    "MCP servers may fail to start. "
                    "Check your Node.js/nvm installation."
                )
        else:
            # Relative command (e.g., "npx") — check PATH
            if not shutil.which(cmd):
                warnings.append(
                    f"Warning: MCP command '{cmd}' not found on PATH — "
                    "MCP servers may fail to start."
                )

    # Check Node.js availability (all current MCP servers use npx)
    has_npx_server = any(
        "npx" in config.get("command", "")
        for config in servers.values()
    )
    if has_npx_server and not shutil.which("node"):
        warnings.append(
            "Warning: 'node' not found on PATH — "
            "npx-based MCP servers require Node.js. "
            "Ensure nvm is loaded or Node.js is installed."
        )

    return warnings
