"""Market lifecycle at the domain level.

Bridges the engine (which thinks in GameState + Market objects) and the raw
chain port (which thinks in ids + option indices). Every chain call is wrapped:
a failed tx must never crash the game loop — we log intent and carry on.
"""
from ..state import GameState, Market
from . import client


def open_game_winner(state: GameState) -> Market:
    try:
        mid = client.open_market(state.game_id, 2)
    except Exception as e:
        print(f"[chain] open_market(game_winner) failed: {e}")
        mid = -1
    market = Market(market_id=mid, type="game_winner", options=["wolves", "village"])
    state.markets.append(market)
    return market


def open_who_voted_out(state: GameState) -> Market:
    living = [p.name for p in state.alive_players()]
    try:
        mid = client.open_market(state.game_id, len(living))
    except Exception as e:
        print(f"[chain] open_market(who_voted_out) failed: {e}")
        mid = -1
    market = Market(
        market_id=mid,
        type="who_voted_out",
        options=living,
        round=state.round,
    )
    state.markets.append(market)
    return market


def freeze_open(state: GameState) -> None:
    """Freeze every market that is still open (called when discussion starts)."""
    for m in state.markets:
        if not m.resolved and not m.frozen:
            try:
                client.freeze_market(m.market_id)
            except Exception:
                pass
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
        try:
            client.resolve_market(m.market_id, m.options.index(out_name))
        except Exception:
            pass
        m.resolved = True
        m.winning_option = out_name


def resolve_game_winner(state: GameState, winner: str) -> None:
    m = next((m for m in state.markets if m.type == "game_winner"), None)
    if m and winner in m.options:
        try:
            client.resolve_market(m.market_id, m.options.index(winner))
        except Exception:
            pass
        m.resolved = True
        m.winning_option = winner


def refresh_pools(state: GameState) -> None:
    """Pull live pool sizes into each market (so /state shows odds)."""
    for m in state.markets:
        try:
            pools = client.get_pools(m.market_id)
        except Exception:
            pools = []
        if pools:
            m.pools = {opt: pools[i] for i, opt in enumerate(m.options)}
        else:
            m.pools = {opt: "0" for opt in m.options}
