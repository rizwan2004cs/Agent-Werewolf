"""Human-input handoff for "play yourself" games.

The game loop runs in a background thread. When it reaches the human player's
turn to speak or vote, it sets state.awaiting and BLOCKS here on an Event until
the frontend POSTs the input (/control/say or /control/vote), which calls
submit(). A timeout guarantees the game never hangs if the human goes away.

Single game at a time, so a single Event suffices.
"""
import threading

_event = threading.Event()
_value = None
_lock = threading.Lock()


def begin() -> None:
    """Reset before the loop waits for the next human input."""
    global _value
    with _lock:
        _value = None
        _event.clear()


def submit(value) -> None:
    """Called by the HTTP endpoint when the human submits."""
    global _value
    with _lock:
        _value = value
    _event.set()


def wait(timeout: float):
    """Block until submit() or timeout. Returns the value, or None on timeout."""
    got = _event.wait(timeout)
    with _lock:
        return _value if got else None
