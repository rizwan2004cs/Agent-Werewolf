"""FastAPI server. Serves the live game to the frontend in the 02-INTERFACES
shape, with server-side fog-of-war: a bettor-mode client never receives hidden
roles or private reasoning.

Run:  uvicorn server:app --reload --port 8000   (from backend/)
"""
from __future__ import annotations

import time
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from game import loop, chain

app = FastAPI(title="Pack Orchestrator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_lock = threading.Lock()
_thread: threading.Thread | None = None
_last_pool_refresh = 0.0


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def root():
    return {"ok": True, "service": "pack-orchestrator", "running": _is_running()}


@app.post("/control/start")
def start():
    global _thread
    with _lock:
        if _is_running():
            return {"ok": False, "error": "game already running"}
        state = loop.new_state()
        _thread = threading.Thread(target=_run, args=(state,), daemon=True)
        _thread.start()
    return {"ok": True, "gameId": state.game_id}


@app.get("/state")
def get_state(mode: str = "bettor"):
    s = loop.STATE
    if s is None:
        return {"phase": "idle", "players": [], "markets": [], "discussionLog": []}
    # When betting is open on a live chain, refresh pools (throttled) so a bet
    # just placed via MetaMask shows up in the odds within ~2s.
    global _last_pool_refresh
    if not chain.MOCK_CHAIN and s.betting_open:
        now = time.time()
        if now - _last_pool_refresh > 2.0:
            _last_pool_refresh = now
            try:
                loop._refresh_pools(s)
            except Exception:
                pass
    return serialize(s, mode)


def serialize(s, mode: str) -> dict:
    god = mode == "god"
    players = []
    for p in s.players:
        revealed = p.revealed_role
        # Fog of war: hide role unless god mode OR it's been publicly revealed.
        role = p.role if (god or revealed) else None
        players.append({
            "idx": p.idx,
            "name": p.name,
            "avatarSeed": p.name,
            "alive": p.alive,
            "role": role,
            "revealedRole": revealed,
            "currentSpeech": p.current_speech,
        })
    out = {
        "gameId": s.game_id,
        "phase": s.phase,
        "round": s.round,
        "maxRounds": s.max_rounds,
        "pot": s.pot,
        "speakingIdx": s.speaking_idx,
        "players": players,
        "nightResult": s.night_result,
        "discussionLog": s.discussion_log,
        "votes": s.votes,
        "bettingOpen": s.betting_open,
        "markets": [m.to_json() for m in s.markets],
        "winner": s.winner,
    }
    if god:
        out["privateReasoning"] = s.private_reasoning
    return out


def _run(state):
    try:
        loop.run_game(state)
    except Exception as e:  # keep the server alive if a game crashes
        import traceback

        traceback.print_exc()
        print(f"[server] game thread error: {e}")


def _is_running() -> bool:
    return _thread is not None and _thread.is_alive()
