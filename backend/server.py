"""FastAPI HTTP layer — routes only.

Thin by design: it starts a game in a background thread and serializes state.
All game logic lives in the `game` package. Run:
    uvicorn server:app --reload --port 8000
"""
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from game import history, human, livestate, loop, markets, serialize
from game.roster import new_game


class SayIn(BaseModel):
    text: str


class VoteIn(BaseModel):
    target: str


class BetIn(BaseModel):
    marketId: int
    option: str
    address: str
    amount: float = 5.0

app = FastAPI(title="Pack — Agent Werewolf")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_lock = threading.Lock()
# Monotonic game-id counter. Seeded from history on first use, then incremented
# in-process so back-to-back games never collide (history is written only at
# game end, so reading the file per-start could reuse an id).
_next_id: int | None = None


@app.on_event("startup")
def _restore_live_game():
    """On boot, restore the last live game from disk. If it wasn't finished,
    resume it from the next phase so a backend restart doesn't lose the match."""
    snap = livestate.load()
    if snap is None:
        return
    loop.STATE = snap
    if snap.phase != "ended":
        print(f"[startup] resuming game {snap.game_id} from phase '{snap.phase}'")
        threading.Thread(target=loop.resume_game, args=(snap,), daemon=True).start()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/control/start")
def start(kind: str = "betting"):
    """kind='betting' (7 agents, humans bet) or 'human' (1 human + 6 agents)."""
    global _next_id
    kind = kind if kind in ("betting", "human") else "betting"
    with _lock:
        running = loop.STATE is not None and loop.STATE.phase not in ("ended", "idle")
        if running:
            return {"ok": False, "reason": "game in progress", "gameId": loop.STATE.game_id}
        if _next_id is None:
            _next_id = history.next_game_id()
        gid = _next_id
        _next_id += 1
        markets.reset()  # fresh play-money pools/balances for the new game
        state = new_game(gid, kind=kind)
        threading.Thread(target=loop.run_game, args=(state,), daemon=True).start()
    return {"ok": True, "gameId": state.game_id, "kind": kind}


@app.post("/control/say")
def control_say(body: SayIn):
    """Human player submits their discussion line (unblocks the game loop)."""
    human.submit(body.text)
    return {"ok": True}


@app.post("/control/vote")
def control_vote(body: VoteIn):
    """Human player submits their vote target (unblocks the game loop)."""
    human.submit(body.target)
    return {"ok": True}


@app.post("/bet")
def place_bet(body: BetIn):
    """Place a play-money bet on a live market (no chain, no wallet)."""
    state = loop.STATE
    if state is None:
        return {"ok": False, "error": "no game in progress"}
    return markets.place_bet(
        state, body.marketId, body.option, body.address, body.amount
    )


@app.get("/wallet")
def get_wallet(address: str):
    """Current play-money balance for a bettor id (seeded on first sight)."""
    return {"address": address, "balance": markets.balance(address)}


@app.get("/state")
def get_state(mode: str = "bettor"):
    state = loop.STATE
    if state is None:
        return {"phase": "idle"}
    mode = mode if mode in ("god", "bettor", "player") else "bettor"
    return serialize.to_client(state, mode)


@app.get("/history")
def get_history():
    """Past completed games, newest first."""
    return list(reversed(history.load()))
