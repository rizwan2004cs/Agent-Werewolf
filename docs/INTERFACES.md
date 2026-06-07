# INTERFACES — The Glue

> The shared contracts between Contract ↔ Orchestrator ↔ Frontend. **Agree on these in the Hour-1 sync and freeze them.** If these drift, integration at Hour 4 dies. Change them only by shouting to the whole team.

---

## 1. Game State JSON (Orchestrator → Frontend)

The orchestrator serves this. The `mode` query param controls how much is revealed.

```jsonc
{
  "gameId": 1,
  "phase": "discussion",        // setup | night | morning | discussion | voting | resolution | ended
  "round": 1,
  "maxRounds": 2,
  "pot": "1.5",                 // MON, string to avoid float issues

  "players": [
    {
      "idx": 0,
      "name": "Luna",
      "address": "0x1234...",
      "alive": true,
      "role": "villager",       // ONLY present in mode=god. null in mode=bettor unless revealed.
      "revealedRole": null,     // set publicly when eliminated or at game end
      "lastSpeech": "I think Caspian is dodging questions."
    }
  ],

  "nightResult": { "victim": "Mira" },     // public after morning phase

  "discussionLog": [
    { "round": 1, "turn": 0, "speaker": "Luna", "text": "...", "ts": 1717800000 }
  ],

  "privateReasoning": [                     // ONLY in mode=god — the dramatic-irony view
    { "round": 1, "speaker": "Caspian", "thought": "I need to pin this on Mira before she reads me." }
  ],

  "votes": [                                // public after voting phase
    { "voter": "Luna", "target": "Caspian" }
  ],

  "bettingOpen": true,                      // false during discussion + voting
  "markets": [ /* see section 2 */ ],

  "winner": null                            // "wolves" | "village" when phase === "ended"
}
```

### Mode rules
- `GET /state?mode=bettor` → strip `role` (unless `revealedRole` set) and omit `privateReasoning` entirely. This is fog-of-war.
- `GET /state?mode=god` → everything, including hidden roles and private reasoning. This is the spectator/demo view.

> The fog-of-war is enforced **server-side** in the orchestrator, not the frontend. Never send hidden roles to a bettor-mode client.

---

## 2. Betting Market object

Parimutuel (pool-based) — no bookmaker. Odds emerge from pool sizes.

```jsonc
{
  "marketId": 10,
  "gameId": 1,
  "type": "who_voted_out",      // who_voted_out | catches_wolf_this_round | game_winner | seer_survives
  "round": 1,
  "options": ["Luna", "Caspian", "Theron", "Dax"],
  "pools": {                    // total MON staked per option — this IS the live odds
    "Luna": "0.2",
    "Caspian": "0.8",
    "Theron": "0.1",
    "Dax": "0.0"
  },
  "frozen": false,              // true during discussion/voting — no new bets
  "resolved": false,
  "winningOption": null
}
```

**Implied odds for an option** = `totalPool / optionPool`. Frontend computes and displays this; it shifts as bets arrive.

**Market types:**
| Type | Bet on | Opens | Resolves |
|------|--------|-------|----------|
| `game_winner` | wolves vs village | after setup | game end |
| `who_voted_out` | which player the vote eliminates | after morning reveal | after vote |
| `catches_wolf_this_round` | yes/no the village votes out a wolf | after morning reveal | after vote |
| `seer_survives` | yes/no | after setup | game end |

---

## 3. Contract surface (what B calls on A's contracts)

### AgentWerewolf.sol
```
createGame(address[] players, bytes32[] roleHashes) payable returns (uint256 gameId)
commitNightKill(uint256 gameId, bytes32 killHash)
revealNightKill(uint256 gameId, uint8 victimIdx, bytes32 salt)
submitVote(uint256 gameId, uint8 targetIdx)        // called per agent wallet
resolveVote(uint256 gameId)
claimPrize(uint256 gameId)
forceEnd(uint256 gameId)

// events B listens for:
event PlayerEliminated(uint256 gameId, uint8 playerIdx, bool wasWolf)
event Winner(uint256 gameId, uint8 team)            // 1=wolf, 2=village
```

### WerewolfBetting.sol
```
openMarket(uint256 gameId, uint8 marketType, string[] options) returns (uint256 marketId)
placeBet(uint256 marketId, uint8 optionIdx) payable  // called by bettor wallets
freezeMarket(uint256 marketId)                       // orchestrator calls at discussion start
resolveMarket(uint256 marketId, uint8 winningOptionIdx)  // orchestrator calls after outcome
claimWinnings(uint256 marketId)                      // bettor claims

// views frontend reads directly:
getPools(uint256 marketId) returns (uint256[] pools)
event BetPlaced(uint256 marketId, address bettor, uint8 optionIdx, uint256 amount)
```

---

## 4. Orchestrator HTTP API (Frontend → Orchestrator)

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/state?mode=bettor\|god` | current game state (poll every 500ms) |
| GET | `/markets?gameId=1` | active betting markets + pools |
| POST | `/control/start` | start a new game (demo control button) |
| POST | `/control/next` | advance phase manually (demo safety — optional) |

> Frontend polls `/state` every 500ms. Simplest reliable option for 6 hours. SSE is a nice-to-have, not a requirement.

---

## 5. Phase → betting window mapping

| Phase | Betting open? | Markets active |
|-------|---------------|----------------|
| setup | ✅ open | game_winner, seer_survives |
| night | ✅ open | game_winner, who_voted_out (after morning) |
| morning | ✅ open | who_voted_out, catches_wolf_this_round open here |
| **discussion** | ❌ **FROZEN** | watch only — this is the locked sweat |
| voting | ❌ frozen | resolving |
| resolution | settle | who_voted_out + catches_wolf resolve |
| ended | settle | game_winner + seer_survives resolve |

Orchestrator calls `freezeMarket()` when entering discussion, `resolveMarket()` after the relevant outcome.
