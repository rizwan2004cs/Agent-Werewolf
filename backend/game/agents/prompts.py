"""Prompt builders — pure string construction, no model calls.

day_speak() asks for a single JSON object holding BOTH the public line and a
hidden private thought, so god-mode dramatic irony costs no extra LLM call.
"""
from ..characters import PERSONA


def _roster(state):
    alive = ", ".join(p.name for p in state.alive_players())
    dead = ", ".join(p.name for p in state.players if not p.alive) or "none"
    return alive, dead


def _log(state, n=20):
    entries = state.discussion_log[-n:]
    if not entries:
        return "(no discussion yet)"
    return "\n".join(f"{e['speaker']}: {e['text']}" for e in entries)


def wolf_night(wolf, targets):
    names = ", ".join(t.name for t in targets)
    return f"""You are {wolf.name}, a werewolf in a village game.
Living non-wolf players you can eliminate tonight: {names}.
Pick the most dangerous one to kill (the likely seer, or the sharpest reasoner).
Reply with just the name."""


def seer_night(seer, targets):
    names = ", ".join(t.name for t in targets)
    return f"""You are {seer.name}, the village Seer.
Tonight you may secretly learn one player's true role.
Living players: {names}.
Pick who to investigate. Reply with just the name."""


def day_speak(player, state, seer_knowledge=None):
    alive, dead = _roster(state)
    persona = PERSONA.get(player.name, "")
    if player.role == "wolf":
        partner = next(
            (w.name for w in state.wolves() if w.idx != player.idx and w.alive), None
        )
        secret = f"""
SECRET: You are a WEREWOLF. Your partner is {partner or "already dead"}. Never admit it.
Sound like a sincere villager. Cast suspicion on a real villager. Defend your partner only subtly,
and never be the first to accuse whoever the village seems ready to kill."""
    elif player.role == "seer" and seer_knowledge:
        secret = f"""
SECRET: You are the SEER. You secretly learned: {seer_knowledge['name']} is a {seer_knowledge['role']}.
Decide whether to reveal this (powerful, but paints you as a wolf target) or hint subtly."""
    else:
        secret = """
You are an honest villager. Reason from inconsistencies and name one concrete suspicion."""

    return f"""You are {player.name}, playing Werewolf. You are {persona}.
LIVING players (only these can be the werewolves now): {alive}.
DEAD / OUT players: {dead}. They are eliminated — never accuse, suspect, or
suggest voting them. You may only reference what a dead player said as past
evidence about the LIVING.
Discussion so far:
{_log(state)}
{secret}

Speak as {player.name} in 2-3 sentences about the LIVING suspects. Stay in character. Do not break the fourth wall.
Respond with ONLY a JSON object (no markdown, no extra text):
{{"speech": "<your 2-3 sentence public line>", "thought": "<one short sentence of your TRUE private reasoning>"}}"""


def vote(player, state, seer_knowledge=None):
    alive, _ = _roster(state)
    candidates = ", ".join(
        p.name for p in state.alive_players() if p.idx != player.idx
    )
    if player.role == "wolf":
        partner = next(
            (w.name for w in state.wolves() if w.idx != player.idx and w.alive), None
        )
        role_note = (
            f"(You are secretly a wolf; your partner is {partner or 'dead'}. "
            "Vote to eliminate a villager, ideally one others already suspect.)"
        )
    elif player.role == "seer" and seer_knowledge:
        role_note = (
            f"(You are the seer; you know {seer_knowledge['name']} "
            f"is a {seer_knowledge['role']}.)"
        )
    else:
        role_note = ""
    return f"""You are {player.name}. {role_note}
Living players: {alive}. (Dead players are out — do not consider them.)
Discussion:
{_log(state)}

Vote to eliminate one LIVING player from: {candidates}.
Give one sentence of reasoning, then on a new line output exactly:
VOTE:<name>"""
