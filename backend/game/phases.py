"""The six phases, each a function over (state, narrator).

Phases mutate GameState, drive pacing beats, delegate decisions to `agents`,
betting to `markets` (off-chain play money), adjudication to `rules`, and
narration to the narrator. They contain no transport or parsing logic.
"""
import random
import re
import time

from . import agents, human, livestate, markets, rules
from .config import config
from .narrator import Narrator
from .state import GameState, Player

DISCUSSION_SUBROUNDS = 2
HUMAN_SPEAK_TIMEOUT = 180   # seconds to wait for the human's line before moving on
HUMAN_VOTE_TIMEOUT = 120


def _beat(seconds: float) -> None:
    if config.pace > 0:
        time.sleep(seconds * config.pace)


def _hold_speech(text: str) -> None:
    """Keep a spoken line on screen long enough for the UI typewriter (~30
    chars/sec) to finish rendering it, plus a short reading beat — so each
    agent finishes before the next one speaks. Skipped entirely at PACE=0
    (instant console/test runs). Length-based, not scaled by PACE."""
    if config.pace <= 0:
        return
    n = len(text or "")
    time.sleep(min(16.0, max(3.5, n / 22)))  # > n/30 typing time, with margin


def _say_beat(state, nar, player, speech, thought, kind, event):
    """Render one player's spoken line as a tagged dramatic beat (defense /
    last words): drive the speech bubble, log it, and hold it on screen."""
    state.speaking_idx = player.idx
    state.speech_kind = kind
    player.current_speech = speech
    state.discussion_log.append(
        {
            "round": state.round,
            "speaker": player.name,
            "text": speech,
            "ts": int(time.time()),
            "kind": kind,
        }
    )
    state.private_reasoning.append(
        {"speaker": player.name, "role": player.role, "thought": thought}
    )
    nar.emit(event, name=player.name, text=speech)
    _hold_speech(speech)
    player.current_speech = None
    state.speech_kind = None


def _most_accused(state: GameState) -> Player | None:
    """The living player most often named by OTHERS in this round's discussion —
    the village's prime suspect. None if it's too early or no one stands out."""
    living = state.alive_players()
    if len(living) < 3:
        return None
    counts = {p.idx: 0 for p in living}
    for e in state.discussion_log:
        if e.get("round") != state.round:
            continue
        speaker, text = e.get("speaker"), e.get("text", "")
        for p in living:
            if p.name == speaker:
                continue
            first = re.escape(p.name.split()[0])
            full = re.escape(p.name)
            if re.search(rf"\b({full}|{first})\b", text, re.IGNORECASE):
                counts[p.idx] += 1
    top = max(counts, key=counts.get)
    return state.players[top] if counts[top] > 0 else None


def _human_speak(state: GameState, p: Player) -> tuple[str, str]:
    """Block until the human submits a line (or times out)."""
    state.speaking_idx = p.idx
    state.awaiting = {"kind": "speak", "playerIdx": p.idx}
    livestate.save(state)
    human.begin()
    text = human.wait(HUMAN_SPEAK_TIMEOUT)
    state.awaiting = None
    if not (text and text.strip()):
        text = f"({p.name} stays quiet, watching the room.)"
    return text.strip(), "(human player)"


def _human_vote(state: GameState, p: Player) -> Player:
    """Block until the human picks who to eliminate (or times out -> random)."""
    options = [x.name for x in state.alive_players() if x.idx != p.idx]
    state.awaiting = {"kind": "vote", "playerIdx": p.idx, "options": options}
    livestate.save(state)
    human.begin()
    name = human.wait(HUMAN_VOTE_TIMEOUT)
    state.awaiting = None
    target = state.by_name(name) if name else None
    if not target or target.idx == p.idx or not target.alive:
        target = state.by_name(random.choice(options))
    return target


def setup(state: GameState, nar: Narrator) -> None:
    state.phase = "setup"
    state.betting_open = state.betting
    nar.emit("setup", roster=[(p.name, p.role) for p in state.players])
    if state.betting:
        markets.open_game_winner(state)
        markets.refresh_pools(state)
    _beat(2)
    livestate.save(state)


