"""Keyless mock behaviour — plausible decisions with no API key, no cost.

Used when config.use_mock is True (no key) AND as the resilient fallback when a
real LLM call fails or is rate-limited. So this module carries the whole "game
feel" when the model is unavailable: it must read like real, varied, situational
table talk, never canned filler.

How it stays believable:
- The table CONVERGES on a real suspect (counts who others keep naming).
- Lines are phase-aware: opening reactions to the night kill, mid-game cases,
  final-round high-stakes pleas, and direct reactions to the previous speaker.
- Roles play differently: villagers build cases, wolves deflect onto others and
  shield a partner, the seer hints (and pushes hard once they've caught a wolf).
- Templates fill in the real {victim}, {suspect}, {last} speaker and {ally}.
"""
import random


class _Safe(dict):
    """str.format_map helper: missing placeholders degrade gracefully."""

    def __missing__(self, key):
        return "someone"


# --- Speech pools -----------------------------------------------------------
# Keyed by role, then by beat: open (round 1 / first to speak), general
# (mid-game accusation), final (last round, win-or-lose), react (answering the
# previous speaker by name). Lots of lines so the feed rarely repeats itself.
LINES = {
    "villager": {
        "open": [
            "{victim} is gone and we slept through it. Who was pushing hardest to trust the wrong people last round?",
            "Let's be methodical. A wolf killed {victim} — so who benefits from that body?",
            "I won't pretend I'm calm. {victim} is dead and one of us did it. Start talking.",
            "Before we point fingers — who was quietest last night? That silence is loud to me.",
            "Two wolves are sitting at this table smiling. I want everyone's read, right now.",
            "We can't afford a wasted day. {victim}'s killer is still here. Let's work it.",
        ],
        "general": [
            "{suspect} keeps dodging every direct question — that reads guilty to me.",
            "Think about who gained from {victim}'s death. {suspect} moved on awfully fast.",
            "I don't buy {suspect}'s story; the timeline just doesn't add up.",
            "We've wasted enough time — {suspect} has been steering us away from the obvious.",
            "Notice how {suspect} only ever speaks to agree? That's a wolf hiding in the crowd.",
            "{victim} is dead and {suspect} hasn't said one useful thing. Convenient.",
            "My gut says {suspect}. Watch closely how they answer this.",
            "Every road leads back to {suspect} for me.",
            "{suspect} changed their story the second the pressure landed. I saw it.",
            "Why is {suspect} so eager to vote and so slow to explain themselves?",
            "I've been counting who defends who. {suspect} keeps covering for the wrong people.",
            "Call it instinct, but {suspect} has wolf written all over today.",
        ],
        "final": [
            "This is it. Get {suspect} wrong and the wolves win tonight — I'm certain it's them.",
            "No more hedging. It's {suspect} or we lose. Look at the whole game and tell me I'm wrong.",
            "Last vote. {suspect} has survived every round by hiding — that ends now.",
            "If we don't lynch {suspect} right here, there won't be a tomorrow for us.",
            "Everything points to {suspect}. Trust the pattern, not the panic.",
        ],
        "react": [
            "{last}, that's a neat speech, but it doesn't clear {suspect} — it protects them.",
            "I hear you, {last}, but you're aiming at the wrong throat. Watch {suspect}.",
            "{last} just said the quiet part out loud — and it lines up with {suspect}, not me.",
            "No, {last}. If you're right then explain why {suspect} keeps slipping the net.",
            "Funny, {last} — the people you trust are exactly the ones I'd burn first.",
        ],
    },
    "wolf": {
        "open": [
            "Awful about {victim}. We need to stay sharp and not let the loudest voice railroad us.",
            "Everyone's rattled — good, fear makes people honest. So who's overplaying it?",
            "Let's not stampede. A wrong lynch tonight hands the game away.",
            "I'm grieving {victim} like the rest of you. Let's think before we swing.",
            "Cool heads. The wolves want us panicking — I won't give them that.",
        ],
        "general": [
            "Let's stay calm — but honestly, {suspect} has been the loudest, and that worries me.",
            "I'm as shaken as anyone about {victim}. We should be looking hard at {suspect}.",
            "Don't tunnel on me — {suspect} is the one twisting the story here.",
            "I want the wolves gone too, and my read keeps landing on {suspect}.",
            "If we're voting, {suspect} is the safest call. Hear me out.",
            "{suspect} is trying way too hard to look innocent right now.",
            "Ask yourself who's been quietly steering every vote. That's {suspect}, not me.",
            "I've defended people before and been burned. Not today — {suspect} feels wrong.",
            "Look, I could be next. That's exactly why I'm telling you it's {suspect}.",
            "{suspect} accused me to take the heat off themselves. Classic move.",
        ],
        "final": [
            "Last vote, so let's get it right: {suspect}. Anything else throws the game.",
            "I've been with you the whole way. Trust me now — it has to be {suspect}.",
            "Lynch me and you lose. The real wolf is {suspect}, and you know it.",
            "Don't flinch at the finish line. {suspect} is the kill we needed all along.",
        ],
        "react": [
            "{last}, you're pointing at me to save yourself. The table should be watching {suspect}.",
            "Careful, {last}. That theory falls apart the second you apply it to {suspect}.",
            "I respect you, {last}, but you're doing the wolves' work for them aiming here.",
            "{last} wants a quick lynch — too quick. Slow down and look at {suspect}.",
        ],
    },
    "seer": {
        "open": [
            "I've been watching more than I've been talking. Give me the round and I'll guide you.",
            "Stay calm. I have a sense of where the rot is — let it play out a moment.",
            "{victim} mattered. Don't waste their death on a careless vote — follow me.",
        ],
        "general": [
            "I have a feeling about {suspect} I can't fully explain yet — keep your eyes on them.",
            "Trust me a little here: {suspect} is not who they're pretending to be.",
            "I've been reading the room, and {suspect} is the one that doesn't sit right.",
            "Hold off jumping at shadows — {suspect} is where the real danger is.",
            "I'm asking for a little faith: {suspect} is the wrong kind of quiet.",
            "Of everyone here, {suspect} is the read I'd bet my life on.",
        ],
        "final": [
            "No more hints — it's {suspect}, and this is the vote that ends it. Believe me.",
            "I've held back to stay alive. I can't anymore: vote {suspect} or we're finished.",
            "If you ever trusted my reads, trust this last one. {suspect}. Now.",
        ],
        "react": [
            "{last}, I know it sounds like instinct, but my instinct keeps landing on {suspect}.",
            "Listen, {last} — chase {suspect} with me and you'll see I was right.",
            "{last}, you're close, but you've got the name wrong. It's {suspect}.",
        ],
    },
}

