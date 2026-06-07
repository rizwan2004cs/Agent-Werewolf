"""The game loop: setup -> rounds (night, morning, discussion, voting, resolution)
-> ended. Mutates a GameState in place so server.py can serve it live while this
runs on a background thread. Pacing beats (time.sleep) give the frontend time to
animate each moment."""
from __future__ import annotations

import os
import time
import random

from .state import (
    GameState,
    Player,
    Market,
    ROLE_WOLF,
    ROLE_VILLAGER,
    ROLE_SEER,
    ROLE_TO_ENUM,
    TEAM_WOLF,
    TEAM_VILLAGE,
)
from . import agents, chain

# Default 5-player roster. One wolf keeps a 5-player / 2-round game watchable;
# add a second wolf + two villagers for a 7-player "pack" once you have the seats.
ROSTER = [
    ("Luna", ROLE_VILLAGER),
    ("Caspian", ROLE_WOLF),
    ("Theron", ROLE_VILLAGER),
    ("Mira", ROLE_SEER),
    ("Dax", ROLE_VILLAGER),
]

POT_MON = os.environ.get("GAME_POT_MON", "1.0")
PACE = float(os.environ.get("PACE_SECONDS", "1.2"))   # gap between speeches/beats
_DEPLOYER_KEY = os.environ.get("ORCHESTRATOR_KEY", "0x" + "00" * 32)

_market_counter = 0


def new_state() -> GameState:
    return GameState(max_rounds=int(os.environ.get("MAX_ROUNDS", "2")), pot="0")


# --------------------------------------------------------------------- beats --

def _beat(state: GameState, phase: str, hold: float | None = None):
    state.phase = phase
    time.sleep(hold if hold is not None else PACE)


def _record_reasoning(state, speaker, thought):
    state.private_reasoning.append(
        {"round": state.round, "speaker": speaker, "thought": thought}
    )


# --------------------------------------------------------------------- setup --

def setup(state: GameState):
    state.phase = "setup"
    wallets = chain.new_agent_wallets(len(ROSTER))
    salt_base = "0x" + "11" * 32
    role_hashes = []
    for idx, (name, role) in enumerate(ROSTER):
        salt = salt_base
        p = Player(idx=idx, name=name, address=wallets[idx]["address"], role=role, salt=salt)
        state.players.append(p)
        role_hashes.append(chain.role_hash(ROLE_TO_ENUM[role], idx, salt))

    pot_wei = int(float(POT_MON) * 1e18)
    state.pot = POT_MON
    state.game_id = chain.create_game(
        [p.address for p in state.players], role_hashes, pot_wei, _DEPLOYER_KEY
    )
    # remember keys for per-agent votes
    state._wallet_keys = {p.idx: wallets[p.idx]["key"] for p in state.players}  # type: ignore[attr-defined]
    print(f"[loop] game {state.game_id} set up with {len(state.players)} players "
          f"(agents={'mock' if agents.using_mock() else agents.MODEL}, "
          f"chain={'mock' if chain.MOCK_CHAIN else 'live'})")


# ------------------------------------------------------------------- markets --

def _open_market(state, mtype, options, seed=False) -> Market:
    global _market_counter
    m = Market(
        market_id=_market_counter,
        game_id=state.game_id,
        type=mtype,
        round=state.round,
        options=list(options),
    )
    _market_counter += 1
    if seed and chain.MOCK_CHAIN:
        # Seed small mock pools so the odds UI has something to show.
        for opt in options:
            m.pools[opt] = f"{round(random.uniform(0.05, 0.4), 2)}"
    chain.open_market(state.game_id, _MARKET_TYPE_ENUM.get(mtype, 0), len(options), _DEPLOYER_KEY)
    state.markets.append(m)
    return m


_MARKET_TYPE_ENUM = {
    "game_winner": 0,
    "who_voted_out": 1,
    "catches_wolf_this_round": 2,
    "seer_survives": 3,
}


def open_setup_markets(state):
    _open_market(state, "game_winner", [TEAM_WOLF, TEAM_VILLAGE], seed=True)
    _open_market(state, "seer_survives", ["yes", "no"], seed=True)


def open_round_markets(state):
    names = [p.name for p in state.alive_players()]
    _open_market(state, "who_voted_out", names, seed=True)
    _open_market(state, "catches_wolf_this_round", ["yes", "no"], seed=True)


def freeze_all_open_markets(state):
    state.betting_open = False
    for m in state.markets:
        if not m.resolved:
            m.frozen = True
            chain.freeze_market(m.market_id, _DEPLOYER_KEY)


def _resolve_market(state, m: Market, winning_option: str):
    m.resolved = True
    m.winning_option = winning_option
    try:
        idx = m.options.index(winning_option)
    except ValueError:
        idx = 0
    chain.resolve_market(m.market_id, idx, _DEPLOYER_KEY)


# --------------------------------------------------------------------- night --

