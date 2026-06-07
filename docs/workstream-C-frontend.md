# Workstream C — Frontend

> You own what the room sees. This is a peer-judged event — judges vote for what they *felt*. Your job is to make agents arguing feel like a live broadcast, and betting feel like a market. **Pacing beats polish.**

## Your files
- `frontend/src/App.jsx` — mode switch + poll loop
- `frontend/src/api.js` — talks to orchestrator
- `frontend/src/modes/GodMode.jsx` — sees everything (spectator/demo)
- `frontend/src/modes/BettorMode.jsx` — fog of war + betting
- `frontend/src/components/PlayerCard.jsx`
- `frontend/src/components/DiscussionFeed.jsx`
- `frontend/src/components/BettingPanel.jsx`

## The two modes (this is the core UX)

| Mode | Sees | Feels | For |
|------|------|-------|-----|
| **God mode** | All roles, private reasoning, who the wolves are | Dramatic irony — watching the village get fooled | Audience / demo / projector |
| **Bettor mode** | Only public info (speeches, deaths, votes) | Risk + deduction under uncertainty | Players betting real MON |

A toggle at the top switches modes. For the live demo, run **god mode on the projector** (it's the most fun to watch) and have **bettor mode** open on a phone to show the betting flow.

## Build order

### Step 1 (Hour 1) — Static board
5 player cards in a row. Each card: name, avatar/emoji, alive/dead state, a speech bubble area. Hardcode fake data first.

```jsx
// components/PlayerCard.jsx
export function PlayerCard({ player, godMode }) {
  return (
    <div className={`card ${player.alive ? "" : "dead"}`}>
      <div className="avatar">{player.alive ? "🧑" : "💀"}</div>
      <div className="name">{player.name}</div>
      {godMode && player.role && <div className={`role role-${player.role}`}>{player.role}</div>}
      {player.revealedRole && <div className="revealed">{player.revealedRole}</div>}
      {player.lastSpeech && <div className="bubble">{player.lastSpeech}</div>}
    </div>
  );
}
```

### Step 2 (Hour 2) — Poll + live feed
```jsx
// api.js
const BASE = import.meta.env.VITE_ORCHESTRATOR_URL;
export async function fetchState(mode) {
  const r = await fetch(`${BASE}/state?mode=${mode}`);
  return r.json();
}
export async function startGame() {
  return fetch(`${BASE}/control/start`, { method: "POST" });
}
```

```jsx
// App.jsx
import { useEffect, useState } from "react";
import { fetchState } from "./api";

export default function App() {
  const [mode, setMode] = useState("god");
  const [state, setState] = useState(null);

  useEffect(() => {
    const id = setInterval(async () => setState(await fetchState(mode)), 500);
    return () => clearInterval(id);
  }, [mode]);

  if (!state) return <div>Loading…</div>;
  return (
    <div>
      <header>
        <h1>PACK</h1>
        <button onClick={() => setMode(m => m === "god" ? "bettor" : "god")}>
          {mode === "god" ? "👁 God mode" : "🎲 Bettor mode"}
        </button>
        <PhaseBadge phase={state.phase} round={state.round} />
        <Pot pot={state.pot} />
      </header>
      <Board players={state.players} godMode={mode === "god"} />
      <DiscussionFeed log={state.discussionLog} />
      {mode === "bettor" && <BettingPanel state={state} />}
      {mode === "god" && <PrivateReasoning reasoning={state.privateReasoning} />}
    </div>
  );
}
```

### Step 3 (Hour 3) — Pacing & animation (THE differentiator)
Do not skip these. They turn a script into a show. All are `setTimeout` / CSS transitions:

| Moment | Beat |
|--------|------|
| Night falls | dim the whole board, show "the village sleeps…" 2s |
| Morning reveal | hold 1s, then flip the victim card to 💀 with a transition |
| Each speech | stream in (typewriter or fade), 1s gap between agents |
| Vote tally | fill bars live as votes arrive |
| Elimination | show full tally 1s, THEN flip the role card |
| Game over | flip all hidden cards at once, then show prize TX |

```css
.card { transition: opacity .4s, transform .4s; }
.card.dead { opacity: .35; transform: scale(.96); filter: grayscale(1); }
.board.night { filter: brightness(.3); transition: filter 1s; }
.role-card-flip { animation: flip .5s ease forwards; }
@keyframes flip { from { transform: rotateY(90deg); } to { transform: rotateY(0); } }
```

### Step 4 (Hour 3-4) — Betting panel (bettor mode)
Reads markets, shows live odds from pools, lets a connected wallet bet. Freeze the UI during discussion.

```jsx
// components/BettingPanel.jsx
function impliedOdds(pools, option) {
  const total = Object.values(pools).reduce((a, b) => a + parseFloat(b), 0);
  const opt = parseFloat(pools[option] || 0);
  return opt > 0 ? (total / opt).toFixed(2) + "x" : "—";
}

export function BettingPanel({ state }) {
  const frozen = !state.bettingOpen;   // true during discussion → "watching"
  return (
    <div className="betting">
      {frozen && <div className="frozen-banner">🔒 Betting closed — discussion in progress</div>}
      {state.markets.map(m => (
        <div key={m.marketId} className="market">
          <h3>{prettyType(m.type)}</h3>
          {m.options.map(opt => (
            <button disabled={frozen} onClick={() => placeBet(m.marketId, opt)}>
              {opt} <span className="odds">{impliedOdds(m.pools, opt)}</span>
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}
```

Wallet connection: use `window.ethereum` (MetaMask on Monad testnet). For the demo, connecting is optional — you can show the odds shifting and the freeze behaviour even without live bets, and demo one real bet from a pre-funded wallet.

### Step 5 (Hour 4-5) — God-mode dramatic irony
This is the spectator magic. In god mode, each player card shows their *true role* permanently, and a side panel streams their *private reasoning* as it happens — so the audience reads "Caspian (WOLF) thinking: pin it on Mira" right before Caspian says something innocent out loud.

```jsx
function PrivateReasoning({ reasoning }) {
  return (
    <aside className="reasoning">
      <h3>🧠 What they're really thinking</h3>
      {reasoning.map((r, i) => (
        <div key={i} className="thought">
          <b>{r.speaker}</b>: <i>{r.thought}</i>
        </div>
      ))}
    </aside>
  );
}
```

## Acceptance criteria
- [ ] Mode toggle works; bettor mode never shows hidden roles (trust the server payload)
- [ ] Board renders 5 cards, alive/dead states, speeches
- [ ] Discussion feed streams with pacing beats (not instant dumps)
- [ ] Night/morning/elimination have visible transitions
- [ ] Betting panel shows live odds from pools, freezes during discussion
- [ ] God mode shows true roles + private reasoning
- [ ] Game-over flips all cards + shows prize TX link to `VITE_EXPLORER_URL`

## If you fall behind
A clean terminal-style feed with colored agent names and good pacing beats a half-built fancy UI. Priority order: live feed with pacing → role reveal moment → betting panel → god-mode reasoning panel. Get the *watching* right before the *betting*.
