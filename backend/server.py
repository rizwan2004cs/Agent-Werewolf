"""FastAPI server. Serves the live GameState to the frontend with server-side
fog-of-war (never sends hidden roles or private reasoning to a bettor-mode client).

Run:  uvicorn server:app --reload   (from the orchestrator/ folder)
"""
from __future__ import annotations

import copy
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from game.state import serialize, GameState
from game import loop

app = FastAPI(title="Pack Orchestrator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE: GameState | None = None
_lock = threading.Lock()
_thread: threading.Thread | None = None


@app.get("/")
def root():
    return {"ok": True, "service": "pack-orchestrator", "running": _is_running()}


@app.get("/state")
def get_state(mode: str = "bettor"):
    if STATE is None:
        return {"phase": "idle", "players": [], "markets": [], "discussionLog": []}
    s = copy.deepcopy(serialize(STATE))
    if mode != "god":
        # FOG OF WAR — strip hidden roles + private reasoning for bettors.
        for p in s["players"]:
            if not p.get("revealedRole"):
                p["role"] = None
        s.pop("privateReasoning", None)
    return s


@app.get("/markets")
def get_markets(gameId: int | None = None):
    if STATE is None:
        return {"markets": []}
    markets = [m.to_json() for m in STATE.markets if gameId is None or m.game_id == gameId]
    return {"markets": markets}


@app.post("/control/start")
def start():
    global STATE, _thread
    with _lock:
        if _is_running():
            return {"ok": False, "error": "game already running"}
        STATE = loop.new_state()
        _thread = threading.Thread(target=_run, args=(STATE,), daemon=True)
        _thread.start()
    return {"ok": True}


def _run(state: GameState):
    try:
        loop.run_game(state)
    except Exception as e:  # keep the server alive if a game crashes
        import traceback

        traceback.print_exc()
        print(f"[server] game thread error: {e}")


def _is_running() -> bool:
    return _thread is not None and _thread.is_alive()
