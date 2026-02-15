#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Claude Code Status Line
Displays: Model | Context ProgressBar % | 5h Usage % | 7d Usage % | Tasks | Agents | Plan(s) | Git Branch

Uses the OAuth usage endpoint (same as claude-dashboard) to get real
subscription plan utilization — not API token counting.

Task/Agent info shows:
- Tasks: Open/completed task counts
- Sub-agents: Active sub-agent count (Team members + Background tasks)
- Plans: Active implementation plans from per-plan sidecar files (multi-agent safe)
"""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# ── ANSI Colors (256-color pastel palette matching claude-dashboard) ──────────
RESET = "\x1b[0m"
DIM = "\x1b[2m"
PASTEL_CYAN = "\x1b[38;5;117m"
PASTEL_PINK = "\x1b[38;5;218m"
PASTEL_GREEN = "\x1b[38;5;151m"
PASTEL_YELLOW = "\x1b[38;5;222m"
PASTEL_RED = "\x1b[38;5;210m"
PASTEL_GRAY = "\x1b[38;5;249m"
PASTEL_LAVENDER = "\x1b[38;5;183m"

# ── Cache ─────────────────────────────────────────────────────────────────────
CACHE_DIR = Path.home() / ".cache" / "claude-statusline"
CACHE_FILE = CACHE_DIR / "usage-cache.json"
CACHE_TTL_SECONDS = 60
API_TIMEOUT_SECONDS = 5
PLAN_CACHE_DIR = CACHE_DIR / "plans"  # one file per plan for multi-agent isolation
PLAN_STALE_SECONDS = 7200  # 2h — ignore sidecar from crashed sessions

# ── Progress bar chars ────────────────────────────────────────────────────────
FILLED = "\u2588"  # █
EMPTY = "\u2591"   # ░
BAR_WIDTH = 10


def color_for_percent(pct: float) -> str:
    """Get color based on percentage threshold."""
    if pct <= 50:
        return PASTEL_GREEN
    if pct <= 80:
        return PASTEL_YELLOW
    return PASTEL_RED


def colorize(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def render_progress_bar(pct: float) -> str:
    """Render a colored progress bar."""
    clamped = max(0, min(100, pct))
    filled = round(clamped / 100 * BAR_WIDTH)
    empty = BAR_WIDTH - filled
    bar = FILLED * filled + EMPTY * empty
    return colorize(bar, color_for_percent(clamped))


def format_time_remaining(resets_at: str | None) -> str:
    """Format time remaining until reset."""
    if not resets_at:
        return ""
    try:
        # Parse ISO format reset time
        reset_str = resets_at.replace("Z", "+00:00")
        from datetime import datetime, timezone
        reset_time = datetime.fromisoformat(reset_str)
        now = datetime.now(timezone.utc)
        diff_seconds = (reset_time - now).total_seconds()
        if diff_seconds <= 0:
            return ""
        total_minutes = int(diff_seconds // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        days = hours // 24
        hours = hours % 24
        if days > 0:
            return f" ({days}d{hours}h)"
        if hours > 0:
            return f" ({hours}h{minutes}m)"
        return f" ({minutes}m)"
    except Exception:
        return ""


# ── OAuth Credentials ─────────────────────────────────────────────────────────

def get_oauth_token() -> str | None:
    """Read OAuth access token from ~/.claude/.credentials.json."""
    try:
        cred_path = Path.home() / ".claude" / ".credentials.json"
        content = cred_path.read_text()
        creds = json.loads(content)
        return creds.get("claudeAiOauth", {}).get("accessToken")
    except Exception:
        return None


# ── Usage API ─────────────────────────────────────────────────────────────────

def fetch_usage_from_api(token: str) -> dict | None:
    """Fetch subscription usage from Anthropic OAuth usage endpoint."""
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20",
            },
        )
        with urllib.request.urlopen(req, timeout=API_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def load_cache() -> dict | None:
    """Load cached usage data if still fresh."""
    try:
        if not CACHE_FILE.exists():
            return None
        content = json.loads(CACHE_FILE.read_text())
        age = time.time() - content.get("timestamp", 0)
        if age < CACHE_TTL_SECONDS:
            return content.get("data")
        return None
    except Exception:
        return None


def save_cache(data: dict) -> None:
    """Save usage data to cache file."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"data": data, "timestamp": time.time()}))
    except Exception:
        pass


def get_usage_data() -> dict | None:
    """Get usage data with caching."""
    # Try cache first
    cached = load_cache()
    if cached is not None:
        return cached

    # Fetch from API
    token = get_oauth_token()
    if not token:
        return None

    data = fetch_usage_from_api(token)
    if data:
        save_cache(data)
    return data


# ── Widgets ───────────────────────────────────────────────────────────────────

def get_model_display(stdin_data: dict) -> str:
    """Extract short model name from stdin."""
    display_name = stdin_data.get("model", {}).get("display_name", "")
    model_id = stdin_data.get("model", {}).get("id", "")
    name = display_name or model_id

    lower = name.lower()
    if "opus" in lower:
        return "Opus"
    if "sonnet" in lower:
        return "Sonnet"
    if "haiku" in lower:
        return "Haiku"
    return name or "Claude"


