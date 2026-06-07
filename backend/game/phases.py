"""The six phases, each a function over (state, narrator).

Phases mutate GameState, drive pacing beats, delegate decisions to `agents`,
betting to `chain.markets`, adjudication to `rules`, and narration to the
narrator. They contain no transport, parsing, or print logic of their own.
"""
import time

from . import agents, rules
from .chain import markets
from .config import config
from .narrator import Narrator
from .state import GameState

DISCUSSION_SUBROUNDS = 2


def _beat(seconds: float) -> None:
    if config.pace > 0:
        time.sleep(seconds * config.pace)


def setup(state: GameState, nar: Narrator) -> None:
    state.phase = "setup"
    state.betting_open = True
    nar.emit("setup", roster=[(p.name, p.role) for p in state.players])
    markets.open_game_winner(state)
    markets.refresh_pools(state)
    _beat(2)


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


def morning(state: GameState, nar: Narrator) -> None:
    state.phase = "morning"
    v = state.pending_kill
    rules.eliminate(v)
    state.night_result = {"victimName": v.name, "victimIdx": v.idx}
    nar.emit("morning", victim=v.name, role=v.role)
    markets.open_who_voted_out(state)
    state.betting_open = True
    markets.refresh_pools(state)
    _beat(2)


def discussion(state: GameState, nar: Narrator) -> None:
    state.phase = "discussion"
    state.betting_open = False
    markets.freeze_open(state)
    nar.emit("discussion_start")
    for sub in range(DISCUSSION_SUBROUNDS):
        nar.emit("subround", n=sub + 1)
        for p in state.alive_players():
            state.speaking_idx = p.idx
            sk = state.seer_knowledge if p.role == "seer" else None
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
            _beat(1.5)
            p.current_speech = None
    state.speaking_idx = None


def voting(state: GameState, nar: Narrator) -> None:
    state.phase = "voting"
    state.votes = []
    nar.emit("voting_start")
    for p in state.alive_players():
        sk = state.seer_knowledge if p.role == "seer" else None
        target, _ = agents.vote(p, state, sk)
        state.votes.append({"voter": p.name, "target": target.name})
        nar.emit("vote", voter=p.name, target=target.name)
        _beat(0.5)
    out = rules.tally(state.votes, state)
    rules.eliminate(out)
    nar.emit("eliminated", name=out.name, role=out.role)
    markets.resolve_who_voted_out(state, out.name)
    state.phase = "resolution"
    _beat(1)


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
    markets.freeze_open(state)
    markets.resolve_game_winner(state, state.winner)
