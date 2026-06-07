# CLAUDE.md — Pack (Agent Werewolf on Monad)

> This is the master context file. Read this first, then the docs in `docs/` in numeric order.

## What we're building

**Pack** is a game where AI agents play Werewolf (social deduction) and humans bet on the outcome, settled on the Monad blockchain. It's a spectator sport: the agents are the players, the humans are the audience and bettors, and the chain is the neutral referee that holds and pays out the money.

This repo is the **MVP**. Build it end to end. Agent personalities will be tuned later — for now, get a full game running with a beautiful game-like UI and on-chain betting.

## The experience we're building toward

- A **village scene**: 7 character avatars arranged in a circle around a central prize pot.
- When an agent speaks, a **speech bubble (cloud) pops above their character** — like a video game.
- Day/night visual states: the scene darkens at night, brightens for day discussion.
- Dead characters are visibly eliminated (greyed out / tombstone).
- A **betting panel** prompts the user to place bets at the right moments, shows live odds, and locks during discussion.
- Two view modes: **God mode** (see everything, for spectators) and **Bettor mode** (fog of war, for players with money down).

It must feel like a polished game, not a dashboard.

## Tech stack

| Layer | Tool |
|-------|------|
| Blockchain | Monad testnet (Chain ID 10143, EVM-compatible) |
| Smart contract | Solidity ^0.8.20 — ONE betting contract, deployed via Remix |
| Backend / AI orchestration | Python + FastAPI + Anthropic SDK + web3.py |
| LLM | Claude (`claude-haiku-4-5-20251001`) — fast and cheap for many agent calls |
| Frontend | React + Vite + plain CSS, ethers.js v6 for wallet/betting |

## Docs index (read in order)

| Doc | Purpose |
|-----|---------|
| `docs/00-GAME-DESIGN.md` | Rules, roles, 7 players, phases, win conditions, game theory |
| `docs/01-ARCHITECTURE.md` | System design, data flow, how the 3 layers connect |
| `docs/02-INTERFACES.md` | **The glue** — game state JSON, contract ABI, HTTP API. Do not deviate. |
| `docs/03-CONTRACT.md` | The single betting contract + Monad deploy via Remix |
| `docs/04-BACKEND.md` | Orchestrator: game loop, agents, prompts, LLM calls, FastAPI server |
| `docs/05-FRONTEND.md` | The character/village UI, speech bubbles, betting panel, animations |
| `docs/06-BUILD-ORDER.md` | The exact sequence to build in, with milestones |

## Repo structure

```
pack/
├── CLAUDE.md
├── docs/                  # these files
├── contract/
│   └── WerewolfArena.sol  # the one contract
├── backend/
│   ├── game/
│   │   ├── state.py       # data model
│   │   ├── agents.py      # LLM agent wrappers
│   │   ├── prompts.py     # all prompt templates
│   │   ├── loop.py        # the game loop
│   │   └── chain.py       # web3.py calls to the contract
│   ├── server.py          # FastAPI — serves /state, /control
│   ├── requirements.txt
│   └── .env               # API keys (user provides)
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   ├── wallet.js      # ethers.js + MetaMask for bets
    │   ├── scene/         # VillageScene, Character, SpeechBubble
    │   ├── betting/       # BettingPanel
    │   └── styles.css
    └── package.json
```

## Build principles

1. **Backend first, runnable off-chain.** Get a full game printing to console before adding chain or UI.
2. **The discussion is the show.** Agents talking believably is the core value — prioritize it.
3. **Chain is minimal.** One contract, ~4 functions, only handles betting money. Game logic is all Python.
4. **Always keep it runnable.** Build incrementally per `06-BUILD-ORDER.md`; never leave it broken.
5. **Frontend must feel like a game** — characters, speech clouds, pacing beats, not a data table.

## Conventions

- Player count: **7** (2 wolves, 1 seer, 4 villagers for MVP). Agent names: Luna, Caspian, Mira, Theron, Dax, Vera, Orin.
- Money amounts: strings in the JSON (avoid float drift), wei/MON in the contract.
- Fog of war is enforced **server-side** — never send hidden roles to a bettor-mode client.
- Max 2 rounds per game (hard cap).
- Env vars and config: the user will provide API keys and ask Claude for config help while building. Read `.env` for `ANTHROPIC_API_KEY`, contract address, RPC.
