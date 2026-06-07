# CLAUDE.md — Pack (Agent Werewolf on Monad)

> Master context. Read this first, then `docs/Architectural decisions/` in numeric order (`00`–`06`).
> That folder is the **authoritative spec**; where this file differs, the differences below are the
> deliberate, user-approved decisions for this build and win.

## What we're building

**Pack**: 7 AI agents play Werewolf (social deduction); humans bet on the outcome; Monad settles the
money and records the votes. A spectator sport — agents are the players, humans are the audience and
bettors, the chain is the neutral referee. This repo is the MVP: a full game in a polished village-scene
UI with on-chain votes + betting.

Built for **Monad Blitz Bangalore V4 — "The Agent Economy"** (7 June). Judged 50% peer devs + 50% jury
on an **innovation lens**; the **3-minute live demo** is the core.

## Locked decisions (override the docs' defaults)

- **LLM:** OpenAI (`gpt-4o-mini`) via provider auto-detect in `backend/game/agents.py`
  (Anthropic also supported; neither key → deterministic mock). Docs said Claude.
- **Network:** contract.dev **stagenet, chainId 143** (RPC in root `.env`, funded ~11k MON).
  Docs said public testnet 10143 — kept as a fallback (`monadTestnet` Hardhat network).
  ⚠ Private RPC: public explorers can't see it; may need a public-testnet deploy for the demo's verify beat.
- **On-chain scope:** votes **and** betting on-chain. Two operator-driven contracts (not the docs'
  single betting-only contract): `AgentWerewolf.sol` (immutable roles/kills/votes/winner) +
  `WerewolfArena.sol` (parimutuel betting). One funded operator key writes all chain state.
- **Folders:** `contract/`, `backend/`, `frontend/` (renamed from contracts/orchestrator).
- **Config:** a single **root `.env`** (gitignored), read by both backend (`game/__init__.py`) and
  Hardhat (`hardhat.config.js`). `MOCK_CHAIN=1` + no LLM key → whole game runs offline.

## Tech stack

| Layer | Tool |
|-------|------|
| Chain | Monad via contract.dev stagenet (chainId 143); EVM-equivalent |
| Contracts | Solidity ^0.8.20, Hardhat (`contract/`) — operator-driven |
| Backend | Python + FastAPI + OpenAI SDK + web3.py (`backend/`) |
| Frontend | React + Vite + ethers v6 (`frontend/`); DiceBear avatars |

## Repo structure

```
pack/
├── CLAUDE.md
├── docs/Architectural decisions/   # authoritative spec (00–06)
├── contract/   contracts/{AgentWerewolf,WerewolfArena}.sol · scripts/ · test/ · hardhat.config.js
├── backend/    game/{state,prompts,agents,chain,loop}.py · server.py · requirements.txt
├── frontend/   src/{scene/, betting/, wallet.js, api.js, App.jsx, styles.css, abi.json}
├── shared/abi/ # ABI source of truth (copied into backend/ + frontend/src/)
└── .env        # single root config (gitignored)
```

## Build principles

1. **Backend first, runnable off-chain.** Full game to console before chain or UI.
2. **The discussion is the show.** Believable agents are the core value — prioritize prompts.
3. **Chain is minimal + resilient.** Operator-driven; every chain call wrapped in try/except so a
   failed tx never crashes the game loop.
4. **Always runnable.** Build per `docs/Architectural decisions/06-BUILD-ORDER.md`; never leave broken.
5. **Frontend must feel like a game** — village ring, character speech clouds, day/night, pacing beats.

## Conventions

- **7 players**: 2 wolves, 1 seer, 4 villagers. Names: Luna, Caspian, Mira, Theron, Dax, Vera, Orin.
- Money: strings in JSON (avoid float drift); wei/MON on-chain.
- **Fog of war is server-side** — never send hidden roles/reasoning to a bettor-mode client.
- **Max 2 rounds** per game (hard cap).
- State/ABI/HTTP shapes are frozen in `02-INTERFACES.md` — build against them.
