# SETUP — Environment & Repo

> Read first. This unblocks everyone. Whoever is setting up: do all of this, then push the skeleton so A/B/C can pull and start.

## Monad Testnet config (verified)

| Field | Value |
|-------|-------|
| Network name | Monad Testnet |
| RPC URL | `https://testnet-rpc.monad.xyz` |
| Chain ID | `10143` |
| Currency symbol | `MON` |
| Block explorer | `https://testnet.monadvision.com` |
| Faucet | Official Monad faucet (link in Monad docs / Discord `#dev`) |

> Monad is fully EVM-compatible — Hardhat, Foundry, ethers.js, web3.py all work unchanged. ~1s blocks, ~10k TPS, near-zero gas. Grab MON from the faucet first; you need it to deploy.
> Double-check the faucet and explorer URLs on `docs.monad.xyz` in case they've rotated — RPC and chain ID are stable.

## Repo structure

```
pack/
├── README.md
├── docs/                       # these md files
├── contracts/                  # Person A — Hardhat
│   ├── contracts/
│   │   ├── AgentWerewolf.sol
│   │   └── WerewolfBetting.sol
│   ├── scripts/deploy.js
│   ├── hardhat.config.js
│   ├── .env.example
│   └── package.json
├── orchestrator/               # Person B — Python
│   ├── game/
│   │   ├── __init__.py
│   │   ├── loop.py             # main game loop
│   │   ├── agents.py           # LLM agent wrappers
│   │   ├── prompts.py          # all prompt templates
│   │   ├── chain.py            # web3 contract calls
│   │   └── state.py            # game state model
│   ├── server.py               # FastAPI — serves /state to frontend
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # Person C — React + Vite
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js              # polls orchestrator
│   │   ├── modes/
│   │   │   ├── GodMode.jsx
│   │   │   └── BettorMode.jsx
│   │   └── components/
│   │       ├── PlayerCard.jsx
│   │       ├── DiscussionFeed.jsx
│   │       └── BettingPanel.jsx
│   └── package.json
└── shared/
    └── abi/                    # contract ABIs (A exports here, B & C import)
```

## One-time setup commands

**Contracts (Person A):**
```bash
mkdir -p contracts && cd contracts
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox dotenv
npx hardhat init        # choose "JavaScript project"
```

**Orchestrator (Person B):**
```bash
mkdir -p orchestrator && cd orchestrator
python -m venv venv && source venv/bin/activate
pip install anthropic web3 fastapi uvicorn python-dotenv
pip freeze > requirements.txt
```

**Frontend (Person C):**
```bash
npm create vite@latest frontend -- --template react
cd frontend && npm install
```

## hardhat.config.js (Monad)

```javascript
require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: "0.8.20",
  networks: {
    monadTestnet: {
      url: "https://testnet-rpc.monad.xyz",
      chainId: 10143,
      accounts: [process.env.PRIVATE_KEY],
    },
  },
};
```

## Environment variables

**contracts/.env**
```
PRIVATE_KEY=0x...        # deployer wallet, funded from faucet
```

**orchestrator/.env**
```
ANTHROPIC_API_KEY=sk-ant-...
RPC_URL=https://testnet-rpc.monad.xyz
CHAIN_ID=10143
GAME_CONTRACT=0x...      # filled after A deploys
BETTING_CONTRACT=0x...   # filled after A deploys
ORCHESTRATOR_KEY=0x...   # wallet that calls contract on agents' behalf
```

**frontend/.env**
```
VITE_ORCHESTRATOR_URL=http://localhost:8000
VITE_EXPLORER_URL=https://testnet.monadvision.com
```

## Wallets you'll need

- **1 deployer wallet** (Person A) — deploys both contracts. Fund from faucet.
- **5 agent wallets** (Person B) — one per agent, so votes come from distinct addresses on-chain. Generate them in code, fund each with a little MON from the faucet. For demo simplicity, the orchestrator can hold all 5 keys and sign on each agent's behalf.
- **Bettor wallets** — the audience connects their own (MetaMask on Monad testnet). For the demo you can pre-fund 2-3 test wallets.

## Definition of "setup done"

- [ ] Repo skeleton pushed with all three folders
- [ ] `hardhat.config.js` points at Monad, deployer wallet funded
- [ ] `npx hardhat compile` runs clean on an empty contract
- [ ] Orchestrator venv installs, `import anthropic, web3` works
- [ ] Frontend `npm run dev` shows the Vite default page
- [ ] `shared/abi/` exists and is gitignored-friendly (A writes ABIs there post-compile)
