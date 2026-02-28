"""
Constants for Claude Code Hooks.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# Derive project root from this file's location:
# constants.py -> utils/ -> hooks/ -> .claude/ -> PROJECT_ROOT
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Absolute log directory — never depends on CWD
LOG_DIR = _PROJECT_ROOT / ".claude" / "data" / "logs"

# JSONL log directory — single append-only file, grep-able across sessions
JSONL_LOG_DIR = _PROJECT_ROOT / ".claude" / "hooks" / "logs"


def get_session_log_dir(session_id: str) -> Path:
    """Get the log directory for a specific session."""
    return LOG_DIR / session_id


def ensure_session_log_dir(session_id: str) -> Path:
    """Ensure the log directory for a session exists and return it."""
    log_dir = get_session_log_dir(session_id)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def log_jsonl(event: str, session_id: str, data: dict) -> None:
    """Append a single JSON line to the JSONL log file.

    Each line is a complete JSON object with timestamp, event type,
    session ID, and payload. Append-only, O(1) per write.

    Args:
        event: Hook event name (e.g., "PreToolUse", "PostToolUse", "Stop")
        session_id: Current session identifier
        data: Event-specific payload (tool name, warnings, etc.)
    """
    JSONL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = JSONL_LOG_DIR / "hooks.jsonl"

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "session": session_id,
        **data,
    }

    try:
        with open(log_path, "a") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except OSError:
        pass  # Never fail the hook due to logging
