"""LLM agent wrappers. Falls back to deterministic mock output when no
ANTHROPIC_API_KEY is set (or MOCK_AGENTS=1), so the full game runs offline."""
from __future__ import annotations

import os
import re
import random

from . import prompts

# Provider auto-detect: OpenAI if its key is present, else Anthropic, else mock.
# Force mock with MOCK_AGENTS=1. Override the model with AGENT_MODEL.
_FORCE_MOCK = os.environ.get("MOCK_AGENTS") == "1"
_OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
_ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")

PROVIDER = "mock"
if not _FORCE_MOCK:
    if _OPENAI_KEY:
        PROVIDER = "openai"
    elif _ANTHROPIC_KEY:
        PROVIDER = "anthropic"

_DEFAULT_MODELS = {"openai": "gpt-4o-mini", "anthropic": "claude-haiku-4-5-20251001"}
MODEL = os.environ.get("AGENT_MODEL") or _DEFAULT_MODELS.get(PROVIDER, "")

_client = None
if PROVIDER == "openai":
    try:
        from openai import OpenAI

        _client = OpenAI(api_key=_OPENAI_KEY)
    except Exception as e:  # pragma: no cover - import/credential issues
        print(f"[agents] OpenAI init failed, falling back to mock: {e}")
        PROVIDER = "mock"
elif PROVIDER == "anthropic":
    try:
        from anthropic import Anthropic

        _client = Anthropic(api_key=_ANTHROPIC_KEY)
    except Exception as e:  # pragma: no cover - import/credential issues
        print(f"[agents] Anthropic init failed, falling back to mock: {e}")
        PROVIDER = "mock"

_USE_MOCK = PROVIDER == "mock"


def using_mock() -> bool:
    return _USE_MOCK


# ----------------------------------------------------------------- real LLM ---

def call_llm(prompt: str, max_tokens: int = 200) -> str:
    if PROVIDER == "openai":
        resp = _client.chat.completions.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""
    # anthropic
    resp = _client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


# -------------------------------------------------------------- mock speech ---

_MOCK_LINES = {
    "wolf": [
        "I hear everyone pointing fingers, but where's the actual evidence? Let's slow down.",
        "Honestly {sus} has been awfully quiet — quiet people are usually hiding something.",
        "I'm just a villager like the rest of you. Pinning this on me wastes a day.",
    ],
    "seer": [
        "I've been watching the patterns, and {sus}'s story doesn't add up for me.",
        "Trust me when I say we should look hard at {sus} before we lose another night.",
        "I have a strong read here. {sus} is the one I'd watch.",
    ],
    "villager": [
        "Something about {sus}'s answers feels rehearsed. I'm suspicious.",
        "I want to hear {sus} explain that last vote — it didn't make sense.",
        "We can't keep stalling. My gut says {sus} is a wolf.",
    ],
}


def _mock_speak(player, state) -> str:
    others = [p.name for p in state.alive_players() if p.idx != player.idx]
    sus = random.choice(others) if others else "someone"
    line = random.choice(_MOCK_LINES.get(player.role, _MOCK_LINES["villager"]))
    return line.format(sus=sus)


# ------------------------------------------------------------------- public ---

def agent_speak(player, state) -> str:
    if _USE_MOCK:
        return _mock_speak(player, state)
    return call_llm(prompts.day_prompt(player, state)).strip()


def _parse_choice(text: str, keyword: str, candidates, fallback_pool):
    m = re.search(rf"{keyword}:\s*([A-Za-z]+)", text, re.IGNORECASE)
    if m:
        name = m.group(1)
        target = next((p for p in candidates if p.name.lower() == name.lower()), None)
        if target:
            return target
    return random.choice(fallback_pool) if fallback_pool else None


def agent_vote(player, state):
    others = [p for p in state.alive_players() if p.idx != player.idx]
    if _USE_MOCK:
        # Villagers/seer lean toward an actual wolf; wolves deflect onto village.
        if player.role == "wolf":
            pool = [p for p in others if p.role != "wolf"] or others
        else:
            pool = [p for p in others if p.role == "wolf"] or others
        target = random.choice(pool)
        return target, f"VOTE: {target.name}"
    text = call_llm(prompts.vote_prompt(player, state), max_tokens=120)
    target = _parse_choice(text, "VOTE", others, others)
    return target, text


def wolf_pick_victim(wolf, state):
    village = state.alive_village()
    if _USE_MOCK:
        # Prefer the seer if alive, else random villager.
        seer = next((p for p in village if p.role == "seer"), None)
        target = seer or (random.choice(village) if village else None)
        return target, f"KILL: {target.name if target else ''}"
    text = call_llm(prompts.night_wolf_prompt(wolf, state), max_tokens=120)
    target = _parse_choice(text, "KILL", village, village)
    return target, text


def seer_inspect(seer, state):
    others = [p for p in state.alive_players() if p.idx != seer.idx]
    if _USE_MOCK:
        target = random.choice(others) if others else None
        return target, f"INSPECT: {target.name if target else ''}"
    text = call_llm(prompts.seer_prompt(seer, state), max_tokens=120)
    target = _parse_choice(text, "INSPECT", others, others)
    return target, text
