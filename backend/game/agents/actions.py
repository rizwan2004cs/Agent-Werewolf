"""Public agent API: the four decisions an agent makes during a game.

This is the only agent module the engine imports. It chooses between the mock
and the real LLM path (via config), delegating transport to `llm` and output
parsing to `parse`. Returns are always concrete game objects, never raw text.
"""
import random

from ..config import config
from . import llm, mock, parse, prompts


def night_wolf_pick(state):
    """Which non-wolf the wolves kill tonight."""
    targets = [p for p in state.alive_players() if p.role != "wolf"]
    if config.use_mock:
        return mock.wolf_pick(state)
    wolf = state.alive_wolves()[0]
    text = llm.chat(prompts.wolf_night(wolf, targets), max_tokens=60)
    picked = parse.name(text, [t.name for t in targets])
    return state.by_name(picked) or random.choice(targets)


def night_seer_pick(state):
    """(seer, investigated_target) or (None, None) if no living seer."""
    seer = next((p for p in state.alive_players() if p.role == "seer"), None)
    if not seer:
        return None, None
    targets = [p for p in state.alive_players() if p.idx != seer.idx]
    if config.use_mock:
        return seer, mock.seer_pick(seer, targets)
    text = llm.chat(prompts.seer_night(seer, targets), max_tokens=60)
    picked = parse.name(text, [t.name for t in targets])
    return seer, (state.by_name(picked) or random.choice(targets))


def speak(player, state, seer_knowledge=None):
    """One call → (public speech, private thought)."""
    if config.use_mock:
        return mock.speak(player, state, seer_knowledge)
    raw = llm.chat(prompts.day_speak(player, state, seer_knowledge), json_mode=True)
    return parse.speak(raw)


def vote(player, state, seer_knowledge=None):
    """(target_player, raw_reasoning_text)."""
    candidates = [p.name for p in state.alive_players() if p.idx != player.idx]
    if config.use_mock:
        return state.by_name(mock.vote(player, state, candidates)), "(mock vote)"
    text = llm.chat(prompts.vote(player, state, seer_knowledge), max_tokens=120)
    picked = parse.vote(text, candidates)
    target = state.by_name(picked)
    if not target or target.idx == player.idx:
        target = state.by_name(random.choice(candidates))
    return target, text