def night(state: GameState, nar: Narrator) -> None:
    state.phase = "night"
    state.speaking_idx = None
    _beat(2)
    victim = agents.night_wolf_pick(state)
    seer, target = agents.night_seer_pick(state)
    state.seer_knowledge = (
        {"name": target.name, "role": target.role} if target else None
    )
    state.pending_kill = victim
    nar.emit(
        "night",
        victim=victim.name,
        seer=seer.name if seer else None,
        target=target.name if target else None,
        target_role=target.role if target else None,
    )
    livestate.save(state)


def morning(state: GameState, nar: Narrator) -> None:
    state.phase = "morning"
    v = state.pending_kill
    rules.eliminate(v)
    state.night_result = {"victimName": v.name, "victimIdx": v.idx}
    nar.emit("morning", victim=v.name, role=v.role)
    if state.betting:
        markets.open_who_voted_out(state)
        state.betting_open = True
        markets.refresh_pools(state)
    _beat(2)
    livestate.save(state)


def discussion(state: GameState, nar: Narrator) -> None:
    state.phase = "discussion"
    state.betting_open = False
    state.speech_kind = None
    if state.betting:
        markets.freeze_open(state)
    nar.emit("discussion_start")
    for sub in range(DISCUSSION_SUBROUNDS):
        nar.emit("subround", n=sub + 1)
        for p in state.alive_players():
            state.speaking_idx = p.idx
            sk = state.seer_knowledge if p.role == "seer" else None
            # The human types their own line; agents (and the human's words to
            # them) are indistinguishable — all go into the same shared log.
            if p.is_human:
                speech, thought = _human_speak(state, p)
            else:
                speech, thought = agents.speak(p, state, sk)
            p.current_speech = speech
            state.discussion_log.append(
                {
                    "round": state.round,
                    "speaker": p.name,
                    "text": speech,
                    "ts": int(time.time()),
                }
            )
            state.private_reasoning.append(
                {"speaker": p.name, "role": p.role, "thought": thought}
            )
            nar.emit("speech", name=p.name, text=speech)
            _hold_speech(speech)  # let the line fully render before the next speaker
            p.current_speech = None
    state.speaking_idx = None
    livestate.save(state)


def voting(state: GameState, nar: Narrator) -> None:
    state.phase = "voting"
    state.votes = []

    # Drama beat: the village's prime suspect pleads their case before the vote.
    accused = _most_accused(state)
    if accused and not accused.is_human:
        nar.emit("accused", name=accused.name)
        sk = state.seer_knowledge if accused.role == "seer" else None
        speech, thought = agents.defend(accused, state, sk)
        _say_beat(state, nar, accused, speech, thought, "defense", "defense")

    nar.emit("voting_start")
    for p in state.alive_players():
        sk = state.seer_knowledge if p.role == "seer" else None
        if p.is_human:
            target = _human_vote(state, p)
        else:
            target, _ = agents.vote(p, state, sk)
        state.votes.append({"voter": p.name, "target": target.name})
        nar.emit("vote", voter=p.name, target=target.name)
        _beat(0.5)
    out = rules.tally(state.votes, state)
    rules.eliminate(out)
    nar.emit("eliminated", name=out.name, role=out.role)
    if state.betting:
        markets.resolve_who_voted_out(state, out.name)

    # Drama beat: the eliminated player's role is now public — give them a final line.
    if not out.is_human:
        lw_speech, lw_thought = agents.last_words(out, state)
        _say_beat(state, nar, out, lw_speech, lw_thought, "last_words", "last_words")
    state.speaking_idx = None

    state.phase = "resolution"
    _beat(1)
    livestate.save(state)


def end(state: GameState, nar: Narrator) -> None:
    state.phase = "ended"
    if not state.winner:
        state.winner = rules.final_winner(state)
    for p in state.players:
        p.revealed_role = p.role
    nar.emit(
        "game_over",
        winner=state.winner,
        roles=[(p.name, p.role) for p in state.players],
    )
    # Freeze any market that never reached a vote (e.g. a who_voted_out opened
    # in the morning of the round the game ended on) so no further bets land on
    # a market that will never resolve.
    if state.betting:
        markets.freeze_open(state)
        markets.resolve_game_winner(state, state.winner)
    livestate.save(state)
