"""Pure game rules. No I/O, no LLM, no chain — just functions over GameState.

Kept separate so the win/elimination logic is trivially testable and the phase
orchestration stays about *sequencing*, not *adjudication*.
"""
from .state import GameState, Player


def decided_winner(state: GameState) -> str | None:
    """Return 'village' / 'wolves' if the game is over, else None."""
    alive_wolves = state.alive_wolves()
    alive_village = [p for p in state.alive_players() if p.role != "wolf"]
    if len(alive_wolves) == 0:
        return "village"
    if len(alive_wolves) >= len(alive_village):
        return "wolves"
    return None


def final_winner(state: GameState) -> str:
    """Winner to declare at game end (falls back to wolves if undecided)."""
    return decided_winner(state) or ("village" if not state.alive_wolves() else "wolves")


def tally(votes: list[dict], state: GameState) -> Player:
    """Most-voted living player. Ties broken by first to reach the max."""
    counts: dict[int, int] = {}
    for v in votes:
        target = state.by_name(v["target"])
        if target:
            counts[target.idx] = counts.get(target.idx, 0) + 1
    out_idx = max(counts, key=counts.get)
    return state.players[out_idx]


def eliminate(player: Player) -> None:
    """Kill a player and publicly reveal their role."""
    player.alive = False
    player.revealed_role = player.role
