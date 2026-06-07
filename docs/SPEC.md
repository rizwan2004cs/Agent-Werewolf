# Pack — Product & Technical Spec (north-star)

> **One line:** AI agents play social deduction with asymmetric info; humans bet real MON under
> fog-of-war; the chain referees. A live, dramatic-irony spectator economy.
>
> Built for **Monad Blitz Bangalore V4 — "The Agent Economy"** (7 June). This is the single
> source of truth. Engineering split lives in `workstream-{A,B,C}.md`; interfaces in `INTERFACES.md`.

---

## 1. Why this wins (the novelty hook)

Judging is **50% peer developers + 50% jury**, scored on the **innovation lens** (novelty, clever
mechanics, problem-solving) — *not* polish. The demo is **3 minutes, live**. So we lead with what is
genuinely new and watchable:

**Three audiences, one game, asymmetric information as the product:**

| Layer | Sees | Feels | The novelty |
|-------|------|-------|-------------|
| **Agents** (athletes) | only their role's info | play to win, unaware betting exists | LLMs doing *deception*, not Q&A |
| **Bettors** (humans) | public info only — fog of war | risk + deduction, real MON | betting on autonomous agents mid-game |
| **Audience** (god mode) | everything incl. wolves + private thoughts | dramatic irony | watch the village get fooled in real time |

The "wow": on the projector, you read **"Caspian (WOLF) thinking: pin it on Mira"** one second
before Caspian says something innocent out loud — while a human on their phone bets, blind, on the
outcome. The chain guarantees nobody cheated: roles committed as hashes pre-game, votes immutable,
payouts automatic. **That triad — autonomous deceptive agents + fog-of-war human market + on-chain
referee — is the idea no one else will have.**

This is exactly on-theme for "The Agent Economy": agents are the economic actors; humans speculate on
their behaviour; settlement is on Monad.

## 2. System architecture

```
  FRONTEND (Vercel)            ORCHESTRATOR (local/tunnel)        CONTRACTS (Monad testnet)
  god | bettor modes    poll   game loop + LLM agents     web3   AgentWerewolf.sol
  live feed + betting  ─────►  state + fog-of-war server ─────►  WerewolfBetting.sol
  replay player               /state /markets /control          roles·votes·kill·win | parimutuel
```

- **Contracts** — `AgentWerewolf` (roles as hash commitments, votes, night kill, win, prize) +
  `WerewolfBetting` (parimutuel pools, no bookmaker — odds emerge from stakes). Hardhat, Solidity 0.8.20.
- **Orchestrator** — Python. Runs the game loop, calls one LLM per agent per turn, holds state, bridges
  to chain. Serves `/state?mode=god|bettor` with **server-side fog-of-war** (never leaks hidden roles
  to a bettor client). Mock fallbacks for both LLM and chain so it runs offline.
- **Frontend** — React + Vite. Two modes + a **replay player**. Polls `/state` every 500 ms.

Repo is a **monorepo**: `contracts/ · orchestrator/ · frontend/ · shared/abi/ · docs/`.

## 3. Hackathon compliance (hard requirements → our plan)

| Requirement (Notion) | Our compliance |
|---|---|
| Deployed & operational on **Monad Testnet** | Deploy both contracts; addresses in `shared/deployed.json`; verify via API |
| App **hosted on web** (Vercel/etc.) | Frontend → Vercel. Orchestrator runs locally behind a tunnel for the live demo (it's a stateful loop; serverless can't host it) |
| Submit a **fork** of `monad-developers/monad-blitz-bangalore` | At submission: clone the fork, drop this monorepo in, push. Repo URL + demo URL → `blitz.devnads.com` |
| Public repo + README | Root `README.md` kept demo-ready |
| **3-min live demo**, innovation-first | God mode on projector + bettor mode on phone; **replay mode** as gremlin-proof backup |
| Fresh idea, built at event | New project, conceived for this Blitz |

**Deadlines (7 June):** code freeze **5:15 PM** · submit **5:30 PM** · demos **6:45 PM** (3 min).

## 4. The demo (what we actually show in 3 minutes)

1. **0:00** — god mode on screen, 5 agents. Hit Start. "AI agents are about to play Werewolf. They
   don't know humans are betting on them."
2. **0:20** — night falls, wolf kills, private-reasoning panel reveals the wolves' plan. Dramatic irony.
3. **1:00** — discussion streams; wolves deflect, villagers accuse. Flip to phone: a human bets under
   fog of war; odds shift live; betting **freezes** during discussion.
4. **2:00** — vote tally fills, elimination card flips to reveal a role — on-chain tx.
5. **2:40** — game ends, all cards flip, winner declared, **prize + payout tx links to the explorer**.
   "Every role, vote, and payout was on Monad. Nobody could cheat."

**Backup:** if live agents stall or the network hiccups, switch to **replay** of a pre-recorded great
game — identical UI, deterministic, fits the time slot.

## 5. Acceptance criteria (definition of "demo-ready")

- [ ] Contracts deployed to Monad testnet; addresses + explorer links live
- [ ] One full game runs with **real LLM agents** that are believable (wolves deceive, villagers reason)
- [ ] `/state?mode=bettor` never leaks hidden roles or private reasoning (verified)
- [ ] Betting: pools update, odds shift, **freeze during discussion**, payout claim works on-chain
- [ ] Frontend hosted on Vercel, pointed at the (tunneled) orchestrator
- [ ] **Replay mode** plays a recorded game start-to-finish with no backend
- [ ] 3-minute demo rehearsed; screenshots + screen-recording captured as fallback

## 6. Game logic — PROVISIONAL (⚠ detailed rules incoming from product owner)

> The user is providing detailed game logic later. **Do not treat the below as final** — these are
> working defaults that keep a game runnable today. Revisit when the real rules land.

Current working defaults (in `orchestrator/game/loop.py`):
- **5 players**, roster `ROSTER`: 1 wolf, 1 seer, 3 villagers (balanced for a 2-round demo).
  *Provisional* — spec may call for a 2-wolf "pack" with more seats.
- **Phases:** setup → (night → morning → discussion ×2 → vote → resolution) ×maxRounds → ended.
- **Win:** village if wolves = 0; wolves if wolves ≥ villagers (parity). *Provisional.*
- **Night:** wolf picks a victim; seer inspects one player (private). **Max 2 rounds** hard cap.
- **Roles** committed as `keccak256(role, idx, salt)` pre-game; revealed on elimination / at end.

**Open questions for the detailed rules** (fill when provided): number of wolves & total players ·
seer/doctor/other special roles · tie-break on votes · exact win conditions · how many discussion
rounds · whether agents get memory across games · betting market set & resolution timing.

## 7. Non-negotiables (carried from README)

- Discussion engine with **real agents** is the demo — build/tune it before polish.
- Betting **freezes** during discussion; windows open only at phase boundaries.
- **Replay/recording ready before deploy** — it's both the backup and the latency hedge.
- Fog-of-war enforced **server-side**, never client-side.
