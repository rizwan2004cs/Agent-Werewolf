"""Prompt templates — the discussion is the show. Agents talk like real people:
short, simple, punchy. They reason from the actual game facts (who died, who was
voted out and what they turned out to be). Wolves coordinate and misdirect; the
seer plays its knowledge INDIRECTLY (never states a role outright).

Wolves and the seer return a hidden THOUGHT next to their public SPEECH."""
from __future__ import annotations

from .state import PERSONA

_STYLE = (
    "Talk like a real person in a casual group chat. Short and simple — ONE or TWO "
    "sentences, 25 words MAX. Plain everyday words. Do NOT repeat what someone already "
    "said; add a NEW point or react to the last speaker. No fancy or formal language."
)

_TWO_LINE = (
    "Output EXACTLY two lines, nothing else:\n"
    "SPEECH: <what you say out loud>\n"
    "THOUGHT: <your real secret plan, max 12 plain words>"
)


def _roster(state):
    alive = ", ".join(p.name for p in state.alive_players())
    dead = ", ".join(p.name for p in state.players if not p.alive) or "none"
    return alive, dead


def _log(state, n: int = 8) -> str:
    lines = "\n".join(f"{e['speaker']}: {e['text']}" for e in state.discussion_log[-n:])
    return lines or "(no one has spoken yet)"


def _context(state) -> str:
    """Hard facts everyone can reason from — deaths and exposed roles."""
    lines = []
    nr = state.night_result
    if nr:
        v = state.by_name(nr["victimName"])
        role = f" — turned out to be a {v.revealed_role}" if v and v.revealed_role else ""
        lines.append(f"Last night {nr['victimName']} was killed{role}.")
    for p in state.players:
        if not p.alive and p.revealed_role and (not nr or p.name != nr.get("victimName")):
            lines.append(f"{p.name} was voted out — turned out to be a {p.revealed_role}.")
    return " ".join(lines) or "It's the first day; nobody has died yet."


def _base(player, state) -> str:
    alive, _ = _roster(state)
    persona = PERSONA.get(player.name, "")
    return (
        f"You are {player.name}, playing the party game Werewolf. You are {persona}\n"
        f"Still alive: {alive}.\nSo far: {_context(state)}\n"
        f"What's been said:\n{_log(state)}"
    )


def _seer_brief(known: dict) -> str:
    if not known:
        return "You haven't learned anyone's role yet."
    return "You secretly know: " + "; ".join(f"{n} is a {r}" for n, r in known.items()) + "."


# ------------------------------------------------------------------- night ----

def wolf_night(wolf, targets) -> str:
    names = ", ".join(t.name for t in targets)
    return (
        f"You are {wolf.name}, a werewolf. Tonight your pack kills one player.\n"
        f"You can kill: {names}.\nKill the biggest threat — whoever sounds like the seer, or the "
        "sharpest player closing in on you. Reply with ONLY the name."
    )


def seer_night(seer, targets) -> str:
    names = ", ".join(t.name for t in targets)
    return (
        f"You are {seer.name}, the Seer. Tonight you secretly learn one player's true role.\n"
        f"Players you haven't checked: {names}.\nCheck whoever is most useful to know. "
        "Reply with ONLY the name."
    )


# ---------------------------------------------------------------- day speak ---

def day_speak(player, state, seer_known=None) -> str:
    base = _base(player, state)
    if player.role == "wolf":
        partner = next((w.name for w in state.wolves() if w.idx != player.idx and w.alive), None)
        return base + (
            f"\n\nSECRET: You are a WEREWOLF. Your partner is {partner or 'already dead'}. "
            "Act like a worried villager. Use the facts above to quietly steer suspicion onto a REAL "
            "villager, and never defend your partner too openly.\n" + _STYLE + "\n" + _TWO_LINE
        )
    if player.role == "seer":
        return base + (
            f"\n\nSECRET: You are the SEER. {_seer_brief(seer_known or {})} "
            "NEVER say you are the seer, and NEVER say outright that someone 'is a villager' or 'is a "
            "wolf'. Be INDIRECT: act like it's a gut read — softly vouch for someone you know is good "
            "(\"I trust Vera\") or nudge suspicion onto someone you know is bad (\"something's off about "
            "Dax\"), without explaining how you know.\n" + _STYLE + "\n" + _TWO_LINE
        )
    return base + (
        "\n\nYou're a normal villager. Use the facts above — who died, who was voted out and what they "
        "turned out to be — to name ONE suspect and say why in plain words.\n" + _STYLE +
        "\nOutput ONLY your spoken line."
    )


# ------------------------------------------------------------------- vote ----

def vote(player, state, seer_known=None) -> str:
    alive, _ = _roster(state)
    candidates = ", ".join(p.name for p in state.alive_players() if p.idx != player.idx)
    note = ""
    if player.role == "wolf":
        partner = next((w.name for w in state.wolves() if w.idx != player.idx and w.alive), None)
        note = (f"(Secret: you're a wolf, partner is {partner or 'dead'}. Vote out a villager others "
                "already suspect — never your partner.)")
    elif player.role == "seer":
        known = seer_known or {}
        live_wolves = [n for n, r in known.items()
                       if r == "wolf" and state.by_name(n) and state.by_name(n).alive]
        if live_wolves:
            note = f"(Secret: you're the seer. {_seer_brief(known)} Vote a wolf you know: {', '.join(live_wolves)}.)"
        else:
            note = f"(Secret: you're the seer. {_seer_brief(known)} Vote your best read.)"
    return (
        f"You are {player.name}. {note}\nStill alive: {alive}.\nSo far: {_context(state)}\n"
        f"Recent talk:\n{_log(state)}\n\nVote out one player from: {candidates}.\n"
        "Give ONE short reason (max 12 words), then a new line with exactly:\nVOTE: <name>"
    )
