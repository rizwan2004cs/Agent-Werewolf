"""The game loop: setup -> rounds(night, morning, discussion, voting, resolution)
-> ended. Mutates a GameState in place; server.py serves it live while this runs
on a background thread. Every chain call is wrapped so a failed tx never crashes
the game. Pacing beats (time.sleep) let the frontend animate each moment."""
from __future__ import annotations

import os
import time
import random

from .state import (
    new_game as _new_game,
    Market,
    ROLE_WOLF,
    ROLE_SEER,
    ROLE_TO_ENUM,
    TEAM_WOLVES,
    TEAM_VILLAGE,
)
from . import agents, chain

POT_MON = os.environ.get("GAME_POT_MON", "1.0")
PACE = float(os.environ.get("PACE_SECONDS", "1.2"))         # gap between speeches
DISCUSSION_SUBROUNDS = int(os.environ.get("DISCUSSION_ROUNDS", "2"))
MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", "2"))

STATE = None   # the live GameState, served by FastAPI


def new_state():
    return _new_game(max_rounds=MAX_ROUNDS, pot=POT_MON)


# ------------------------------------------------------------------ helpers ---

def _reason(state, speaker, role, thought):
    state.private_reasoning.append({"speaker": speaker, "role": role, "thought": thought})


def _safe(fn, *args):
    """Call a chain function; log + swallow failures so the game keeps running."""
    try:
        return fn(*args)
    except Exception as e:  # pragma: no cover - network/tx issues
        print(f"[loop] chain call {getattr(fn, '__name__', fn)} failed: {e}")
        return None


# ------------------------------------------------------------------- phases ---

def run_game(state):
    global STATE
    STATE = state
    setup_phase(state)
    for rnd in range(1, state.max_rounds + 1):
        state.round = rnd
        night_phase(state)
        morning_phase(state)
        if check_win(state):
            break
        discussion_phase(state)
        voting_phase(state)
        if check_win(state):
            break
    end_phase(state)


def setup_phase(state):
    state.phase = "setup"
    state.betting_open = True
    # Commit role hashes immutably on-chain (provably fair).
    role_hashes = [chain.role_hash(ROLE_TO_ENUM[p.role], p.idx, p.salt) for p in state.players]
    gid = _safe(chain.create_game, role_hashes)
    if gid is not None:
        state.game_id = gid
    _open_market(state, "game_winner", [TEAM_WOLVES, TEAM_VILLAGE], seed=True)
    _refresh_pools(state)
    print(f"[loop] game {state.game_id}: {len(state.players)} players "
          f"(agents={'mock' if agents.using_mock() else agents.MODEL}, "
          f"chain={'mock' if chain.MOCK_CHAIN else 'live'})")
    time.sleep(2.0)


def night_phase(state):
    state.phase = "night"
    state.speaking_idx = None
    time.sleep(2.0)

    victim, _wreason = agents.night_wolf_pick(state)
    actor = next(iter(state.alive_wolves()), None)
    if victim and actor:
        _reason(state, actor.name, "wolf", f"(night) We're taking out {victim.name} tonight.")

    seer, target = agents.night_seer_pick(state)
    if seer and target:
        verdict = "a WOLF!" if target.role == ROLE_WOLF else "not a wolf"
        state._seer_knowledge = {"name": target.name, "role": target.role}
        _reason(state, seer.name, "seer", f"(night) I checked {target.name} — {verdict}")
    else:
        state._seer_knowledge = None

    state._pending_kill = victim


def morning_phase(state):
    state.phase = "morning"
    v = getattr(state, "_pending_kill", None)
    if v:
        v.alive = False
        v.revealed_role = v.role
        state.night_result = {"victimName": v.name, "victimIdx": v.idx}
        _safe(chain.record_kill, state.game_id, v.idx)
    # Open the who-voted-out market over the living players.
    living = [p.name for p in state.alive_players()]
    _open_market(state, "who_voted_out", living, seed=True, rnd=state.round)
    state.betting_open = True
    _refresh_pools(state)
    time.sleep(1.5)


