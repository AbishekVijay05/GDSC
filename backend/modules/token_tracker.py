"""
token_tracker.py — Centralized Token Usage Tracker
Tracks tokens used/remaining per API module across the platform.
"""
import time
from threading import Lock

_lock = Lock()

# Token budget definitions (from the Free plan)
TOKEN_BUDGETS = {
    "Chatbot (Llama 70B)":              {"max": 500,  "used": 0, "model": "meta/llama-3.1-70b-instruct", "module": "intent_translator"},
    "Drug Report (Llama 8B)":           {"max": 1500, "used": 0, "model": "meta/llama-3.1-8b-instruct",  "module": "synthesizer"},
    "Disease→Drug (Claude Haiku)":      {"max": 300,  "used": 0, "model": "anthropic/claude-3-haiku",    "module": "hypothesis"},
    "Hypothesis (Claude Haiku)":        {"max": 300,  "used": 0, "model": "anthropic/claude-3-haiku",    "module": "hypothesis_generator"},
    "Follow-up Q&A (Llama 70B)":        {"max": 400,  "used": 0, "model": "meta/llama-3.1-70b-instruct", "module": "followup"},
}

_last_reset = time.time()
RESET_INTERVAL = 5 * 3600  # 5 hours refresh cycle


def _maybe_reset():
    """Auto-reset token counters after the refresh interval."""
    global _last_reset
    now = time.time()
    if now - _last_reset >= RESET_INTERVAL:
        with _lock:
            for v in TOKEN_BUDGETS.values():
                v["used"] = 0
            _last_reset = now


def record_usage(module_name: str, tokens_used: int):
    """Record tokens consumed by a specific module."""
    _maybe_reset()
    with _lock:
        for entry in TOKEN_BUDGETS.values():
            if entry["module"] == module_name:
                entry["used"] += tokens_used
                break


def get_usage_summary() -> dict:
    """Return the current token usage state for all modules."""
    _maybe_reset()
    global _last_reset
    elapsed = time.time() - _last_reset
    remaining_secs = max(0, RESET_INTERVAL - elapsed)
    hours = int(remaining_secs // 3600)
    mins = int((remaining_secs % 3600) // 60)

    items = []
    with _lock:
        for label, entry in TOKEN_BUDGETS.items():
            remaining = max(0, entry["max"] - entry["used"])
            pct = remaining / entry["max"] if entry["max"] else 0
            items.append({
                "label":     label,
                "model":     entry["model"],
                "max":       entry["max"],
                "used":      entry["used"],
                "remaining": remaining,
                "pct":       round(pct, 3),
            })

    return {
        "items":   items,
        "refresh": f"Refreshes in {hours} hours, {mins} minutes",
    }