# Seer who has actually investigated a wolf — push hard, almost-but-not-quite reveal.
SEER_WOLF = [
    "I'm telling you, look hard at {suspect} — everything in me says it's them.",
    "Don't waste this vote. {suspect} is the wolf, I'd stake my life on it.",
    "If you trust one thing I say tonight, trust this: it's {suspect}.",
    "I can't tell you how I know — but {suspect} is a wolf. Please, vote them.",
    "Forget my reasons. {suspect}. I have never been more sure of anything.",
]

_THOUGHTS = {
    "wolf": [
        "(wolf) Push the heat onto {suspect}; keep {ally} clean.",
        "(wolf) Stay likable, stay reasonable — and bury {suspect} while they trust me.",
        "(wolf) One more quiet day and the village eats itself.",
        "(wolf) {suspect} is the perfect mislynch. Sell it gently.",
    ],
    "seer": [
        "(seer) Steering the room toward {suspect} without painting a target on myself.",
        "(seer) I know more than I can say — every word is a risk.",
        "(seer) If they lynch me, my reads die with me. Move carefully.",
    ],
    "seer_wolf": [
        "(seer) I've caught {suspect} red-handed. Get the table there before I'm silenced.",
    ],
    "villager": [
        "(villager) Genuinely unsure, but {suspect} is where my gut keeps landing.",
        "(villager) Trying to read faces and follow the logic, not the panic.",
        "(villager) If I'm wrong about {suspect}, we might not get another chance.",
    ],
}

_recent: list[str] = []


def _pick(pool):
    """Random line, avoiding the last several used so the feed doesn't repeat."""
    fresh = [ln for ln in pool if ln not in _recent] or pool
    line = random.choice(fresh)
    _recent.append(line)
    if len(_recent) > 12:
        _recent.pop(0)
    return line


def _most_suspected(player, state, others):
    """Who is the table converging on? Counts mentions by other speakers."""
    if not others:
        return "someone here"
    counts = {n: 0 for n in others}
    for e in state.discussion_log[-20:]:
        if e.get("speaker") == player.name:
            continue
        text = e.get("text", "")
        for n in others:
            if n in text or n.split()[0] in text:
                counts[n] += 1
    best = max(counts, key=counts.get)
    if counts[best] == 0:
        return random.choice(others)
    # Mostly follow the crowd; sometimes diverge so the table isn't a hive mind.
    return best if random.random() < 0.7 else random.choice(others)