def discussion_phase(state):
    state.phase = "discussion"
    state.betting_open = False
    for m in state.markets:
        if not m.resolved and not m.frozen:
            m.frozen = True
            _safe(chain.freeze_market, m.market_id)

    for _ in range(DISCUSSION_SUBROUNDS):
        for p in state.alive_players():
            state.speaking_idx = p.idx
            sk = getattr(state, "_seer_knowledge", None) if p.role == ROLE_SEER else None
            speech, thought = agents.speak(p, state, sk)
            p.current_speech = speech
            state.discussion_log.append({
                "round": state.round, "speaker": p.name,
                "text": speech, "ts": int(time.time()),
            })
            if thought:
                _reason(state, p.name, p.role, thought)
            time.sleep(PACE)
            p.current_speech = None
    state.speaking_idx = None


def voting_phase(state):
    state.phase = "voting"
    state.votes = []
    counts: dict[int, int] = {}
    for p in state.alive_players():
        sk = getattr(state, "_seer_knowledge", None) if p.role == ROLE_SEER else None
        target, reasoning = agents.vote(p, state, sk)
        if target is None:
            continue
        state.votes.append({"voter": p.name, "target": target.name})
        _reason(state, p.name, p.role, f"(vote) {reasoning}")
        _safe(chain.record_vote, state.game_id, p.idx, target.idx)
        counts[target.idx] = counts.get(target.idx, 0) + 1
        time.sleep(PACE * 0.5)

    if counts:
        out_idx = max(counts, key=counts.get)
        out = state.players[out_idx]
        out.alive = False
        out.revealed_role = out.role
        _resolve_who_voted_out(state, out.name)
    state.phase = "resolution"
    time.sleep(1.0)


def end_phase(state):
    state.phase = "ended"
    if state.winner is None:
        if not check_win(state):
            state.winner = TEAM_WOLVES if state.alive_wolves() else TEAM_VILLAGE
    for p in state.players:
        p.revealed_role = p.role
    _safe(chain.declare_winner, state.game_id, 1 if state.winner == TEAM_WOLVES else 2)
    gw = next((m for m in state.markets if m.type == "game_winner" and not m.resolved), None)
    if gw:
        _resolve_market(state, gw, state.winner)
    state.speaking_idx = None
    print(f"[loop] game over — winner: {state.winner}")


def check_win(state) -> bool:
    aw = len(state.alive_wolves())
    av = len(state.alive_village())
    if aw == 0:
        state.winner = TEAM_VILLAGE
        return True
    if aw >= av:
        state.winner = TEAM_WOLVES
        return True
    return False


# ------------------------------------------------------------------ markets ---

def _open_market(state, mtype, options, seed=False, rnd=None):
    mid = _safe(chain.open_market, state.game_id, len(options))
    if mid is None:
        mid = len(state.markets)
    m = Market(market_id=mid, type=mtype, options=list(options), round=rnd or state.round)
    if seed and chain.MOCK_CHAIN:
        for o in options:
            m.pools[o] = f"{random.uniform(0.05, 0.4):.2f}"
    state.markets.append(m)
    return m


def _refresh_pools(state):
    if chain.MOCK_CHAIN:
        return
    for m in state.markets:
        pools = _safe(chain.get_pools, m.market_id)
        if pools:
            m.pools = {o: pools[i] for i, o in enumerate(m.options)}


def _resolve_market(state, m, winning_option):
    m.resolved = True
    m.winning_option = winning_option
    try:
        idx = m.options.index(winning_option)
    except ValueError:
        idx = 0
    _safe(chain.resolve_market, m.market_id, idx)


def _resolve_who_voted_out(state, out_name):
    m = next((m for m in state.markets
              if m.type == "who_voted_out" and m.round == state.round and not m.resolved), None)
    if m and out_name in m.options:
        _resolve_market(state, m, out_name)


# ---------------------------------------------------------------- console run -

if __name__ == "__main__":
    s = new_state()
    run_game(s)
    print("\n=== WINNER:", s.winner, "===")
