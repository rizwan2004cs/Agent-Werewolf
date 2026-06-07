"""Prompt templates — the discussion is the show, so this is where the win is.

Wolves and the seer return a hidden THOUGHT alongside their public SPEECH in the
same call (free dramatic irony for god mode); villagers just speak."""
from __future__ import annotations

from .state import PERSONA


def _roster(state):
    alive = ", ".join(p.name for p in state.alive_players())
    dead = ", ".join(p.name for p in state.players if not p.alive) or "none"
    return alive, dead


def _log(state, n: int = 20) -> str:
    lines = "\n".join(f"{e['speaker']}: {e['text']}" for e in state.discussion_log[-n:])
    return lines or "(no discussion yet)"


def _base(player, state) -> str:
    alive, dead = _roster(state)
    persona = PERSONA.get(player.name, "")
    return (
        f"You are {player.name}, playing Werewolf (social deduction). You are {persona}\n"
        f"Living players: {alive}. Dead: {dead}.\n"
        f"Round {state.round} of {state.max_rounds}. Discussion so far:\n{_log(state)}"
    )


_TWO_LINE = (
    "Output EXACTLY two lines and nothing else:\n"
    "SPEECH: <what you say out loud, 2-3 sentences, in character>\n"
    "THOUGHT: <your real private intent this turn, one sentence>"
)


# ------------------------------------------------------------------- night ----

def wolf_night(wolf, targets) -> str:
    names = ", ".join(t.name for t in targets)
    return (
        f"You are {wolf.name}, a werewolf. It is night and your pack kills one player.\n"
        f"Living non-wolves you can eliminate: {names}.\n"
        "Pick the most dangerous one (the likely seer, or the sharpest reasoner who could "
        "expose you). Reply with ONLY the name."
    )


def seer_night(seer, targets) -> str:
    names = ", ".join(t.name for t in targets)
    return (
        f"You are {seer.name}, the village Seer. Tonight you secretly learn one player's true role.\n"
        f"Living players: {names}.\nPick who to investigate. Reply with ONLY the name."
    )


# ---------------------------------------------------------------- day speak ---

def day_speak(player, state, seer_knowledge=None) -> str:
    base = _base(player, state)
    if player.role == "wolf":
        partner = next((w.name for w in state.wolves() if w.idx != player.idx and w.alive), None)
        return base + (
            f"\n\nSECRET: You are a WEREWOLF. Your partner is {partner or 'already dead'}. "
            "Never admit it. Sound like a sincere villager: cast suspicion on a real villager, "
            "defend your partner only subtly, and never over-defend yourself.\n" + _TWO_LINE
        )
    if player.role == "seer" and seer_knowledge:
        return base + (
            f"\n\nSECRET: You are the SEER. Last night you learned that "
            f"{seer_knowledge['name']} is a {seer_knowledge['role']}. Decide whether to reveal "
            "this (powerful, but paints you as the wolves' next target) or hint subtly.\n" + _TWO_LINE
        )
    return base + (
        "\n\nYou are an honest villager. Reason from inconsistencies and name one concrete "
        "suspect with a reason. Speak as yourself in 2-3 sentences. Output ONLY your spoken line."
    )


# ------------------------------------------------------------------- vote ----

def vote(player, state, seer_knowledge=None) -> str:
    alive, _ = _roster(state)
    candidates = ", ".join(p.name for p in state.alive_players() if p.idx != player.idx)
    note = ""
    if player.role == "wolf":
        partner = next((w.name for w in state.wolves() if w.idx != player.idx and w.alive), None)
        note = (f"(You are secretly a wolf; your partner is {partner or 'dead'}. Vote out a "
                "villager, ideally one others already suspect — never your partner.)")
    elif player.role == "seer" and seer_knowledge:
        note = f"(You are the seer; you know {seer_knowledge['name']} is a {seer_knowledge['role']}.)"
    return (
        f"You are {player.name}. {note}\n"
        f"Living players: {alive}.\nDiscussion:\n{_log(state)}\n\n"
        f"Vote to eliminate one player from: {candidates}.\n"
        "Give one sentence of reasoning, then on a new line output EXACTLY:\nVOTE: <name>"
    )