def night(state: GameState):
    _beat(state, "night", hold=2.0)   # "the village sleeps…"
    state.betting_open = True

    # Wolf picks a victim.
    victim = None
    for wolf in state.alive_wolves():
        victim, reasoning = agents.wolf_pick_victim(wolf, state)
        _record_reasoning(state, wolf.name, f"(night) targeting {victim.name if victim else '?'}: {reasoning}")
        break

    # Seer investigates (private knowledge; surfaces only in god mode).
    for seer in [p for p in state.alive_players() if p.role == ROLE_SEER]:
        inspected, reasoning = agents.seer_inspect(seer, state)
        if inspected:
            verdict = "WOLF" if inspected.role == ROLE_WOLF else "not a wolf"
            _record_reasoning(state, seer.name, f"(night) inspected {inspected.name}: {verdict}")

    if victim:
        # commit/reveal the kill on-chain, then apply it.
        chain.commit_night_kill(state.game_id, b"\x00" * 32, _DEPLOYER_KEY)
        chain.reveal_night_kill(state.game_id, victim.idx, victim.salt, _DEPLOYER_KEY)
        victim.alive = False
        state.night_result = {"victim": victim.name}


def morning(state: GameState):
    _beat(state, "morning", hold=1.5)
    if state.night_result:
        print(f"[loop] morning: {state.night_result['victim']} was found eliminated")


# ---------------------------------------------------------------- discussion --

def run_discussion(state: GameState):
    state.phase = "discussion"
    freeze_all_open_markets(state)     # BETTING FREEZES during discussion
    rounds = int(os.environ.get("DISCUSSION_ROUNDS", "2"))
    for _ in range(rounds):
        for p in state.alive_players():
            speech = agents.agent_speak(p, state)
            p.last_speech = speech
            state.discussion_log.append(
                {
                    "round": state.round,
                    "turn": p.idx,
                    "speaker": p.name,
                    "text": speech,
                    "ts": int(time.time()),
                }
            )
            time.sleep(PACE)


# ------------------------------------------------------------------- voting ---

def run_voting(state: GameState):
    state.phase = "voting"
    state.votes = []
    keys = getattr(state, "_wallet_keys", {})
    tally: dict[int, int] = {}
    for p in state.alive_players():
        target, reasoning = agents.agent_vote(p, state)
        if target is None:
            continue
        _record_reasoning(state, p.name, f"(vote) {reasoning}")
        chain.submit_vote(state.game_id, target.idx, keys.get(p.idx, _DEPLOYER_KEY))
        state.votes.append({"voter": p.name, "target": target.name})
        tally[target.idx] = tally.get(target.idx, 0) + 1
        time.sleep(PACE * 0.6)

    chain.resolve_vote(state.game_id, _DEPLOYER_KEY)
    return _apply_elimination(state, tally)


def _apply_elimination(state: GameState, tally: dict[int, int]):
    if not tally:
        return None
    out_idx = max(tally, key=lambda k: tally[k])
    victim = state.players[out_idx]
    # reveal the eliminated player's role on-chain (audit) then publicly.
    chain.reveal_role(state.game_id, victim.idx, ROLE_TO_ENUM[victim.role], victim.salt, _DEPLOYER_KEY)
    victim.alive = False
    victim.revealed_role = victim.role
    return victim


def resolve_round_markets(state: GameState, eliminated: Player | None):
    state.phase = "resolution"
    for m in state.markets:
        if m.resolved:
            continue
        if m.type == "who_voted_out" and m.round == state.round and eliminated:
            if eliminated.name in m.options:
                _resolve_market(state, m, eliminated.name)
        elif m.type == "catches_wolf_this_round" and m.round == state.round:
            caught = bool(eliminated and eliminated.role == ROLE_WOLF)
            _resolve_market(state, m, "yes" if caught else "no")
    time.sleep(PACE)


# --------------------------------------------------------------------- win ----

def check_win(state: GameState) -> bool:
    wolves = len(state.alive_wolves())
    village = len(state.alive_village())
    if wolves == 0:
        state.winner = TEAM_VILLAGE
    elif wolves >= village:
        state.winner = TEAM_WOLF
    else:
        return False
    return True


def end_game(state: GameState):
    state.phase = "ended"
    # reveal every role publicly + on-chain.
    for p in state.players:
        if p.revealed_role is None:
            chain.reveal_role(state.game_id, p.idx, ROLE_TO_ENUM[p.role], p.salt, _DEPLOYER_KEY)
            p.revealed_role = p.role

    team_enum = 1 if state.winner == TEAM_WOLF else 2
    chain.declare_winner(state.game_id, team_enum, _DEPLOYER_KEY)

    # settle game-level markets.
    seer = next((p for p in state.players if p.role == ROLE_SEER), None)
    for m in state.markets:
        if m.resolved:
            continue
        if m.type == "game_winner":
            _resolve_market(state, m, state.winner)
        elif m.type == "seer_survives":
            _resolve_market(state, m, "yes" if (seer and seer.alive) else "no")
    print(f"[loop] game over — winner: {state.winner}")


# -------------------------------------------------------------- orchestration --

def run_game(state: GameState):
    setup(state)
    open_setup_markets(state)

    for rnd in range(1, state.max_rounds + 1):
        state.round = rnd
        night(state)
        morning(state)
        if check_win(state):
            break
        open_round_markets(state)
        run_discussion(state)
        eliminated = run_voting(state)
        resolve_round_markets(state, eliminated)
        if check_win(state):
            break
        state.betting_open = True   # reopen between rounds

    if state.winner is None:
        # ran out of rounds — decide by who holds the majority.
        check_win(state) or state.__setattr__(
            "winner", TEAM_WOLF if state.alive_wolves() else TEAM_VILLAGE
        )
    end_game(state)
