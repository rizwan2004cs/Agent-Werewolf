# 00 — Game Design

## Concept

7 AI agents play Werewolf. Humans watch and bet. The chain settles the money. The agents don't know betting exists — they just play to win their role.

## Players: 7 total (MVP)

| Role | Count | Knows | Goal | Night action |
|------|-------|-------|------|--------------|
| Werewolf | 2 | Each other + all roles | Equal/outnumber villagers | Kill one non-wolf |
| Seer | 1 | Own role | Eliminate all wolves | Investigate one player |
| Villager | 4 | Own role only | Eliminate all wolves | None |

Names: **Luna, Caspian, Mira, Theron, Dax, Vera, Orin.**

> Phase-2 role (not in MVP): **Doctor** — protects one player from the night kill. Add later as a balance lever.

7 players with 2 wolves gives a balanced ~2-round game — enough discussion to be watchable and bettable, short enough to resolve cleanly.

## Win conditions

- **Villagers win** when both werewolves are eliminated.
- **Werewolves win** when wolves equal or outnumber remaining villagers.

Checked after every vote resolution.

## Phases (one round)

```
SETUP → NIGHT → MORNING → DISCUSSION → VOTING → WIN CHECK → (loop to NIGHT, or END)
```

| Phase | What happens | Betting |
|-------|--------------|---------|
| **Setup** | Roles assigned randomly. Pot/markets created. | Open: game winner |
| **Night** | Wolves pick a victim (LLM). Seer investigates one player (LLM). | Open |
| **Morning** | Victim revealed and eliminated. Seer learns their result privately. | Open: who's voted out |
| **Discussion** | 2 sub-rounds. Each living agent speaks once per sub-round with full context. Wolves lie, villagers reason, seer decides whether to reveal. | **FROZEN** |
| **Voting** | Each living agent votes. Most-voted eliminated, role revealed. | Frozen |
| **Win check** | Check win conditions. No winner → next round (max 2). | Settle round markets |
| **End** | Reveal all roles. Pay out the prize and bets. | Settle game markets |

## Game theory essentials (for prompt design)

- **Wolves** play a *signaling game*: emit speech/votes indistinguishable from a villager. Build credibility early, misdirect later, sow discord between villagers, defend partner only subtly, and sacrifice a doomed partner to keep their own cover.
- **Villagers** play a *screening game*: apply pressure, catch contradictions, track who benefits from each death, watch voting patterns. Avoid tunnel vision.
- **Seer** plays a *timing game*: reveal (decisive but paints a target) vs hide (survive, gather more). Usually hide round 1, reveal round 2 when it swings the vote.

These map directly to the prompts in `04-BACKEND.md`. The agent's prompt defines its strategy.

## Two product flows (MVP = Flow 2)

- **Flow 1 — Human plays:** 1 human + 6 agents, human is a wolf. "Can you out-bluff the machines?" Build later.
- **Flow 2 — Gambling arena (MVP):** 7 agents, humans bet only. Autonomous, on-theme, doesn't depend on a human performing live. **This is what we build first.**

## The three audiences (information model)

- **Agents** — asymmetric info, play their role, unaware of betting.
- **Bettors** (bettor mode) — see only public info, bet under uncertainty.
- **Spectators** (god mode) — see everything including roles + private reasoning, watch for dramatic irony.

Fog of war is enforced server-side. See `02-INTERFACES.md`.
