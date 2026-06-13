"""Prompt builders — pure string construction, no model calls.

day_speak() asks for a single JSON object holding BOTH the public line and a
hidden private thought, so god-mode dramatic irony costs no extra LLM call.
The prompts are written to push the model toward SPECIFIC, LOGICAL, in-character
table talk — naming real suspects, reacting to real statements, and escalating
tension — so spectators actually feel the game.
"""
from ..characters import PERSONA


def _roster(state):
    alive = ", ".join(p.name for p in state.alive_players())
    dead = ", ".join(p.name for p in state.players if not p.alive) or "none"
    return alive, dead


def _log(state, n=16):
    entries = state.discussion_log[-n:]
    if not entries:
        return "(no one has spoken yet — you may be opening the discussion)"
    return "\n".join(f"{e['speaker']}: {e['text']}" for e in entries)


def _situation(state):
    """Hard facts the table can reason from: round, headcount, confirmed deaths."""
    lines = [
        f"It is Round {state.round} of {state.max_rounds}. "
        f"{len(state.alive_players())} players are still alive."
    ]
    nr = state.night_result
    if nr and nr.get("victimName"):
        victim = state.by_name(nr["victimName"])
        role = f" — confirmed {victim.role}" if (victim and victim.revealed_role) else ""
        lines.append(
            f"Last night the wolves killed {nr['victimName']}{role}."
        )
    # Anyone voted out is a CONFIRMED role — a fact, not a theory.
    confirmed = [
        f"{p.name} was eliminated and revealed as a {p.role}"
        for p in state.players
        if not p.alive and (not nr or p.name != nr.get("victimName"))
    ]
    for c in confirmed:
        lines.append(c)
    if state.round >= state.max_rounds:
        lines.append(
            "This is the FINAL round — the village must get this vote right or the wolves win. "
            "Stakes are at their highest."
        )
    return "\n".join(lines)


SPEAK_RULES = """How to speak (this is what makes the game gripping — follow it):
- BE SPECIFIC: name a LIVING player and react to something concrete they actually
  said or did this game. No vague, generic filler like "something feels off".
- BE LOGICAL: point at a real contradiction, a dodge, a flip-flop, a suspicious
  vote, or who benefited from a death. Build a case or tear one down.
- ADD SOMETHING NEW: don't just echo what others already said — bring a fresh
  angle, a question, a challenge, or a theory that moves the table forward.
- STAY IN CHARACTER and show real emotion: pressure, suspicion, confidence, fear.
  Make it personal. Talk like a real person at the table, not a narrator.
- Keep it to 2-3 punchy sentences. Never break the fourth wall, never mention
  being an AI, a model, a prompt, roles being "assigned", or this being a game."""


def _wolf_brief(player, state):
    partner = next(
        (w.name for w in state.wolves() if w.idx != player.idx and w.alive), None
    )
    final = state.round >= state.max_rounds
    push = (
        "It's the final round and you must avoid the vote — get a villager "
        "eliminated NOW. A confident, well-aimed accusation can stampede the table."
        if final
        else "Blend in. Sound like the most reasonable villager in the room."
    )
    return f"""SECRET — YOU ARE A WEREWOLF. {('Your surviving partner is ' + partner) if partner else 'Your partner is already dead, so you are alone — be extra careful.'}
Your goal: get VILLAGERS eliminated without ever being suspected. Tactics:
- {push}
- Cast doubt on a real villager, ideally one others already distrust, and pile on at the right moment (not first, not too eager).
- Defend your partner only subtly and indirectly — never leap to their rescue.
- If you're cornered, redirect with a sharp counter-accusation rather than over-explaining.
- A bold, risky move (a fake read, a surprise pivot) can win the game — use it when it fits.
Never admit or hint that you are a wolf."""


def _seer_brief(player, state, sk):
    final = state.round >= state.max_rounds
    if not sk:
        return """SECRET — YOU ARE THE SEER, but you haven't learned anything useful yet.
Probe the table, track who dodges, and set up trust so your future word carries weight."""
    is_wolf = sk["role"] == "wolf"
    if is_wolf:
        reveal = (
            "REVEAL IT NOW and hammer the point — name them, explain you investigated "
            "them, and rally every vote. This is your last chance."
            if final
            else "You can REVEAL it to swing the vote (powerful, but it paints a target on "
            "you for tonight's kill), or hint hard and bait them into exposing themselves."
        )
        return f"""SECRET — YOU ARE THE SEER. You secretly investigated {sk['name']} and KNOW they are a WEREWOLF.
This is hard truth, not a hunch. {reveal}
If you claim seer, expect a wolf to fake-claim seer too — pre-empt that and sound credible."""
    return f"""SECRET — YOU ARE THE SEER. You secretly investigated {sk['name']} and confirmed they are a {sk['role']} (NOT a wolf).
Use {sk['name']} as a trusted ally and anchor — defend them and steer suspicion toward the genuinely unknown players, without burning your seer claim too early."""


def _villager_brief(player, state):
    return """You are an HONEST VILLAGER with no special information — only logic and instinct.
Hunt the wolves: weigh who benefits from each death, who deflects, who over-defends
someone, and whose story shifted. Commit to ONE concrete, named suspicion and push on it."""


def wolf_night(wolf, targets):
    names = ", ".join(t.name for t in targets)
    return f"""You are {wolf.name}, a werewolf. Tonight you and your pack choose one victim to kill.
Living non-wolf players you can eliminate: {names}.
Kill the most dangerous threat to the wolves — the likely Seer, or the sharpest, most
persuasive reasoner who could rally the village against you.
Reply with just the name, nothing else."""