def _beat(player, state):
    """Pick which kind of line fits the moment."""
    if state.round >= state.max_rounds:
        return "final"
    spoken_this_round = sum(
        1 for e in state.discussion_log[-12:] if e.get("speaker") != player.name
    )
    if spoken_this_round <= 1:
        return "open"
    last = state.discussion_log[-1]["speaker"] if state.discussion_log else None
    if last and last != player.name and random.random() < 0.4:
        return "react"
    return "general"


def wolf_pick(state):
    targets = [p for p in state.alive_players() if p.role != "wolf"]
    seer = next((t for t in targets if t.role == "seer"), None)
    return seer if (seer and random.random() < 0.6) else random.choice(targets)


def seer_pick(seer, targets):
    return random.choice(targets)


def speak(player, state, seer_knowledge):
    others = [p.name for p in state.alive_players() if p.idx != player.idx]
    victim = (state.night_result or {}).get("victimName") or "our friend"
    last = state.discussion_log[-1]["speaker"] if state.discussion_log else None
    if last == player.name and len(state.discussion_log) > 1:
        last = state.discussion_log[-2]["speaker"]
    ally = next(
        (w.name for w in state.alive_players() if w.role == "wolf" and w.idx != player.idx),
        "my partner",
    )

    role = player.role
    # A wolf must never publicly throw their own partner under the bus.
    sus_pool = [n for n in others if n != ally] if role == "wolf" else others
    suspect = _most_suspected(player, state, sus_pool or others)
    thought_key = role
    if role == "seer" and seer_knowledge:
        known = seer_knowledge
        if known["role"] == "wolf" and known["name"] in others:
            suspect = known["name"]
            line = _pick(SEER_WOLF)
            thought_key = "seer_wolf"
        else:
            line = _pick(LINES["seer"][_beat(player, state)])
    elif role == "wolf":
        line = _pick(LINES["wolf"][_beat(player, state)])
    elif role == "seer":
        line = _pick(LINES["seer"][_beat(player, state)])
    else:
        line = _pick(LINES["villager"][_beat(player, state)])

    ctx = _Safe(suspect=suspect, victim=victim, last=last or "you", ally=ally)
    thought = random.choice(_THOUGHTS[thought_key]).format_map(ctx)
    return line.format_map(ctx), thought


# --- Defense (the accused pleads before the vote) ---------------------------
_DEFENSE = [
    "You're all wrong about me — ask yourselves who actually gains if I'm gone.",
    "I've been straight with you from the start. {other} is the one twisting every word.",
    "Lynch me and you'll see your mistake tomorrow, when another body turns up.",
    "This is a setup. Look at who's pushing hardest to bury me — that's your wolf.",
    "Kill me and you waste your last real ally. {other} is leading you off a cliff.",
    "I get it, I'm an easy target. But easy isn't right. Think it through.",
    "Every accusation against me came from {other}. Doesn't that tell you something?",
    "If I were a wolf, why would I keep dragging the table toward the truth?",
    "Fine — vote me. But when the next one of you dies, remember I warned you.",
    "I'm begging you: not me. Follow the kills, follow the votes. It's not me.",
]

_LAST_WORDS = {
    "wolf": [
        "Heh. You got me — but you're still one short, and the pack doesn't sleep.",
        "Clever. Too bad it won't save the rest of you.",
        "One wolf down. Sleep well tonight — if you can.",
        "You found me. Pity you found me last.",
    ],
    "seer": [
        "I was your Seer, you fools — I knew, and now you've thrown it away.",
        "Listen to me: watch the quiet one. I saw the truth before you silenced me.",
        "You just blinded yourselves. My last read was right — chase it.",
        "I gave you the answer and you buried it with me. Don't waste it.",
    ],
    "villager": [
        "You just killed an innocent. The wolves are still sitting right beside you.",
        "Wrong call. Remember my face when the next of you falls.",
        "I was on your side. The real monsters are clapping right now.",
        "No claws here. You'll know that by morning — too late.",
    ],
}


def defend(player, state):
    others = [p.name for p in state.alive_players() if p.idx != player.idx]
    other = random.choice(others) if others else "someone here"
    line = _pick(_DEFENSE).format_map(_Safe(other=other))
    if player.role == "wolf":
        thought = f"(wolf) Cornered — sell my innocence and dump the heat on {other}."
    elif player.role == "seer":
        thought = "(seer) If I reveal now I might survive, but I paint a target on myself."
    else:
        thought = "(villager) I'm innocent and terrified they'll waste the vote on me."
    return line, thought


def last_words(player, state):
    line = _pick(_LAST_WORDS.get(player.role, _LAST_WORDS["villager"]))
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
