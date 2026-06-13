"""Off-chain, play-money betting — a self-contained parimutuel simulation.

This used to talk to a Monad contract; now everything lives in memory. Each
bettor is identified by a client-generated id ("address") and starts with a
fixed play-money balance. Bets are pooled per market/option; when a market
resolves, the whole pool is split among the winners pro-rata to their stake
(classic parimutuel), and winnings are credited back to their balance.

Nothing here touches a chain, a wallet, or the network — it just mutates the
in-memory GameState (markets/pools) plus a couple of module-level ledgers.

Function names match what `phases.py` calls, so the game loop is unchanged.
"""
from .state import GameState, Market

# Each new bettor starts with this much play money.
START_BALANCE = 100.0

# Ephemeral ledgers (reset per game). They don't need to survive a restart —
# a fresh game starts everyone's balance over, which is fine for a demo.
_balances: dict[str, float] = {}
# market_id -> { address -> { option -> staked amount } }
_stakes: dict[int, dict[str, dict[str, float]]] = {}


def reset() -> None:
    """Clear all betting state. Called when a new game starts."""
    global _balances, _stakes
    _balances = {}
    _stakes = {}


def _new_market_id(state: GameState) -> int:
    # Derive from existing markets so ids stay unique even after a
    # restart-resume (when the ephemeral ledgers are empty but state isn't).
    return max((m.market_id for m in state.markets), default=-1) + 1


def balance(address: str) -> float:
    """Current play-money balance for a bettor (seeded on first sight)."""
    if address not in _balances:
        _balances[address] = START_BALANCE
    return _balances[address]


def _pools_for(market_id: int, options: list[str]) -> dict[str, float]:
    totals = {opt: 0.0 for opt in options}
    for by_opt in _stakes.get(market_id, {}).values():
        for opt, amt in by_opt.items():
            if opt in totals:
                totals[opt] += amt
    return totals


def _sync_pools(state: GameState) -> None:
    """Copy live pool sizes (as strings) onto each market for serialization."""
    for m in state.markets:
        pools = _pools_for(m.market_id, m.options)
        m.pools = {opt: f"{pools[opt]:.2f}" for opt in m.options}


# ---- market lifecycle (called from phases.py) -----------------------------

def open_game_winner(state: GameState) -> Market:
    market = Market(
        market_id=_new_market_id(state),
        type="game_winner",
        options=["wolves", "village"],
    )
    _stakes[market.market_id] = {}
    state.markets.append(market)
    return market


def open_who_voted_out(state: GameState) -> Market:
    living = [p.name for p in state.alive_players()]
    market = Market(
        market_id=_new_market_id(state),
        type="who_voted_out",
        options=living,
        round=state.round,
    )
    _stakes[market.market_id] = {}
    state.markets.append(market)
    return market


def freeze_open(state: GameState) -> None:
    """Freeze every market that is still open (called when discussion starts)."""
    for m in state.markets:
        if not m.resolved and not m.frozen:
            m.frozen = True


def resolve_who_voted_out(state: GameState, out_name: str) -> None:
    m = next(
        (
            m
            for m in state.markets
            if m.type == "who_voted_out"
            and m.round == state.round
            and not m.resolved
        ),
        None,
    )
    if m and out_name in m.options:
        _settle(state, m, out_name)


def resolve_game_winner(state: GameState, winner: str) -> None:
    m = next((m for m in state.markets if m.type == "game_winner"), None)
    if m and winner in m.options:
        _settle(state, m, winner)


def refresh_pools(state: GameState) -> None:
    """Pull live pool sizes into each market (so /state shows odds)."""
    _sync_pools(state)


# ---- betting ---------------------------------------------------------------

def place_bet(state: GameState, market_id: int, option: str, address: str, amount: float) -> dict:
    """Record a play-money bet. Returns {ok, message, balance}."""
    address = (address or "").strip()
    if not address:
        return {"ok": False, "error": "missing bettor id"}
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid amount"}
    if amount <= 0:
        return {"ok": False, "error": "amount must be positive"}

    m = next((m for m in state.markets if m.market_id == market_id), None)
    if m is None:
        return {"ok": False, "error": "market not found"}
    if m.resolved:
        return {"ok": False, "error": "market already resolved"}
    if m.frozen or not state.betting_open:
        return {"ok": False, "error": "betting is closed for this phase"}
    if option not in m.options:
        return {"ok": False, "error": "invalid option"}

    bal = balance(address)
    if amount > bal:
        return {"ok": False, "error": f"not enough points (balance {bal:.2f})"}

    _balances[address] = bal - amount
    book = _stakes.setdefault(market_id, {}).setdefault(address, {})
    book[option] = book.get(option, 0.0) + amount
    _sync_pools(state)
    return {
        "ok": True,
        "message": f"Bet {amount:.2f} pts on {option}",
        "balance": _balances[address],
    }


def _settle(state: GameState, m: Market, winning_option: str) -> None:
    """Resolve a market: split the whole pool among winners pro-rata and
    credit winnings back to their play-money balances. Records each payout on
    `state.payouts` so the client can show what landed."""
    m.resolved = True
    m.winning_option = winning_option
    pools = _pools_for(m.market_id, m.options)
    total = sum(pools.values())
    win_pool = pools.get(winning_option, 0.0)
    m.pools = {opt: f"{pools[opt]:.2f}" for opt in m.options}
    if win_pool <= 0:
        return  # nobody backed the winner — pool evaporates
    for address, by_opt in _stakes.get(m.market_id, {}).items():
        staked = by_opt.get(winning_option, 0.0)
        if staked <= 0:
            continue
        payout = total * staked / win_pool
        _balances[address] = balance(address) + payout
        state.payouts.append(
            {
                "marketId": m.market_id,
                "type": m.type,
                "address": address,
                "option": winning_option,
                "amount": f"{payout:.2f}",
            }
        )
