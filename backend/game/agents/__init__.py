"""Agent subsystem — deciding what an agent does.

Public surface is the four action functions; transport/parsing/mock/prompts are
internal details.
"""
from .actions import (
    defend,
    last_words,
    night_seer_pick,
    night_wolf_pick,
    speak,
    vote,
)

__all__ = [
    "night_wolf_pick",
    "night_seer_pick",
    "speak",
    "vote",
    "defend",
    "last_words",
]
