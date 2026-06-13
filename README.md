# Pack — Agent Werewolf

7 AI agents play Werewolf (social deduction). Humans watch and bet **play money**
on the outcome, or join the table as a hidden-role player. No blockchain, no
wallet — everything runs off-chain in memory so it deploys to any free host.

## Game modes

- **Betting Arena (spectator/bettor)**: watch 7 AI agents discuss, vote, and
  resolve. Each browser gets a starting balance of play-money points and can bet
  on live markets ("who wins?", "who gets voted out?"). Winners split the pool
  pro-rata (parimutuel) and the winnings are credited back automatically.
- **Play Yourself (human + agents)**: join as a player with a secret role and
  play through discussion + voting.
- **God mode / bettor mode**: toggle between full visibility and fog-of-war.

> Note: with a real `OPENAI_API_KEY`, agent turns can take a moment while the
> model generates decisions. Without a key the game runs instantly in mock mode.

## How the betting works (no chain)

- Each browser gets a random `bettor id` (stored in `localStorage`) and starts
  with 100 play-money points.
- Bets are pooled per market/option on the backend (`backend/game/markets.py`).
- When a market resolves, the whole pool is split among the winners in
  proportion to their stake, and credited back to their balance.
- It's all in-memory: a fresh game (or backend restart) resets balances.

## Stack

- Frontend: React + Vite
- Backend: FastAPI + (optional) OpenAI + LangGraph
- Betting: in-memory parimutuel simulation (play money)

## Quick start (local)

```bash
# backend (runs in mock mode with no API key)
cd backend
python -m pip install -r requirements.txt
python -m uvicorn server:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```

Then open the Vite dev URL. To use real agents, put `OPENAI_API_KEY=...` in a
root `.env` (see `.env.example`).

## Deploy (Render free tier)

This repo ships a `render.yaml` Blueprint that deploys two services:

1. `pack-backend` (Python web service) — set `OPENAI_API_KEY` in the dashboard
   (or leave it unset to run mock agents).
2. `pack-frontend` (static site) — set `VITE_BACKEND_URL` to the deployed
   backend URL.

In Render: **New → Blueprint → point at this repo**, then fill in the secrets.

> Free-plan caveat: the backend sleeps after ~15 min idle and resets in-memory
> game state + balances on wake. Fine for demos; use a paid plan to keep it warm.
