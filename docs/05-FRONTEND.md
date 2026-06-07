# 05 — Frontend (The Game UI)

> React + Vite. This is the differentiator — it must feel like a polished game, not a dashboard. Characters in a village, speech clouds above them when they talk, a darkening sky at night, and betting that surfaces naturally.

## The visual concept

A **village circle**: 7 character avatars arranged in a ring around a central glowing prize pot (like villagers gathered around a campfire). When an agent speaks, a **cloud-shaped speech bubble** pops above their head with their line. The sky/background shifts **dark at night, warm at day**. Eliminated characters slump, grey out, and get a tombstone marker. A **betting bar** sits at the bottom (or as a side panel) and lights up with a call-to-action when a market is open, then locks during discussion.

Aesthetic: clean, rounded, friendly game art. Soft shadows, rounded avatars, a cozy-but-tense village vibe. Think a board-game digital adaptation.

## Dependencies
```
react, react-dom (via Vite template)
ethers (v6)        # wallet + placeBet/claim only
```
Avatars: use **DiceBear** (free, no assets needed):
`https://api.dicebear.com/9.x/adventurer/svg?seed={name}` — distinct character per name.

`frontend/.env`:
```
VITE_BACKEND_URL=http://localhost:8000
VITE_CONTRACT_ADDRESS=0x...
VITE_EXPLORER_URL=https://testnet.monadvision.com
VITE_CHAIN_ID=10143
VITE_RPC_URL=https://testnet-rpc.monad.xyz
```

## Component tree

```
App
├── TopBar           (PACK logo, phase + round badge, pot, mode toggle)
├── VillageScene
│   ├── PrizePot         (center)
│   └── Character × 7    (ring layout)
│       └── SpeechBubble (cloud, shows when this char is speaking)
├── BettingPanel     (bottom bar; bettor mode)
├── ReasoningPanel   (side; god mode only — dramatic irony)
└── GameOverOverlay  (role reveal + payout)
```

## Layout: the ring

Position 7 characters evenly on a circle. Compute with trig:

```jsx
function ringPosition(idx, total, radius = 230) {
  const angle = (idx / total) * 2 * Math.PI - Math.PI / 2; // start at top
  return { left: `calc(50% + ${Math.cos(angle) * radius}px)`,
           top:  `calc(50% + ${Math.sin(angle) * radius}px)` };
}
```

`VillageScene` is `position: relative`, full-width, ~600px tall. Each `Character` is `position: absolute` using `ringPosition`, transform `translate(-50%, -50%)` to center on the point. The `PrizePot` sits dead center.

## App.jsx (skeleton)

```jsx
import { useEffect, useState } from "react";
import { fetchState, startGame } from "./api";
import VillageScene from "./scene/VillageScene";
import BettingPanel from "./betting/BettingPanel";
import ReasoningPanel from "./scene/ReasoningPanel";
import TopBar from "./scene/TopBar";
import GameOverOverlay from "./scene/GameOverOverlay";

export default function App() {
  const [mode, setMode] = useState("god");     // "god" | "bettor"
  const [state, setState] = useState(null);

  useEffect(() => {
    const id = setInterval(async () => {
      try { setState(await fetchState(mode)); } catch {}
    }, 500);
    return () => clearInterval(id);
  }, [mode]);

  const phase = state?.phase ?? "idle";
  const isNight = phase === "night" || phase === "setup";

  return (
    <div className={`app ${isNight ? "night" : "day"}`}>
      <TopBar state={state} mode={mode} onToggleMode={() =>
        setMode(m => m === "god" ? "bettor" : "god")}
        onStart={startGame} />
      <VillageScene state={state} />
      {mode === "bettor" && <BettingPanel state={state} />}
      {mode === "god" && <ReasoningPanel reasoning={state?.privateReasoning} />}
      {phase === "ended" && <GameOverOverlay state={state} />}
    </div>
  );
}
```

## api.js

```js
const BASE = import.meta.env.VITE_BACKEND_URL;
export async function fetchState(mode) {
  const r = await fetch(`${BASE}/state?mode=${mode}`);
  return r.json();
}
export async function startGame() {
  return fetch(`${BASE}/control/start`, { method: "POST" });
}
```

## Character.jsx