def get_context_info(stdin_data: dict) -> tuple[float, str]:
    """Get context percentage and token summary."""
    ctx = stdin_data.get("context_window", {})
    usage = ctx.get("current_usage")
    context_size = ctx.get("context_window_size", 200_000)

    if not usage:
        return 0.0, "0K"

    input_tokens = (
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )

    pct = min(100, round(input_tokens / context_size * 100)) if context_size > 0 else 0

    # Format token count
    if input_tokens >= 1_000_000:
        token_str = f"{input_tokens / 1_000_000:.1f}M"
    elif input_tokens >= 1_000:
        token_str = f"{input_tokens / 1_000:.0f}K"
    else:
        token_str = str(input_tokens)

    return pct, token_str


def get_git_branch(cwd: str) -> str:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd or ".",
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return ""
    except Exception:
        return ""


def render_rate_limit(label: str, limit_data: dict | None) -> str:
    """Render a rate limit widget segment."""
    if not limit_data:
        return f"{label}: {colorize('--', PASTEL_GRAY)}"

    utilization = round(limit_data.get("utilization", 0))
    resets_at = limit_data.get("resets_at")
    color = color_for_percent(utilization)
    time_str = format_time_remaining(resets_at)

    return f"{label}: {colorize(f'{utilization}%', color)}{time_str}"


def get_task_info(stdin_data: dict) -> str | None:
    """Get task status summary."""
    tasks = stdin_data.get("tasks", {})
    open_count = tasks.get("open", 0)
    completed_count = tasks.get("completed", 0)

    if open_count == 0 and completed_count == 0:
        return None

    # Color based on completion ratio
    total = open_count + completed_count
    completion_pct = (completed_count / total * 100) if total > 0 else 0

    # Show both counts with color
    if open_count > 0:
        color = PASTEL_YELLOW if completion_pct < 50 else PASTEL_GREEN
    else:
        color = PASTEL_GREEN  # All done

    return f"Tasks: {colorize(f'{open_count}', PASTEL_YELLOW)}/{colorize(f'{completed_count}', PASTEL_GREEN)}"


def get_agent_info(stdin_data: dict) -> str | None:
    """Get active sub-agent summary (team members + background tasks)."""
    teammates = stdin_data.get("teammates", [])
    background_tasks = stdin_data.get("background_tasks", [])

    teammate_count = len(teammates) if teammates else 0
    bg_task_count = len(background_tasks) if background_tasks else 0
    total_agents = teammate_count + bg_task_count

    if total_agents == 0:
        return None

    parts = []
    if teammate_count > 0:
        parts.append(f"{colorize(str(teammate_count), PASTEL_CYAN)} team")
    if bg_task_count > 0:
        parts.append(f"{colorize(str(bg_task_count), PASTEL_PINK)} bg")

    return f"Agents: {' + '.join(parts)}"


def get_plan_info() -> str | None:
    """Get active plan/phase from per-plan sidecar files written by /implement.

    Each /implement session writes its own file to plans/{plan-name}.json,
    so multiple agents on different plans don't overwrite each other.
    """
    try:
        if not PLAN_CACHE_DIR.exists():
            return None

        now = time.time()
        active_plans: list[tuple[float, str]] = []  # (updated, label)

        for sidecar in PLAN_CACHE_DIR.glob("*.json"):
            try:
                data = json.loads(sidecar.read_text())
                age = now - data.get("updated", 0)
                if age > PLAN_STALE_SECONDS:
                    continue
                plan = data.get("plan", "")
                phase = data.get("phase")
                if not plan:
                    continue
                label = f"{plan} P{phase}" if phase else plan
                active_plans.append((data.get("updated", 0), label))
            except Exception:
                continue

        if not active_plans:
            return None

        # Sort by most recently updated, show all active plans
        active_plans.sort(key=lambda x: x[0], reverse=True)
        labels = [label for _, label in active_plans]
        return colorize(" | ".join(labels), PASTEL_LAVENDER)
    except Exception:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    try:
        stdin_data = json.load(sys.stdin)
    except Exception:
        print(colorize("?", PASTEL_YELLOW))
        return

    sep = f" {DIM}|{RESET} "
    parts: list[str] = []

    # 1. Model
    model = get_model_display(stdin_data)
    parts.append(colorize(f"{model}", PASTEL_CYAN))

    # 2. Context: progress bar + percentage + tokens
    ctx_pct, ctx_tokens = get_context_info(stdin_data)
    bar = render_progress_bar(ctx_pct)
    pct_color = color_for_percent(ctx_pct)
    parts.append(f"{bar} {colorize(f'{ctx_pct}%', pct_color)}")

    # 3. Rate limits from OAuth usage API
    usage = get_usage_data()

    five_hour = usage.get("five_hour") if usage else None
    seven_day = usage.get("seven_day") if usage else None

    parts.append(render_rate_limit("5h", five_hour))
    parts.append(render_rate_limit("7d", seven_day))

    # 4. Task status
    task_info = get_task_info(stdin_data)
    if task_info:
        parts.append(task_info)

    # 5. Agent status (teammates + background tasks)
    agent_info = get_agent_info(stdin_data)
    if agent_info:
        parts.append(agent_info)

    # 6. Active plan/phase (from /implement sidecar file)
    plan_info = get_plan_info()
    if plan_info:
        parts.append(plan_info)

    # 7. Git branch
    cwd = stdin_data.get("workspace", {}).get("current_dir", "")
    branch = get_git_branch(cwd)
    if branch:
        parts.append(colorize(branch, PASTEL_PINK))

    print(sep.join(parts))


if __name__ == "__main__":
    main()
