"""
Sound notification utility for Claude Code hooks.

Sends HTTP requests to a PowerShell sound server running on the
user's local Windows machine, reached via SSH reverse tunnel
(-R 9999:localhost:9999).

Usage from any hook:
    from utils.notify import notify
    notify("complete")   # task finished
    notify("stop")       # Claude stopped
    notify("error")      # something failed
    notify("attention")  # needs user input
    notify("session-end")  # session ending

Fails silently if the sound server isn't reachable (no tunnel,
server not running, etc.). Never blocks the hook — fires and forgets.
"""

import subprocess

SOUND_SERVER_URL = "http://localhost:9999"

# Valid event names (must match PowerShell server mappings)
VALID_EVENTS = frozenset({
    "complete",
    "error",
    "attention",
    "stop",
    "session-end",
})


def notify(event: str) -> None:
    """
    Send a sound notification for the given event.

    Fires curl in the background with a short timeout.
    Never raises — hooks must not fail due to notifications.
    """
    if event not in VALID_EVENTS:
        return

    try:
        subprocess.Popen(
            [
                "curl", "-s", "-m", "2",
                f"{SOUND_SERVER_URL}/{event}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError):
        # curl not available or other OS error — silent
        pass
