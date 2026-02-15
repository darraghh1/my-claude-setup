"""
Constants for Claude Code Hooks.
"""

from pathlib import Path

# Derive project root from this file's location:
# constants.py -> utils/ -> hooks/ -> .claude/ -> PROJECT_ROOT
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Absolute log directory — never depends on CWD
LOG_DIR = _PROJECT_ROOT / ".claude" / "data" / "logs"


def get_session_log_dir(session_id: str) -> Path:
    """Get the log directory for a specific session."""
    return LOG_DIR / session_id


def ensure_session_log_dir(session_id: str) -> Path:
    """Ensure the log directory for a session exists and return it."""
    log_dir = get_session_log_dir(session_id)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
