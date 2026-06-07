# 02 — Interfaces (THE GLUE)

> These are the contracts between frontend, backend, and chain. Build everything against these shapes. Keep them stable.

## 1. GameState JSON — `GET /state?mode=bettor|god`

```jsonc
{
  "gameId": 1,
  "phase": "discussion",        // setup|night|morning|discussion|voting|resolution|ended
  "round": 1,
  "maxRounds": 2,
  "pot": "1.0",                 // MON as string
  "speakingIdx": 2,             // index of agent currently speaking, or null

  "players": [
    {
      "idx": 0,
      "name": "Luna",
      "avatarSeed": "Luna",     // for DiceBear avatar generation
      "alive": true,
      "role": "villager",       // mode=god only; null in bettor mode unless revealedRole set
      "revealedRole": null,     // set publicly on elimination / game end
      "currentSpeech": null     // the line to show in their speech bubble, or null
    }
    // ... 7 players
  ],

  "nightResult": { "victimName": "Mira", "victimIdx": 2 },  // public after morning

  "discussionLog": [
    { "round": 1, "speaker": "Luna", "text": "Caspian is dodging.", "ts": 1717800000 }
  ],

  "privateReasoning": [          // mode=god only — the dramatic-irony panel
    { "speaker": "Caspian", "role": "wolf", "thought": "Pin it on Mira before she reads me." }
  ],

  "votes": [                     // public after voting
    { "voter": "Luna", "target": "Caspian" }
  ],

  "bettingOpen": true,           // false during discussion + voting
  "markets": [ /* see section 2 */ ],

  "winner": null                 // "wolves" | "village" when phase === "ended"
}
```

### Mode rules (server-side, mandatory)
- `mode=bettor`: for every player where `revealedRole` is null, set `role = null`. Omit `privateReasoning`. This is fog of war.
- `mode=god`: return everything.

## 2. Market object

Parimutuel pools — odds emerge from pool sizes, no bookmaker.

```jsonc
{
  "marketId": 0,
  "type": "game_winner",        // game_winner | who_voted_out | catches_wolf
  "round": 1,
  "options": ["wolves", "village"],
  "pools": { "wolves": "0.6", "village": "0.4" },  // total MON per option
  "frozen": false,
  "resolved": false,
  "winningOption": null
}
```

Implied odds for an option = `totalPool / optionPool`. Frontend computes and displays; updates as bets arrive.

Market types for MVP:
| Type | Options | Opens | Resolves |
|------|---------|-------|----------|
| `game_winner` | wolves / village | setup | game end |
| `who_voted_out` | living player names | morning | after vote |

(Add `catches_wolf` yes/no later if time.)

## 3. Backend HTTP API

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/state?mode=bettor\|god` | Current game state. Poll every 500ms. |
| POST | `/control/start` | Start a new game (demo button). |
| GET | `/health` | `{ "ok": true }` |

CORS: allow all origins (it's a local demo).

## 4. Contract ABI surface (`WerewolfArena.sol`)

```
openMarket(uint256 gameId, uint8 numOptions) returns (uint256 marketId)
placeBet(uint256 marketId, uint8 optionIdx) payable
freezeMarket(uint256 marketId)
resolveMarket(uint256 marketId, uint8 winningOptionIdx)
claimWinnings(uint256 marketId)
getPools(uint256 marketId) view returns (uint256[] pools)

event MarketOpened(uint256 marketId, uint256 gameId)
event BetPlaced(uint256 marketId, address bettor, uint8 optionIdx, uint256 amount)
event MarketResolved(uint256 marketId, uint8 winningOption)
```

- Backend calls: `openMarket`, `freezeMarket`, `resolveMarket`, and reads `getPools`.
- Frontend calls (via MetaMask): `placeBet`, `claimWinnings`.

## 5. Phase → betting window

| Phase | bettingOpen | Action |
|-------|-------------|--------|
| setup | true | open `game_winner` market |
| night | true | — |
| morning | true | open `who_voted_out` market |
| discussion | **false** | `freezeMarket` all open markets |
| voting | false | — |
| resolution | settle | `resolveMarket(who_voted_out)` |
| ended | settle | `resolveMarket(game_winner)` |
