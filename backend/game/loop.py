"""Game runner — drives the LangGraph orchestration.

Thin: it holds the shared GameState global (read by the FastAPI layer while a
game runs in a background thread), builds the graph, and invokes it. All flow
topology lives in `graph.py`, all phase work in `phases.py`, adjudication in
`rules`, narration in the injected `Narrator`.
"""
from . import graph as game_graph
from . import history
from .narrator import ConsoleNarrator, Narrator, SilentNarrator
from .state import GameState

STATE: GameState | None = None

# Headroom over the ~11 supersteps a 2-round game takes.
_RECURSION_LIMIT = 50


def run_game(state: GameState, nar: Narrator | None = None) -> GameState:
    global STATE
    STATE = state
    nar = nar or SilentNarrator()
    compiled = game_graph.build_graph(state, nar)
    compiled.invoke(
        {"round": 1, "decided": False},
        config={"recursion_limit": _RECURSION_LIMIT},
    )
    history.record(state)
    return state


if __name__ == "__main__":
    from .roster import new_game

    run_game(new_game(), ConsoleNarrator())
