"""Prompt templates — the discussion is the show. Agents must talk like real
people in a casual voice chat: short, simple, punchy. No essays. The audience
reads these live, so plain language beats clever language every time.

Wolves and the seer return a hidden THOUGHT next to their public SPEECH (free
dramatic irony for god mode); villagers just speak."""
from __future__ import annotations

from .state import PERSONA

# The house style every speaking agent must follow.
_STYLE = (
    "Talk like a real person in a casual group chat. Short and simple — ONE or TWO "
    "sentences, 25 words MAX. Use plain everyday words a kid could follow. Do NOT repeat "
    "what someone already said; add a NEW point or react to the last speaker. No fancy or "
    "formal language, no lists."
)


def _roster(state):
    alive = ", ".join(p.name for p in state.alive_players())
    dead = ", ".join(p.name for p in state.players if not p.alive) or "none"
    return alive, dead


def _log(state, n: int = 8) -> str:
    lines = "\n".join(f"{e['speaker']}: {e['text']}" for e in state.discussion_log[-n:])
    return lines or "(no one has spoken yet)"


def _base(player, state) -> str:
    alive, _ = _roster(state)
    persona = PERSONA.get(player.name, "")
    return (
        f"You are {player.name}, playing the party game Werewolf. You are {persona}\n"
        f"Still in: {alive}.\n"
        f"What's been said:\n{_log(state)}"
    )


_TWO_LINE = (
    "Output EXACTLY two lines, nothing else:\n"
    "SPEECH: <what you say out loud>\n"
    "THOUGHT: <your real secret plan, max 12 plain words>"
)


# ------------------------------------------------------------------- night ----

def wolf_night(wolf, targets) -> str:
    names = ", ".join(t.name for t in targets)
    return (
        f"You are {wolf.name}, a werewolf. Tonight your pack kills one player.\n"
        f"You can kill: {names}.\nPick the biggest threat (the seer, or the sharpest player). "
        "Reply with ONLY the name."
    )


def seer_night(seer, targets) -> str:
    names = ", ".join(t.name for t in targets)
    return (
        f"You are {seer.name}, the Seer. Tonight you secretly learn one player's true role.\n"
        f"Players: {names}.\nPick who to check. Reply with ONLY the name."
    )


# ---------------------------------------------------------------- day speak ---

def day_speak(player, state, seer_knowledge=None) -> str:
    base = _base(player, state)
    if player.role == "wolf":
        partner = next((w.name for w in state.wolves() if w.idx != player.idx and w.alive), None)
        return base + (
            f"\n\nSECRET: You are a WEREWOLF. Your partner is {partner or 'already dead'}. "
            "Never admit it. Act like a normal villager, gently point suspicion at a real "
            f"villager, and don't defend your partner too hard.\n{_STYLE}\n{_TWO_LINE}"
        )
    if player.role == "seer" and seer_knowledge:
        return base + (
            f"\n\nSECRET: You are the SEER. Last night you found out {seer_knowledge['name']} "
            f"is a {seer_knowledge['role']}. Choose: call them out now (risky — wolves may kill "
            f"you tonight) or drop a hint.\n{_STYLE}\n{_TWO_LINE}"
        )
    return base + (
        "\n\nYou're a normal villager. Point at ONE person you find suspicious and say why in "
        f"plain words.\n{_STYLE}\nOutput ONLY your spoken line."
    )


# ------------------------------------------------------------------- vote ----

def vote(player, state, seer_knowledge=None) -> str:
    alive, _ = _roster(state)
    candidates = ", ".join(p.name for p in state.alive_players() if p.idx != player.idx)
    note = ""
    if player.role == "wolf":
        partner = next((w.name for w in state.wolves() if w.idx != player.idx and w.alive), None)
        note = (f"(Secret: you're a wolf, partner is {partner or 'dead'}. Vote out a villager "
                "others already suspect — never your partner.)")
    elif player.role == "seer" and seer_knowledge:
        note = f"(Secret: you're the seer; you know {seer_knowledge['name']} is a {seer_knowledge['role']}.)"
    return (
        f"You are {player.name}. {note}\nStill in: {alive}.\n"
        f"Recent talk:\n{_log(state)}\n\n"
        f"Vote out one player from: {candidates}.\n"
        "Give ONE short, simple reason (max 12 words), then a new line with exactly:\nVOTE: <name>"
    )
