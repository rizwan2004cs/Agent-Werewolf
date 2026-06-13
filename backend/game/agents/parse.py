"""Parse raw model output into game-usable values. No model calls, no state."""
import json
import re


def speak(raw: str) -> tuple[str, str]:
    """Parse the speak JSON into (speech, thought) with graceful fallback."""
    try:
        data = json.loads(raw)
        speech = str(data.get("speech", "")).strip()
        thought = str(data.get("thought", "")).strip()
        if speech:
            return speech, (thought or "(no comment)")
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    return (raw or "...").strip(), "(could not parse private thought)"


def name(text: str, candidates: list[str]) -> str | None:
    """The candidate name appearing EARLIEST in the text (best reflects intent
    when several names are mentioned). Returns None if none are found."""
    best, best_pos = None, len(text) + 1
    for c in candidates:
        m = re.search(rf"\b{re.escape(c)}\b", text, re.IGNORECASE)
        if m and m.start() < best_pos:
            best, best_pos = c, m.start()
    return best


def vote(text: str, candidates: list[str]) -> str | None:
    """Prefer the explicit `VOTE:<name>` line (multi-word names supported);
    else fall back to the earliest candidate mentioned anywhere."""
    m = re.search(r"VOTE:\s*(.+)", text, re.IGNORECASE)
    if m:
        tail = m.group(1).strip()
        # Match against the full candidate names; prefer the longest match so
        # "Victor Kane" wins over a stray "Victor" substring.
        for c in sorted(candidates, key=len, reverse=True):
            if re.search(rf"\b{re.escape(c)}\b", tail, re.IGNORECASE):
                return c
    return name(text, candidates)
