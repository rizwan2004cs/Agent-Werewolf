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
    """First candidate name mentioned anywhere in the text."""
    for n in candidates:
        if re.search(rf"\b{re.escape(n)}\b", text, re.IGNORECASE):
            return n
    return None


def vote(text: str, candidates: list[str]) -> str | None:
    """Prefer the explicit `VOTE:<name>` line; else any name mentioned."""
    m = re.search(r"VOTE:\s*(\w+)", text, re.IGNORECASE)
    if m and any(m.group(1).lower() == c.lower() for c in candidates):
        return m.group(1)
    return name(text, candidates)