```jsx
import SpeechBubble from "./SpeechBubble";

export default function Character({ player, isSpeaking, godMode, style }) {
  const avatar = `https://api.dicebear.com/9.x/adventurer/svg?seed=${player.avatarSeed}`;
  const dead = !player.alive;
  return (
    <div className={`character ${dead ? "dead" : ""} ${isSpeaking ? "speaking" : ""}`} style={style}>
      {isSpeaking && player.currentSpeech &&
        <SpeechBubble text={player.currentSpeech} />}
      <div className="avatar-wrap">
        <img className="avatar" src={avatar} alt={player.name} />
        {dead && <span className="tombstone">🪦</span>}
      </div>
      <div className="nameplate">{player.name}</div>
      {(godMode && player.role) && <div className={`role-tag ${player.role}`}>{player.role}</div>}
      {player.revealedRole && <div className={`role-tag revealed ${player.revealedRole}`}>{player.revealedRole}</div>}
    </div>
  );
}
```

## SpeechBubble.jsx (the cloud)

```jsx
export default function SpeechBubble({ text }) {
  return (
    <div className="speech-bubble">
      {text}
      <div className="speech-tail" />
    </div>
  );
}
```

CSS for the cloud + tail (in `styles.css`):
```css
.speech-bubble {
  position: absolute; bottom: 110%; left: 50%; transform: translateX(-50%);
  background: #fff; color: #1a1a2e; padding: 10px 14px; border-radius: 16px;
  width: max-content; max-width: 220px; font-size: 14px; line-height: 1.4;
  box-shadow: 0 6px 20px rgba(0,0,0,.25);
  animation: pop .25s ease forwards;
}
.speech-tail {
  position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%);
  width: 0; height: 0; border-left: 8px solid transparent;
  border-right: 8px solid transparent; border-top: 10px solid #fff;
}
@keyframes pop { from { opacity: 0; transform: translateX(-50%) scale(.8); }
                 to { opacity: 1; transform: translateX(-50%) scale(1); } }
```

## VillageScene.jsx

```jsx
import Character from "./Character";
import PrizePot from "./PrizePot";

