# Pack — Agent Werewolf on Monad

> AI agents play social deduction; humans bet on the outcome; the chain referees.
> Monad Blitz V4.

Three layers:

- **Agents** — LLM players with asymmetric info, play to win their role, unaware betting exists.
- **Bettors** — humans in fog-of-war mode betting real MON between phases.
- **Audience** — god-mode spectators who see everything (roles + private reasoning).

The chain guarantees fairness: roles committed as hashes before the game, votes immutable, payouts automatic.

## Repo layout

```
pack/
├── docs/            # design + workstream docs (start with docs/SETUP.md)
├── contracts/       # Hardhat — AgentWerewolf.sol + WerewolfBetting.sol (Monad testnet)
├── orchestrator/    # Python — game loop, LLM agents, FastAPI /state, chain calls
├── frontend/        # React + Vite — god mode / bettor mode + betting UI
└── shared/abi/      # contract ABIs exported after compile (B & C import these)
```

## Quick start

```bash
# 1. Contracts
cd contracts && npm install && npx hardhat compile

# 2. Orchestrator
cd orchestrator
python -m venv venv
venv\Scripts\activate           # Windows  (source venv/bin/activate on *nix)
pip install -r requirements.txt
uvicorn server:app --reload     # serves http://localhost:8000

# 3. Frontend
cd frontend && npm install && npm run dev
```

See [docs/SETUP.md](docs/SETUP.md) for full environment config, Monad testnet details, and the
"definition of setup done" checklist. See [docs/INTERFACES.md](docs/INTERFACES.md) for the frozen
contracts between the three components.

## Status

Chain calls run in **mock mode** by default (`MOCK_CHAIN=1`) so the full game runs locally without a
funded wallet. Set `MOCK_CHAIN=0` and fill `orchestrator/.env` to deploy + run against Monad testnet.
