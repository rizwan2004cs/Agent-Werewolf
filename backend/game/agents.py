"""LLM agent wrappers. Provider auto-detects (OpenAI > Anthropic > mock); set
MOCK_AGENTS=1 or leave keys unset to run deterministic offline mock agents."""
from __future__ import annotations

import os
import re
import json
import random

from . import prompts

# Provider auto-detect: OpenAI if its key is present, else Anthropic, else mock.
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
    except Exception as e:  # pragma: no cover
        print(f"[agents] OpenAI init failed, falling back to mock: {e}")
        PROVIDER = "mock"
elif PROVIDER == "anthropic":
    try:
        from anthropic import Anthropic

        _client = Anthropic(api_key=_ANTHROPIC_KEY)
    except Exception as e:  # pragma: no cover
        print(f"[agents] Anthropic init failed, falling back to mock: {e}")
        PROVIDER = "mock"

_USE_MOCK = PROVIDER == "mock"


def using_mock() -> bool:
    return _USE_MOCK


def call_llm(prompt: str, max_tokens: int = 200, json_mode: bool = False) -> str:
    if PROVIDER == "openai":
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        resp = _client.chat.completions.create(
            model=MODEL, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return resp.choices[0].message.content or ""
    resp = _client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


# ------------------------------------------------------------------ parsing ---

def _extract(text: str, names) -> str | None:
    for n in names:
        if re.search(rf"\b{re.escape(n)}\b", text, re.IGNORECASE):
            return n
    return None


def _extract_vote(text: str, names) -> str | None:
    m = re.search(r"VOTE:\s*([A-Za-z]+)", text, re.IGNORECASE)
    if m and any(m.group(1).lower() == n.lower() for n in names):
        return m.group(1)
    return _extract(text, names)


def _split_speech(raw: str):
    """Pull SPEECH:/THOUGHT: out of a wolf/seer reply. Falls back to whole text."""
    speech = thought = None
    m = re.search(r"SPEECH:\s*(.+?)(?:\n\s*THOUGHT:|$)", raw, re.IGNORECASE | re.DOTALL)
    t = re.search(r"THOUGHT:\s*(.+)$", raw, re.IGNORECASE | re.DOTALL)
    if m:
        speech = m.group(1).strip()
    if t:
        thought = t.group(1).strip()
    if not speech:
        speech = raw.strip()
    return speech, thought


# -------------------------------------------------------------- mock speech ---

_MOCK_LINES = {
    "wolf": [
        "I hear fingers pointing, but where's the actual evidence? Let's not rush, {sus}.",
        "Honestly {sus} has been awfully quiet — quiet people are usually hiding something.",
        "I'm a villager same as you. Burning a day on me just helps the real wolves.",
    ],
    "seer": [
        "I've been watching the patterns, and {sus}'s story doesn't add up for me.",
        "Trust me — we should look hard at {sus} before we lose another night.",
        "I have a strong read here. {sus} is the one I'd watch.",
    ],
    "villager": [
        "Something about {sus}'s answers feels rehearsed. I'm suspicious.",
        "I want {sus} to explain that last point — it didn't sit right.",
        "We can't keep stalling. My gut says {sus} is a wolf.",
    ],
}


def _mock_speak(player, state):
    others = [p.name for p in state.alive_players() if p.idx != player.idx]
    sus = random.choice(others) if others else "someone"
    line = random.choice(_MOCK_LINES.get(player.role, _MOCK_LINES["villager"])).format(sus=sus)
    thought = None
    if player.role == "wolf":
        thought = f"Keep the heat on {sus}; protect my partner and stay unremarkable."
    elif player.role == "seer":
        thought = "Hold my read for now — revealing too early gets me killed tonight."
    return line, thought


# ------------------------------------------------------------------- public ---

def night_wolf_pick(state):
    """-> (victim Player | None, reasoning str)."""
    targets = [p for p in state.alive_players() if p.role != "wolf"]
    if not targets:
        return None, ""
    if _USE_MOCK:
        seer = next((p for p in targets if p.role == "seer"), None)
        victim = seer or random.choice(targets)
        return victim, f"Take out {victim.name} — neutralize the biggest threat to us."
    actor = next((w for w in state.alive_wolves()), None)
    raw = call_llm(prompts.wolf_night(actor, targets), max_tokens=60)
    name = _extract(raw, [t.name for t in targets])
    victim = state.by_name(name) or random.choice(targets)
    return victim, raw.strip()


def night_seer_pick(state):
    """-> (seer Player | None, target Player | None)."""
    seer = next((p for p in state.alive_players() if p.role == "seer"), None)
    if not seer:
        return None, None
    others = [p for p in state.alive_players() if p.idx != seer.idx]
    if not others:
        return seer, None
    known = set(getattr(state, "seer_known", {}).keys())
    targets = [p for p in others if p.name not in known] or others
    if _USE_MOCK:
        return seer, random.choice(targets)
    raw = call_llm(prompts.seer_night(seer, targets), max_tokens=40)
    name = _extract(raw, [t.name for t in targets])
    return seer, (state.by_name(name) or random.choice(targets))


def _parse_speak(raw: str):
    """JSON {"speech","thought"} -> tuple, with graceful fallback (clean-branch)."""
    try:
        data = json.loads(raw)
        speech = str(data.get("speech", "")).strip()
        thought = str(data.get("thought", "")).strip()
        if speech:
            return speech, (thought or None)
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    return _split_speech((raw or "...").strip())   # legacy SPEECH:/THOUGHT: fallback


def speak(player, state, seer_knowledge=None):
    """One JSON call -> (speech, thought) for EVERY role (thought feeds god mode)."""
    if _USE_MOCK:
        return _mock_speak(player, state)
    raw = call_llm(prompts.day_speak(player, state, seer_knowledge),
                   max_tokens=150, json_mode=True)
    return _parse_speak(raw)


def vote(player, state, seer_knowledge=None):
    """-> (target Player, reasoning str)."""
    cands = [p for p in state.alive_players() if p.idx != player.idx]
    if _USE_MOCK:
        if player.role == "wolf":
            pool = [p for p in cands if p.role != "wolf"] or cands
        else:
            pool = [p for p in cands if p.role == "wolf"] or cands
        t = random.choice(pool)
        return t, f"VOTE: {t.name}"
    raw = call_llm(prompts.vote(player, state, seer_knowledge), max_tokens=50)
    name = _extract_vote(raw, [c.name for c in cands])
    target = state.by_name(name)
    if not target or target.idx == player.idx:
        target = random.choice(cands)
    return target, raw.strip()
