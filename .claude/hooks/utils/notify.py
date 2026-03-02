"""
Clippy Awakens notification utility for Claude Code hooks.

Sends HTTP requests to the Clippy Awakens app running on Windows,
reached via SSH reverse tunnel (-R 9999:localhost:9999).

Usage from any hook:
    from utils.notify import notify, message
    notify("complete")                    # task finished
    notify("stop")                        # Claude stopped
    notify("error")                       # something failed
    notify("attention")                   # needs user input
    notify("session-end")                 # session ending
    message("Found the bug!")             # custom speech bubble

Fails silently if Clippy isn't reachable (no tunnel, app not running).
Never blocks the hook — fires and forgets.
"""

import subprocess
import urllib.parse

SOUND_SERVER_URL = "http://localhost:9999"

# Valid event names (must match Clippy Awakens server routes)
VALID_EVENTS = frozenset({
    "complete",
    "error",
    "attention",
    "stop",
    "session-end",
})


def notify(event: str) -> None:
    """
    Send a notification event to Clippy.

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


def message(text: str) -> None:
    """
    Send a custom message through Clippy's speech bubble.

    Clippy pops up, plays a random animation, and speaks the text.
    """
    if not text:
        return

    encoded = urllib.parse.quote(text)
    try:
        subprocess.Popen(
            [
                "curl", "-s", "-m", "2",
                f"{SOUND_SERVER_URL}/message?text={encoded}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError):
        pass
