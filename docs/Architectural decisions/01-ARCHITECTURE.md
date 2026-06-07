# 01 — Architecture

## The three layers

```
┌──────────────────────────────────────────────────────────┐
│  FRONTEND (React + Vite)                                   │
│  Village scene · character speech bubbles · betting panel  │
│  God mode / Bettor mode                                    │
│   • polls backend GET /state every 500ms                   │
│   • sends bets via MetaMask + ethers.js (placeBet)         │
└───────────────┬───────────────────────────┬───────────────┘
                │ HTTP (state, control)      │ ethers.js (bets only)
                ▼                            ▼
┌──────────────────────────────────┐  ┌────────────────────────┐
│  BACKEND (Python + FastAPI)       │  │  CONTRACT (Monad)       │
│  • runs the game loop             │  │  WerewolfArena.sol      │
│  • LLM calls per agent (Claude)   │  │  parimutuel betting:    │
│  • holds GameState                │──┤  openMarket / placeBet  │
│  • serves /state (fog of war)     │  │  resolveMarket / claim  │
│  • calls openMarket/resolveMarket │  │                         │
│    + reads pools (web3.py)        │  └────────────────────────┘
└───────────────────────────────────┘
```

## Data flow, one game

1. Backend assigns roles, creates the game state, calls `openMarket()` on the contract for "game winner".
2. Backend runs the loop: night → morning → discussion → voting, updating `GameState` in memory each step.
3. Frontend polls `GET /state` every 500ms and re-renders the scene (who's speaking, who died, current phase).
4. At phase boundaries the backend opens/freezes betting markets. Users place bets directly on the contract via MetaMask.
5. Backend reads pool sizes via web3.py and includes them in `/state` so the frontend shows live odds without touching the chain for reads.
6. When the game ends, backend calls `resolveMarket()`. Winners call `claimWinnings()` from their wallet.

## Key design decisions

- **Game logic is 100% off-chain (Python).** The chain only holds and splits betting money. This keeps the blockchain surface tiny.
- **Frontend reads through the backend, writes through MetaMask.** All chain *reads* (pools/odds) are proxied via `/state`. The only chain *writes* from the frontend are `placeBet` and `claimWinnings` (must come from the user's wallet).
- **Fog of war is server-side.** `GET /state?mode=bettor` strips hidden roles and private reasoning. `?mode=god` returns everything.
- **Polling, not websockets.** 500ms polling is simpler and reliable for the MVP.

## Tech stack rationale

- **Python backend** — best LLM SDK ergonomics; the orchestration is the heavy logic.
- **FastAPI** — minimal, fast to serve JSON state.
- **web3.py** — 2 contract calls + pool reads. That's all.
- **React + Vite** — fast scaffold; the UI is the differentiator.
- **ethers.js v6** — standard wallet/contract interaction for bets only.
- **Monad** — EVM-equivalent, so all standard Ethereum tooling works unchanged. Fast + cheap = per-bet transactions are viable.

## Running locally

- Contract: deployed once to Monad testnet (address goes in `backend/.env` and `frontend/.env`).
- Backend: `uvicorn server:app --reload --port 8000`
- Frontend: `npm run dev` (Vite, usually port 5173), proxies to backend at `http://localhost:8000`.
