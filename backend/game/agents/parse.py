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


def _match(token: str, candidates: list[str]) -> str | None:
    """Resolve a token to a candidate: full name first, then unique first name."""
    token = token.strip().lower()
    if not token:
        return None
    for c in candidates:
        if token == c.lower():
            return c
    first = token.split()[0]
    firsts = [c for c in candidates if c.split()[0].lower() == first]
    return firsts[0] if len(firsts) == 1 else None


def name(text: str, candidates: list[str]) -> str | None:
    """First candidate name mentioned anywhere in the text (full name, or
    unambiguous first name)."""
    for n in candidates:
        if re.search(rf"\b{re.escape(n)}\b", text, re.IGNORECASE):
            return n
    for n in candidates:
        first = n.split()[0]
        if first != n and re.search(rf"\b{re.escape(first)}\b", text, re.IGNORECASE):
            same = [c for c in candidates if c != n and c.split()[0].lower() == first.lower()]
            if not same:
                return n
    return None


def vote(text: str, candidates: list[str]) -> str | None:
    """Prefer the explicit `VOTE:<name>` line; else any name mentioned.
    Handles multi-word names ("VOTE: Ronan Voss") and bare first names."""
    m = re.search(r"VOTE:\s*([A-Za-z][A-Za-z' -]*)", text, re.IGNORECASE)
    if m:
        resolved = _match(m.group(1), candidates)
        if resolved:
            return resolved
    return name(text, candidates)
