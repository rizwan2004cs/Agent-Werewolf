# CLAUDE.md — Pack (Agent Werewolf)

> Master context. The `docs/` folder holds the original architectural spec, which was written for an
> on-chain (Monad) build. **That blockchain layer has been removed** — the notes below are the
> authoritative description of how this repo actually works now. Where the docs mention Monad,
> contracts, wallets, web3, or on-chain settlement, treat it as historical: it no longer applies.

## What we're building

**Pack**: 7 AI agents play Werewolf (social deduction). Humans watch and bet **play money** on the
outcome, or join the table as a hidden-role player. A spectator sport — agents are the players,
humans are the audience and bettors. No blockchain, no wallet: everything runs off-chain in memory
so it deploys to any free host (e.g. Render).

## Locked decisions

- **LLM:** provider auto-detect in `backend/game/config.py` (all OpenAI-compatible):
  `OPENAI_API_KEY` → OpenAI (`gpt-4o-mini`), else `GROQ_API_KEY` → Groq
  (`llama-3.3-70b-versatile`), else deterministic mock mode (offline, no cost).
- **No chain.** All Monad/contract/web3/wallet code has been removed. Betting is a self-contained,
  in-memory **parimutuel play-money simulation** in `backend/game/markets.py`.
- **Play money:** each browser gets a random `bettor id` (localStorage) and starts with 100 points.
  Bets are pooled per market/option; on resolve the pool is split among winners pro-rata and credited
  back. State is in-memory and resets on a new game / backend restart.
- **Folders:** `backend/`, `frontend/` (the old `contract/` and `shared/` dirs are gone).
- **Config:** a single root `.env` (gitignored), read by the backend via `game/config.py`. Only LLM +
  pacing settings remain (`OPENAI_API_KEY`, `OPENAI_MODEL`, `PACE`, `MAX_ROUNDS`).

## Tech stack

| Layer | Tool |
|-------|------|
| Backend | Python + FastAPI + (optional) OpenAI + LangGraph (`backend/`) |
| Betting | In-memory parimutuel simulation (play money) — `backend/game/markets.py` |
| Frontend | React + Vite (`frontend/`); DiceBear avatars |

## Repo structure

```
pack/
├── CLAUDE.md
├── docs/                # original spec (historical — describes the removed on-chain build)
├── backend/  game/{state,roster,agents,phases,markets,loop,...}.py · server.py · requirements.txt
├── frontend/ src/{scene/, betting/, play/, api.js, App.jsx, styles.css}
├── render.yaml          # Render Blueprint (backend web service + static frontend)
└── .env                 # single root config (gitignored)
```

## HTTP surface (backend)

- `POST /control/start?kind=betting|human` — start a game.
- `POST /control/say`, `POST /control/vote` — human-player inputs.
- `GET  /state?mode=god|bettor|player` — fog-aware game state (includes `markets` + `payouts`).
- `POST /bet` `{marketId, option, address, amount}` — place a play-money bet.
- `GET  /wallet?address=...` — current play-money balance for a bettor id.
- `GET  /history` — past completed games.

## Build principles

1. **Always runnable, fully offline.** No API key and no chain needed — `PACE=0` runs instantly.
2. **The discussion is the show.** Believable agents are the core value — prioritize prompts.
3. **Betting never breaks the game.** It's a side ledger over GameState; a bad bet just returns an error.
4. **Frontend must feel like a game** — village ring, speech clouds, day/night, pacing beats.

## Conventions

- **7 players**: 2 wolves, 1 seer, 4 villagers. Names drawn from `backend/game/characters.py`.
- Money: play-money "points", tracked as floats in `markets.py`, serialized as strings to clients.
- **Fog of war is server-side** — never send hidden roles/reasoning to a bettor-mode client.
- **Max 2 rounds** per game (hard cap).
