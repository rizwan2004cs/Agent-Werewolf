"""Prompt templates + agent personalities. Tune these — they are the demo."""
from __future__ import annotations

# A personality line per agent makes the difference between robotic and watchable.
PERSONALITIES = {
    "Luna": "analytical and calm; you reason out loud and weigh evidence carefully.",
    "Caspian": "charming and quick; you deflect suspicion with humour and never over-defend.",
    "Theron": "blunt and confident; you push hard on one suspect and rally others.",
    "Mira": "cautious and observant; you notice contradictions and ask pointed questions.",
    "Dax": "earnest and a little anxious; you want to do the right thing and name a suspect.",
}


def _roster(state) -> str:
    living = ", ".join(p.name for p in state.alive_players())
    dead = ", ".join(p.name for p in state.players if not p.alive) or "none"
    return f"Alive: {living}. Eliminated: {dead}."


def _recent_discussion(state, limit: int = 12) -> str:
    log = state.discussion_log[-limit:]
    if not log:
        return "(no discussion yet)"
    return "\n".join(f"{e['speaker']}: {e['text']}" for e in log)


def _role_brief(player) -> str:
    if player.role == "wolf":
        return (
            "You are a WEREWOLF. At night your pack secretly kills a villager. "
            "By day you must blend in, deflect suspicion, and steer votes toward "
            "villagers. NEVER reveal you are a wolf. Be subtle; do not over-defend."
        )
    if player.role == "seer":
        return (
            "You are the SEER. Each night you learn one player's true alignment. "
            "Use what you know carefully — if you out yourself too early the wolves "
            "will target you tonight."
        )
    return (
        "You are a VILLAGER. You have no special info. Reason from behaviour and "
        "contradictions to find the wolves. Name a specific suspect each turn."
    )


def day_prompt(player, state) -> str:
    persona = PERSONALITIES.get(player.name, "thoughtful.")
    return f"""You are {player.name}, playing social-deduction Werewolf. You are {persona}
{_role_brief(player)}

{_roster(state)}
Round {state.round} of {state.max_rounds}. It is the day discussion.

Recent discussion:
{_recent_discussion(state)}

Speak ONE short, natural turn (1-3 sentences) as {player.name}. Advance the
conversation: react to what was said, share suspicion or defend yourself in
character. Do not narrate actions or use stage directions. Output only your spoken line."""


def vote_prompt(player, state) -> str:
    persona = PERSONALITIES.get(player.name, "thoughtful.")
    candidates = ", ".join(p.name for p in state.alive_players() if p.idx != player.idx)
    return f"""You are {player.name}, {persona}
{_role_brief(player)}

{_roster(state)}
Round {state.round}. The discussion is over; it is time to vote someone out.

Discussion recap:
{_recent_discussion(state, limit=20)}

Choose exactly one player to eliminate from: {candidates}.
First give one short sentence of reasoning, then on a new line output your vote
in EXACTLY this format:
VOTE: <name>"""


def night_wolf_prompt(player, state) -> str:
    targets = ", ".join(p.name for p in state.alive_village())
    return f"""You are {player.name}, a WEREWOLF. It is night. Your pack must choose one
villager to eliminate. Alive villagers (and seer) you may target: {targets}.

{_recent_discussion(state, limit=10)}

Pick the most dangerous target (a likely seer, or someone close to catching you).
Give one short sentence of reasoning, then output EXACTLY:
KILL: <name>"""


def seer_prompt(player, state) -> str:
    targets = ", ".join(p.name for p in state.alive_players() if p.idx != player.idx)
    return f"""You are {player.name}, the SEER. It is night. Choose one player to
investigate and learn their true alignment. Candidates: {targets}.
Give one short sentence of reasoning, then output EXACTLY:
INSPECT: <name>"""
