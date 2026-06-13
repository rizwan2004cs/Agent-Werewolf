"""Keyless mock behaviour — plausible decisions with no API key, no cost.

Used when config.use_mock is True so the full game (and the whole UI) is
verifiable and demo-safe before any OpenAI key is provided.
"""
import random

_LINES = [
    "Something about last night doesn't sit right with me.",
    "I've been watching the voting patterns and one of you stands out.",
    "Let's not rush, but I do have a suspicion forming.",
    "Whoever's quiet right now is exactly who I'd watch.",
    "I'll say it plainly: that explanation was too convenient.",
    "We can't afford another wasted vote. Think it through.",
    "I trusted that read earlier and now I'm second-guessing it.",
    "The math points one direction and I don't like where it lands.",
]


def wolf_pick(state):
    targets = [p for p in state.alive_players() if p.role != "wolf"]
    seer = next((t for t in targets if t.role == "seer"), None)
    return seer if (seer and random.random() < 0.6) else random.choice(targets)


def seer_pick(seer, targets):
    return random.choice(targets)


def speak(player, state, seer_knowledge):
    others = [p.name for p in state.alive_players() if p.idx != player.idx]
    target = random.choice(others) if others else "someone"
    line = random.choice(_LINES)
    if random.random() < 0.5 and others:
        line = f"{line} {target}, you've been hard to read."
    if player.role == "wolf":
        thought = f"(wolf) Steer the heat toward {target}, keep my partner clean."
    elif player.role == "seer" and seer_knowledge:
        thought = (
            f"(seer) I know {seer_knowledge['name']} is a "
            f"{seer_knowledge['role']}; holding it for now."
        )
    else:
        thought = f"(villager) Genuinely unsure, leaning toward {target}."
    return line, thought


_DEFENSE = [
    "You're all wrong about me — ask yourselves who actually gains if I'm gone.",
    "I've been straight with you from the start. {other} is the one twisting every word.",
    "Lynch me and you'll see your mistake tomorrow, when another body turns up.",
    "This is a setup. Look at who's pushing hardest to bury me — that's your wolf.",
]
_LAST_WORDS = {
    "wolf": [
        "Heh. You got me — but you're still one short, and the pack doesn't sleep.",
        "Clever. Too bad it won't save the rest of you.",
    ],
    "seer": [
        "I was your Seer, you fools — I knew, and now you've thrown it away.",
        "Listen to me: watch the quiet one. I saw the truth before you silenced me.",
    ],
    "villager": [
        "You just killed an innocent. The wolves are still sitting right beside you.",
        "Wrong call. Remember my face when the next of you falls.",
    ],
}


def defend(player, state):
    others = [p.name for p in state.alive_players() if p.idx != player.idx]
    other = random.choice(others) if others else "someone here"
    line = random.choice(_DEFENSE).format(other=other)
    if player.role == "wolf":
        thought = f"(wolf) Cornered — sell my innocence and dump the heat on {other}."
    elif player.role == "seer":
        thought = "(seer) If I reveal now I might survive, but I paint a target on myself."
    else:
        thought = "(villager) I'm innocent and terrified they'll waste the vote on me."
    return line, thought


def last_words(player, state):
    line = random.choice(_LAST_WORDS.get(player.role, _LAST_WORDS["villager"]))
    return line, f"({player.role}) final words."


def vote(player, state, candidates: list[str]) -> str:
    if player.role == "wolf":
        prey = [
            p.name
            for p in state.alive_players()
            if p.role != "wolf" and p.idx != player.idx
        ]
        if prey:
            return random.choice(prey)
    if player.role == "seer" and state.seer_knowledge:
        known = state.seer_knowledge
        if known["role"] == "wolf" and known["name"] in candidates:
            return known["name"]
    return random.choice(candidates)