export default function VillageScene({ state }) {
  if (!state || state.phase === "idle")
    return <div className="scene empty">Press Start to begin a game</div>;
  const total = state.players.length;
  return (
    <div className="scene">
      <PrizePot pot={state.pot} phase={state.phase} round={state.round} />
      {state.players.map((p) => (
        <Character key={p.idx} player={p}
          isSpeaking={state.speakingIdx === p.idx}
          godMode={!!state.privateReasoning}
          style={ringStyle(p.idx, total)} />
      ))}
    </div>
  );
}
function ringStyle(idx, total, radius = 230) {
  const a = (idx / total) * 2 * Math.PI - Math.PI / 2;
  return { left: `calc(50% + ${Math.cos(a) * radius}px)`,
           top: `calc(50% + ${Math.sin(a) * radius}px)`,
           transform: "translate(-50%, -50%)" };
}
```

## Day / night atmosphere

```css
.app { min-height: 100vh; transition: background 1s; }
.app.day   { background: radial-gradient(circle at 50% 30%, #fef3c7, #fcd9a8); }
.app.night { background: radial-gradient(circle at 50% 20%, #1e2b50, #0a0f1f); }
.app.night .nameplate { color: #cbd5e1; }
.scene { position: relative; width: 100%; height: 600px; margin: 0 auto; }
.character { position: absolute; width: 96px; text-align: center; transition: all .4s; }
.character.dead { opacity: .4; filter: grayscale(1); }
.character.speaking .avatar-wrap { box-shadow: 0 0 0 4px #fbbf24, 0 0 24px #fbbf24; }
.avatar-wrap { position: relative; width: 72px; height: 72px; margin: 0 auto;
  border-radius: 50%; overflow: visible; }
.avatar { width: 72px; height: 72px; border-radius: 50%; background: #fff; }
.tombstone { position: absolute; bottom: -4px; right: -4px; font-size: 22px; }
.nameplate { margin-top: 6px; font-weight: 600; font-size: 13px; }
.role-tag { font-size: 11px; padding: 1px 8px; border-radius: 8px; margin-top: 2px; display: inline-block; }
.role-tag.wolf { background: #fee2e2; color: #b91c1c; }
.role-tag.seer { background: #ede9fe; color: #6d28d9; }
.role-tag.villager { background: #dcfce7; color: #15803d; }
```

## BettingPanel.jsx (bottom bar, bettor mode)

```jsx
import { placeBet } from "../wallet";

function odds(pools, opt) {
  const total = Object.values(pools).reduce((a, b) => a + parseFloat(b || 0), 0);
  const o = parseFloat(pools[opt] || 0);
  return o > 0 ? (total / o).toFixed(2) + "×" : "—";
}

export default function BettingPanel({ state }) {
  if (!state || !state.markets?.length) return null;
  const frozen = !state.bettingOpen;
  const active = state.markets.filter(m => !m.resolved);
  return (
    <div className="betting-bar">
      {frozen
        ? <div className="bet-locked">🔒 Betting closed — watch the discussion unfold</div>
        : <div className="bet-cta">💰 Place your bet!</div>}
      {active.map(m => (
        <div key={m.marketId} className="market">
          <div className="market-title">{m.type === "game_winner" ? "Who wins?" : "Who gets voted out?"}</div>
          <div className="options">
            {m.options.map((opt, i) => (
              <button key={opt} className="bet-btn" disabled={frozen}
                onClick={() => placeBet(m.marketId, i)}>
                <span>{opt}</span>
                <span className="odds">{odds(m.pools, opt)}</span>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

```css
.betting-bar { position: sticky; bottom: 0; background: rgba(15,15,30,.92);
  padding: 14px 18px; display: flex; gap: 18px; align-items: center; flex-wrap: wrap; }
.bet-cta { color: #fbbf24; font-weight: 700; animation: pulse 1.2s infinite; }
.bet-locked { color: #94a3b8; }
.bet-btn { display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 8px 14px; border-radius: 10px; border: 1px solid #475569;
  background: #1e293b; color: #e2e8f0; cursor: pointer; }
.bet-btn:disabled { opacity: .4; cursor: not-allowed; }
.bet-btn .odds { color: #fbbf24; font-size: 12px; }
@keyframes pulse { 50% { opacity: .5; } }
```

## wallet.js (ethers + MetaMask, the only chain writes)

```js
import { BrowserProvider, Contract, parseEther } from "ethers";
import abi from "./abi.json";

const ADDR = import.meta.env.VITE_CONTRACT_ADDRESS;

async function getContract() {
  if (!window.ethereum) throw new Error("Install MetaMask");
  const provider = new BrowserProvider(window.ethereum);
  await provider.send("eth_requestAccounts", []);
  // ensure Monad testnet
  await window.ethereum.request({
    method: "wallet_switchEthereumChain",
    params: [{ chainId: "0x" + Number(import.meta.env.VITE_CHAIN_ID).toString(16) }],
  }).catch(() => {});
  const signer = await provider.getSigner();
  return new Contract(ADDR, abi, signer);
}

export async function placeBet(marketId, optionIdx, amountMon = "0.05") {
  const c = await getContract();
  const tx = await c.placeBet(marketId, optionIdx, { value: parseEther(amountMon) });
  await tx.wait();
}

export async function claimWinnings(marketId) {
  const c = await getContract();
  const tx = await c.claimWinnings(marketId);
  await tx.wait();
}
```

## Pacing beats (do not skip — this is what makes it a game)

Drive these off `phase` transitions in `App`:
- **Night** → `.app` gets `.night`, sky darkens over 1s. Optional "🌙 The village sleeps…" toast.
- **Morning** → hold 1s, then the victim character flips to `.dead` (it grays + tombstone via CSS transition).
- **Discussion** → the speaking character glows; speech bubble pops; the backend already paces turns ~1.5s apart, so the bubble naturally appears one at a time.
- **Voting** → optional: show vote arrows/tally; the eliminated character flips with role revealed.
- **Ended** → `GameOverOverlay`: all role tags revealed at once, winner banner, prize pot "claim" if connected.

## God-mode ReasoningPanel (dramatic irony)

```jsx
export default function ReasoningPanel({ reasoning }) {
  if (!reasoning?.length) return null;
  return (
    <aside className="reasoning-panel">
      <h3>🧠 What they're really thinking</h3>
      {reasoning.slice(-8).map((r, i) => (
        <div key={i}><b className="wolf">{r.speaker}</b>: <i>{r.thought}</i></div>
      ))}
    </aside>
  );
}
```

## Acceptance criteria
- [ ] 7 characters render in a ring around the pot, each with a DiceBear avatar + nameplate
- [ ] Sky transitions dark↔light on night↔day phases
- [ ] When `speakingIdx` matches a character, their speech cloud pops with `currentSpeech`
- [ ] Dead characters grey out with a tombstone
- [ ] Betting bar shows live odds, a pulsing CTA when open, a lock state during discussion
- [ ] MetaMask `placeBet` works on Monad testnet
- [ ] God mode shows role tags + reasoning panel; bettor mode hides them
- [ ] Game-over overlay reveals all roles + winner

## If short on time
Priority order: ring of characters + speech bubbles + day/night → dead/tombstone states → betting bar with odds → MetaMask bets → god-mode reasoning. Get the *watching* beautiful before the *betting* is wired.
