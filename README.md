# Pack — Agent Werewolf on Monad

> AI agents play social deduction; humans bet on the outcome; the chain referees.
> Monad Blitz V4.

Three layers:

- **Agents** — LLM players with asymmetric info, play to win their role, unaware betting exists.
- **Bettors** — humans in fog-of-war mode betting real MON between phases.
- **Audience** — god-mode spectators who see everything (roles + private reasoning).

The chain guarantees fairness: roles committed as hashes before the game, votes immutable, payouts automatic.

**Built for Monad Blitz Bangalore V4 — "The Agent Economy".** Master context: [CLAUDE.md](CLAUDE.md) ·
authoritative spec: [docs/Architectural decisions/](docs/Architectural%20decisions/) (read `00`–`06`).

## Repo layout

```
pack/
├── CLAUDE.md        # master context — read first
├── docs/            # design docs; docs/Architectural decisions/ is the authoritative spec
├── contract/        # Hardhat — AgentWerewolf.sol (game) + WerewolfArena.sol (betting)
├── backend/         # Python — game loop, LLM agents, FastAPI /state, chain calls
├── frontend/        # React + Vite — village scene, god/bettor modes, betting UI
└── shared/abi/      # contract ABIs exported after compile (backend & frontend import these)
```

## Quick start

```bash
# 1. Contracts
cd contract && npm install && npx hardhat compile

# 2. Backend
cd backend
python -m venv venv
venv\Scripts\activate           # Windows  (source venv/bin/activate on *nix)
pip install -r requirements.txt
uvicorn server:app --reload     # serves http://localhost:8000

# 3. Frontend
cd frontend && npm install && npm run dev
```

See [docs/Architectural decisions/06-BUILD-ORDER.md](docs/Architectural%20decisions/06-BUILD-ORDER.md)
for the build sequence and [02-INTERFACES.md](docs/Architectural%20decisions/02-INTERFACES.md) for the
frozen state/ABI/HTTP contracts.

## Status

All config lives in a single **root `.env`** (copy from [.env.example](.env.example)) — read by both the
orchestrator and Hardhat. Chain calls run in **mock mode** by default (`MOCK_CHAIN=1`) so the full game
runs locally without a funded wallet. Set `OPENAI_API_KEY` for real agents; set `MOCK_CHAIN=0` +
`PRIVATE_KEY` to deploy and run against a live Monad network.
