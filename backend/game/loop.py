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
from . import agents, chain, history

POT_MON = os.environ.get("GAME_POT_MON", "1.0")
PACE = float(os.environ.get("PACE_SECONDS", "1.2"))         # minimum gap between speeches
DISCUSSION_SUBROUNDS = int(os.environ.get("DISCUSSION_ROUNDS", "2"))
MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", "2"))

# Reading-time pacing: hold each spoken line on screen long enough to read it
# (~20 chars/sec + a beat to settle), capped so the demo never drags.
READ_SECONDS_PER_CHAR = float(os.environ.get("READ_SECONDS_PER_CHAR", "0.05"))
READ_SECONDS_MAX = float(os.environ.get("READ_SECONDS_MAX", "8"))


def _hold_for(text: str | None) -> float:
    """Seconds to keep a speech bubble up: scales with line length."""
    return max(PACE, min(READ_SECONDS_MAX, 1.2 + len(text or "") * READ_SECONDS_PER_CHAR))

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

    victim, wreason = agents.night_wolf_pick(state)
    actor = next(iter(state.alive_wolves()), None)
    if victim and actor:
        # Surface the wolf's REAL reasoning (LLM output), not a canned line.
        why = (wreason or "").strip() or f"We're taking out {victim.name} tonight."
        _reason(state, actor.name, "wolf", f"(night) {why}")

    seer, target = agents.night_seer_pick(state)
    if seer and target:
        verdict = "a WOLF!" if target.role == ROLE_WOLF else "not a wolf"
        state.seer_known[target.name] = target.role   # accumulates across nights
        _reason(state, seer.name, "seer", f"(night) I checked {target.name} — {verdict}")

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
            sk = state.seer_known if p.role == ROLE_SEER else None
            speech, thought = agents.speak(p, state, sk)
            p.current_speech = speech
            state.discussion_log.append({
                "round": state.round, "speaker": p.name,
                "text": speech, "ts": int(time.time()),
            })
            if thought:
                _reason(state, p.name, p.role, thought)
            time.sleep(_hold_for(speech))
            p.current_speech = None
    state.speaking_idx = None


def voting_phase(state):
    state.phase = "voting"
    state.votes = []
    counts: dict[int, int] = {}
    for p in state.alive_players():
        sk = state.seer_known if p.role == ROLE_SEER else None
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
    state.betting_open = False
    if state.winner is None:
        if not check_win(state):
            state.winner = TEAM_WOLVES if state.alive_wolves() else TEAM_VILLAGE
    for p in state.players:
        p.revealed_role = p.role
    _safe(chain.declare_winner, state.game_id, 1 if state.winner == TEAM_WOLVES else 2)
    # Freeze any market that never reached a vote (e.g. a who_voted_out opened
    # the morning the game ended) so no further bets land on a market that
    # will never resolve. (Ported from clean-branch.)
    for m in state.markets:
        if not m.resolved and not m.frozen:
            m.frozen = True
            _safe(chain.freeze_market, m.market_id)
    gw = next((m for m in state.markets if m.type == "game_winner" and not m.resolved), None)
    if gw:
        _resolve_market(state, gw, state.winner)
    state.speaking_idx = None
    history.record(state)   # persist for /history (ported from clean-branch)
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

# Max sponsored stake per wallet per market — protects the operator bankroll.
BET_CAP_MON = float(os.environ.get("BET_CAP_MON", "0.25"))


def place_sponsored_bet(state, market_id: int, option: str, address: str, amount: float):
    """House-sponsored bet (called from server.py): the operator stakes on-chain
    on the user's behalf; we track whose bet it is and pay winners directly.
    Returns (ok, message)."""
    if not address or not address.startswith("0x") or len(address) != 42:
        return False, "invalid wallet address"
    if amount <= 0:
        return False, "stake must be positive"
    m = next((x for x in state.markets if x.market_id == market_id), None)
    if not m or m.frozen or m.resolved or not state.betting_open:
        return False, "betting is closed for this market"
    if option not in m.options:
        return False, "unknown option"
    spent = sum(float(b["amount"]) for b in state.sponsored_bets
                if b["address"].lower() == address.lower() and b["marketId"] == market_id)
    if spent + amount > BET_CAP_MON + 1e-9:
        return False, f"house cap is {BET_CAP_MON} MON per market per wallet"
    _safe(chain.place_bet, market_id, m.options.index(option), f"{amount:.6f}")
    # Mirror locally so odds move immediately (and at all, in mock mode).
    m.pools[option] = f"{float(m.pools.get(option, '0') or 0) + amount:.4f}"
    state.sponsored_bets.append({"marketId": market_id, "address": address,
                                 "option": option, "amount": f"{amount:.6f}"})
    return True, f"bet placed: {amount} MON on {option}"


def _pay_sponsored(state, m, winning_option):
    """Parimutuel payout for sponsored winners, sent straight to their wallets."""
    total = sum(float(v or 0) for v in m.pools.values())
    win_pool = float(m.pools.get(winning_option, "0") or 0)
    if win_pool <= 0:
        return
    per_addr: dict[str, float] = {}
    for b in state.sponsored_bets:
        if b["marketId"] == m.market_id and b["option"] == winning_option:
            a = b["address"].lower()
            per_addr[a] = per_addr.get(a, 0.0) + float(b["amount"])
    for addr, stake in per_addr.items():
        payout = total * stake / win_pool
        tx = _safe(chain.send_mon, addr, f"{payout:.6f}")
        state.payouts.append({"marketId": m.market_id, "address": addr,
                              "amount": f"{payout:.4f}",
                              "txHash": tx if isinstance(tx, str) else None})
        print(f"[loop] sponsored payout {payout:.4f} MON -> {addr}")


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
    _pay_sponsored(state, m, winning_option)


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
