# Pack — Development Docs

> Agent Werewolf on Monad. AI agents play social deduction; humans bet on the outcome; the chain referees.
> Monad Blitz V4. Build window: 6 hours. Team of 3.

## What this folder is

Engineering docs, split by workstream so all three of us can work in parallel without stepping on each other. Game design lives separately in `agent-werewolf-spec.md` (the north-star doc). These files are *how we build it*.

## Read order

1. **`SETUP.md`** — read first. Repo structure, dependencies, Monad testnet config. Whoever is setting up starts here.
2. **`INTERFACES.md`** — the contracts between our three components. Read before writing any integration code. This is what stops us from melting down at Hour 4.
3. Your workstream file:
   - **`workstream-A-contracts.md`** — Solidity + Monad deploy
   - **`workstream-B-orchestrator.md`** — Python game loop + agents + chain calls
   - **`workstream-C-frontend.md`** — React, two view modes, betting UI

## The system in one picture

```
        ┌─────────────────────────────────────────────┐
        │           FRONTEND (Person C)                │
        │  God mode (sees all) | Bettor mode (fog)     │
        │  polls /state, renders game + betting UI      │
        └───────────────┬─────────────────────────────┘
                        │ HTTP (poll /state)
        ┌───────────────▼─────────────────────────────┐
        │        ORCHESTRATOR (Person B)               │
        │  Runs game loop, calls LLM per agent,        │
        │  manages state, talks to chain               │
        └───────────────┬─────────────────────────────┘
                        │ web3 (ethers/web3.py)
        ┌───────────────▼─────────────────────────────┐
        │     SMART CONTRACTS (Person A) — Monad        │
        │  AgentWerewolf.sol  | WerewolfBetting.sol     │
        │  roles, votes, kill, win | parimutuel pools   │
        └───────────────────────────────────────────────┘
```

## Three layers, three audiences (the product model)

- **Agents** = the athletes. Asymmetric info. Play to win their role. Unaware betting exists.
- **Bettors** = humans in fog-of-war mode. See only public info. Bet under uncertainty between phases.
- **Audience** = god-mode spectators. See everything including who the wolves are. Watch for dramatic irony.

The chain guarantees nobody cheated: roles are committed as hashes before the game, votes are immutable, payouts are automatic.

## Team ownership

| Person | Owns | File |
|--------|------|------|
| A | Contracts + deploy | `workstream-A-contracts.md` |
| B | Orchestrator + agents | `workstream-B-orchestrator.md` |
| C | Frontend + betting UI | `workstream-C-frontend.md` |

## Non-negotiables

- **Discussion engine is the demo.** Build it before polish.
- **Betting freezes during discussion.** Windows open only at phase boundaries.
- **Max 2 rounds.** Hard cap to avoid runaway games.
- **Backup recording by Hour 5.** If live fails, replay.
- If contract work slips: run night off-chain, keep votes + payout + betting on-chain.
