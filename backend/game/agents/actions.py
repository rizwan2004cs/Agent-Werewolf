"""Public agent API: the four decisions an agent makes during a game.

This is the only agent module the engine imports. It chooses between the mock
and the real LLM path (via config), delegating transport to `llm` and output
parsing to `parse`. Returns are always concrete game objects, never raw text.

Resilience: every real LLM path is wrapped so a timeout/error falls back to the
mock behaviour. A stalled model call can therefore never freeze the narration —
the game keeps progressing with a stand-in line/pick.
"""
import random

from ..config import config
from . import llm, mock, parse, prompts


def night_wolf_pick(state):
    """Which non-wolf the wolves kill tonight."""
    targets = [p for p in state.alive_players() if p.role != "wolf"]
    if config.use_mock:
        return mock.wolf_pick(state)
    try:
        wolf = state.alive_wolves()[0]
        text = llm.chat(prompts.wolf_night(wolf, targets), max_tokens=60)
        picked = parse.name(text, [t.name for t in targets])
        return state.by_name(picked) or random.choice(targets)
    except Exception as e:
        print(f"[agents] night_wolf_pick LLM failed ({e}); mock fallback")
        return mock.wolf_pick(state)


def night_seer_pick(state):
    """(seer, investigated_target) or (None, None) if no living seer."""
    seer = next((p for p in state.alive_players() if p.role == "seer"), None)
    if not seer:
        return None, None
    targets = [p for p in state.alive_players() if p.idx != seer.idx]
    if config.use_mock:
        return seer, mock.seer_pick(seer, targets)
    try:
        text = llm.chat(prompts.seer_night(seer, targets), max_tokens=60)
        picked = parse.name(text, [t.name for t in targets])
        return seer, (state.by_name(picked) or random.choice(targets))
    except Exception as e:
        print(f"[agents] night_seer_pick LLM failed ({e}); mock fallback")
        return seer, mock.seer_pick(seer, targets)


def speak(player, state, seer_knowledge=None):
    """One call -> (public speech, private thought)."""
    if config.use_mock:
        return mock.speak(player, state, seer_knowledge)
    try:
        raw = llm.chat(
            prompts.day_speak(player, state, seer_knowledge),
            max_tokens=320,
            json_mode=True,
        )
        return parse.speak(raw)
    except Exception as e:
        print(f"[agents] speak LLM failed ({e}); mock fallback")
        return mock.speak(player, state, seer_knowledge)


def defend(player, state, seer_knowledge=None):
    """The accused pleads their case before the vote -> (speech, thought)."""
    if config.use_mock:
        return mock.defend(player, state)
    try:
        raw = llm.chat(
            prompts.defend(player, state, seer_knowledge),
            max_tokens=320,
            json_mode=True,
        )
        return parse.speak(raw)
    except Exception as e:
        print(f"[agents] defend LLM failed ({e}); mock fallback")
        return mock.defend(player, state)


def last_words(player, state):
    """A just-eliminated player's final line -> (speech, thought)."""
    if config.use_mock:
        return mock.last_words(player, state)
    try:
        raw = llm.chat(prompts.last_words(player, state), max_tokens=200, json_mode=True)
        return parse.speak(raw)
    except Exception as e:
        print(f"[agents] last_words LLM failed ({e}); mock fallback")
        return mock.last_words(player, state)


def vote(player, state, seer_knowledge=None):
    """(target_player, raw_reasoning_text)."""
    candidates = [p.name for p in state.alive_players() if p.idx != player.idx]
    if config.use_mock:
        return state.by_name(mock.vote(player, state, candidates)), "(mock vote)"
    try:
        text = llm.chat(prompts.vote(player, state, seer_knowledge), max_tokens=120)
        picked = parse.vote(text, candidates)
        target = state.by_name(picked)
        if not target or target.idx == player.idx:
            target = state.by_name(random.choice(candidates))
        return target, text
    except Exception as e:
        print(f"[agents] vote LLM failed ({e}); mock fallback")
        return state.by_name(mock.vote(player, state, candidates)), "(mock vote)"