def seer_night(seer, targets):
    names = ", ".join(t.name for t in targets)
    return f"""You are {seer.name}, the village Seer. Tonight you may secretly learn ONE player's true role.
Living players you can investigate: {names}.
Pick the player whose role would most change the game to know — usually a loud, influential,
or suspiciously evasive player. Reply with just the name, nothing else."""


def day_speak(player, state, seer_knowledge=None):
    alive, dead = _roster(state)
    persona = PERSONA.get(player.name, "")
    if player.role == "wolf":
        secret = _wolf_brief(player, state)
    elif player.role == "seer":
        secret = _seer_brief(player, state, seer_knowledge)
    else:
        secret = _villager_brief(player, state)

    return f"""You are {player.name}, a player in a live game of Werewolf (social deduction).
PERSONA (fully inhabit this voice, temperament, and tactics): {persona}

{_situation(state)}

LIVING suspects — the wolves are hiding among THESE players: {alive}.
ELIMINATED — out of the game, their roles are CONFIRMED facts: {dead}.
Never accuse, suspect, or suggest voting an eliminated player. You may only cite what
a dead player said as evidence about the LIVING.

What's been said this game (most recent last):
{_log(state)}

{secret}

{SPEAK_RULES}

Respond with ONLY a JSON object (no markdown, no extra text):
{{"speech": "<your 2-3 sentence public line, fully in character>", "thought": "<one vivid sentence of your TRUE private reasoning — your real read and your actual plan>"}}"""


def defend(player, state, seer_knowledge=None):
    """The prime suspect gets to plead their case right before the vote."""
    alive, dead = _roster(state)
    persona = PERSONA.get(player.name, "")
    if player.role == "wolf":
        angle = (
            "You are SECRETLY A WOLF and you are about to be lynched. Do NOT confess. "
            "Lie with total conviction, poke holes in the case against you, and pin the "
            "suspicion on a specific living villager instead. This is do-or-die."
        )
    elif player.role == "seer" and seer_knowledge:
        angle = (
            f"You are SECRETLY THE SEER and you investigated {seer_knowledge['name']} "
            f"(a {seer_knowledge['role']}). You're about to be wrongly lynched — you can "
            "REVEAL your seer claim now to save yourself and redirect the village, but a "
            "wolf may fake-claim seer too. Sell it hard."
        )
    else:
        angle = (
            "You are INNOCENT and the village has the wrong person. Protest with real "
            "emotion, dismantle the logic against you, and point at who actually looks "
            "like a wolf among the living."
        )
    return f"""You are {player.name}. {persona}
The village has turned on YOU — you are the prime suspect and the vote is moments away.

{_situation(state)}
LIVING players: {alive}. ELIMINATED (out, roles confirmed): {dead}.
What's been said:
{_log(state)}

{angle}
Make your defense in 2-3 charged, in-character sentences. Be specific — answer the actual
accusations and name who the village should look at instead. Never break the fourth wall.

Respond with ONLY a JSON object (no markdown):
{{"speech": "<your 2-3 sentence defense, in character>", "thought": "<one vivid sentence of your TRUE reasoning right now>"}}"""


def last_words(player, state):
    """A just-eliminated player's final line. Their role is now public, so they
    can speak the truth — vindication, warning, taunt, or revelation."""
    persona = PERSONA.get(player.name, "")
    alive, _ = _roster(state)
    if player.role == "wolf":
        angle = (
            "The village got you. Go out with a wolf's snarl — a taunt, a warning that your "
            "pack is still out there, or a cryptic hint that rattles them."
        )
    elif player.role == "seer":
        angle = (
            "You were the SEER and they wasted you. Use your final breath to reveal what you "
            "knew and beg them to make it count."
        )
    else:
        angle = (
            "You were an INNOCENT VILLAGER and they killed the wrong person. Make them feel "
            "it — warn them the wolves are still among the living and that they just helped them."
        )
    return f"""You are {player.name}. {persona}
You have just been VOTED OUT, and your true role — {player.role.upper()} — is now revealed to everyone.
Living players who remain: {alive}.

{angle}
One or two unforgettable, in-character sentences. Speak the truth now; you have nothing to hide.
Never break the fourth wall.

Respond with ONLY a JSON object (no markdown):
{{"speech": "<your dramatic final words, in character>", "thought": "<one short sentence of your final private thought>"}}"""


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
            f"(SECRET: you are a wolf{', partnered with ' + partner if partner else ''}. "
            "Vote out a VILLAGER — ideally one the table already distrusts so your vote "
            "looks principled. NEVER vote your partner.)"
        )
    elif player.role == "seer" and seer_knowledge:
        role_note = (
            f"(SECRET: you are the seer; you investigated {seer_knowledge['name']} and "
            f"know they are a {seer_knowledge['role']}. Vote the wolf if you found one.)"
        )
    elif player.role == "seer":
        role_note = "(SECRET: you are the seer but have no confirmed wolf — vote your best logical read.)"
    else:
        role_note = "(You are an honest villager — vote the player your logic most suspects.)"
    return f"""You are {player.name}. {role_note}
Living players: {alive}. (Eliminated players are out — do not consider them.)
Discussion this game:
{_log(state)}

Decide who to eliminate from these LIVING candidates: {candidates}.
Give ONE sharp sentence of in-character reasoning that fits everything said above,
then on a NEW line output exactly:
VOTE:<name>"""
